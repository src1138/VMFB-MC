#!/usr/bin/python

from datetime import datetime	# to handle dates
import time			# to handle timers
import threading		# to handle timer and interupt threads
# import urllib2		# to handle http requests to enable/disable motion detection
import os 			# needed to execute system commands to start/stop motioneye server
import RPi.GPIO as GPIO		# for GPIO access

# Configuration variables
SENSOR_IR_TIMEOUT=30		# seconds the sensors stay on after last PIR trigger
MOTOR_TIMEOUT=10			# soconds dispenser motor stays on before it times out
TIMED_DISPENSE_PERIOD=3600	# seconds between timed dispense when it is enabled
TIMED_DISPENSE_START_TIME=500	# time of day timed dispense will start when enabled
				# (HHMM format, don't use leading zeros)
TIMED_DISPENSE_END_TIME=1600	# time of day timed dispense will stop when enabled
				# (HHMM format, don't use leading zeros)
PBKA_ON_PERIOD=1			# seconds the PBKA will sink current to keep a powerbank on
PBKA_OFF_PERIOD=10		# seconds between PBKA current sinks
DEFAULT_TOGGLE_TIMED_DISPENSE=1   		# set to 1 to enable timer on startup
DEFAULT_TOGGLE_PBKA=0      	# set to 1 to enable PBKA on startup

# Initialize RPi GPIO
# GPIO.setmode(GPIO.BOARD)	# uses board pin numbers to reference pins
GPIO.setmode(GPIO.BCM)		# uses gpio numbers to reference pins

# Disable warnings
GPIO.setwarnings(False)		# disables GPIO warnings (ex. pin already in use)

# Set GPIO pin numbers
PIR=27 		#PIN 13 - input to sense PIR signal
MT=17 		#PIN 11	- input to sense hopper empty signal
MAN=26 		#PIN 37 - input to sense manual dispense event
PBKA=19 	#PIN 35 - input to sense if PBKA is enabled
TMR=6 		#PIN 31 - input to sense if timer is enabled
CAL=22      	#PIN 15 - input to sense if calibration mode is enabled
DIS=15 		#PIN 10 - input to sense a deposit event
DEP=14 		#PIN 8 - input to sense a dispense event
SIR=18 		#PIN 12 - output to turn on IR sensor LEDs
MTR=4 		#PIN 7 - output to turn on dispense motor
MT_SIG=24	#PIN 18 - output to indicate if hopper is (almost) empty
TMR_SIG=12  	#PIN 32 - output to indicate if timed dispense is enabled
PBKA_SIG=16 	#PIN 36 - output to indicate if PBKA is enabled
CAL_SIG=23      #PIN 16 - output to indicate if calibration mode is enabled

# Configure GPIO inputs with pull-downs
GPIO.setup([PIR,MT,MAN,PBKA,TMR,CAL], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# For op-amps pull down, for comparators pull up.
GPIO.setup([DEP,DIS], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# Configure GPIO outputs and set them to low initially
GPIO.setup([SIR,MTR,MT_SIG], GPIO.OUT, initial=GPIO.LOW)

# Logs events as <timestamp>\t<eventType>\t<event>, casts areguments as strings
def log_event(eventType=None,event=None,pin=None):
    '''logs interrupt and timer events'''
    #print("Start log_event()")
    timestamp = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
        file.write(timestamp + "	" + str(eventType) + "	" + str(event) + "	" + str(pin) + "\n")
    #print("End log_event()")

# When PIR signal goes high, enables sensors
def PIR_event(pin=None):
    '''Turns the sensor IR LEDs on'''
    #print("Start PIR_event()")
    log_event("PIR",1,pin)
    sensor_IR_on(pin)
    #print("End PIR_event()")

# When sensors are on, checks the empty sensor and updates the MT_SIG pin state
# Takes this approach because when the sensor LEDs are off the signal is always low
def update_MT(pin=None):
    '''Updates the alue of the empty indicator output pin'''
    #print("Start update_MT()")
    event=0
    if GPIO.input(MT) == 1:
        GPIO.output(MT_SIG,1)
        event=1
    else:
        GPIO.output(MT_SIG,0)
    log_event("MT",event,pin)
    #print("End update_MT()")

# Suspends PBKA if it is enabled, turns on sensor LEDs,
# updates empty sensor status, and (re)starts sensor timeout timer
def sensor_IR_on(pin=None):
    '''Turns the IR LEDs for the sensors on'''
    #print("Start sensor_IR_on()")
    log_event("SIR","ON",pin)
    if GPIO.input(PBKA) == 1:
        suspend_PBKA(pin)
    GPIO.output(SIR,1)
    global sensor_timer
    if sensor_timer.is_alive() is True:
        sensor_timer.cancel()
    sensor_timer = threading.Timer(SENSOR_IR_TIMEOUT, sensor_IR_off)
    sensor_timer.start()
    # Add event detect for DEP and DIS, especially when using a comparator you need a bouncetime
    # around 1000ms
    # Removing events first since adding them when already added (manual dispense when sensors
    # are already on) raises an exception and halts execution of the thread
    GPIO.remove_event_detect(DEP)
    GPIO.remove_event_detect(DIS)
    # Interrupt for Deposit and Dispense when signal goes low>high.
    # It triggers as soon as an object is seen, and will not
    # trigger again until the pin goes low, then high again
    # adding a 1000ms debounce because LM393 comparators are jittery
    # for LM358 op-amps, a 100ms debounce should be sufficient
    GPIO.add_event_detect(DEP, GPIO.RISING, deposit_event, 100)
    GPIO.add_event_detect(DIS, GPIO.RISING, dispense_event, 100)
    update_MT(pin)
    # if the trigger came from the PIR, enable camera, enable motion detection in motioneye
    # and log the event
    if pin == PIR:
        # enable the camera
        # enable_camera(pin)
        # enable motion detection
        # urllib2.urlopen("http://localhost:7999/1/detection/start").read()
        os.system('curl http://localhost:7999/1/detection/start')
        log_event("MOD","START",pin)
    #print("End sensor_IR_on()")

# Updates empty sensor status, turns off sensor LEDs, stops sensor timeout timer,
# re-enables PBKA if it is enabled
def sensor_IR_off(pin="TO"):
    '''Turns the IR LEDs for the sensors off'''
    #print("Start sensor_IR_off()")
    # Some PIR sensors stay on until they don't detect anything
    # this will check again to make sure the PIR is not triggering before disabling the sensors
    if GPIO.input(PIR) == 1:
        sensor_IR_on(PIR)
    else:
        update_MT(pin)
        log_event("SIR","OFF",pin)
        GPIO.output(SIR,0)
        if sensor_timer.is_alive() is True:
            sensor_timer.cancel()
        if GPIO.input(PBKA) == 1:
            toggle_PBKA(pin)
        # Remove event detect for DEP and DIS
        GPIO.remove_event_detect(DEP)
        GPIO.remove_event_detect(DIS)
	# Make sure the motor is off since the sensors are off
        motor_off(pin)
        # end any recording disable motion detection in motioneye and log the response
        # urllib2.urlopen("http://localhost:7999/1/detection/pause").read()
        os.system('curl http://localhost:7999/1/detection/pause')
        log_event("MOD","PAUSE",pin)
        # urllib2.urlopen("http://localhost:7999/1/action/eventend").read()
        os.system('curl http://localhost:7999/1/action/eventend')
        log_event("REC","STOP",pin)
        # disable the camera to save power while sensors are off
        # disable_camera(pin)
    #print("End sensor_IR_off()")

# When a deposit event is detected, turn on the dispense motor
def deposit_event(pin=None):
    '''Turns the dispense motor on'''
    #print("Start deposit_event()")
    if GPIO.input(DIS) == 0:
        log_event("DEP",1,pin)
        motor_on(pin)
    else:
        # If there is something triggering the dispense sensor
        # when a deposit is sensed, log it and don't turn on the motor
        log_event("DEP","DISJAM",pin)
    #print("End deposit_event()")

# When a dispense event is detected, turns off the dispense motor
def dispense_event(pin=None):
    '''Turns the dispense motor off'''
    #print("Start dispense_event()")
    log_event("DIS",1,pin)
    motor_off(pin)
    #print("End dispense_event()")

# Turns on the motor and (re)starts the motor timeout timer
def motor_on(pin=None):
    '''Turns the dispense motor on'''
    #print("Start motor_on()")
    log_event("MTR","ON",pin)
    GPIO.output(MTR,1)
    global motor_timer
    if motor_timer.is_alive() is True:
        motor_timer.cancel()
    motor_timer = threading.Timer(MOTOR_TIMEOUT, motor_off)
    motor_timer.start()
    #print("End motor_on()")

# Turns off the motor and stops the motor timeout timer
def motor_off(pin="TO"):
    '''Turns the dispense motor off''' 
    #print("Start motor_off()")
    log_event("MTR","OFF",pin)
    GPIO.output(MTR,0)
    if motor_timer.is_alive() is True:
        motor_timer.cancel()
    #print("End motor_off()")

# When a manual dispense event is detected, turns on the sensors and starts the dispense motor
def manual_dispense(pin=None):
    '''Dispenses a peanut''' 
    #print("Start manual_dispense()")
    log_event("MAN","DISPENSE",pin)
    sensor_IR_on(pin)
    motor_on(pin)
    #print("End manual_dispense()")

# if current time is equal to or after the start time and equal to
# or before the end time, turns on the sensor LEDs and starts the
# motor and (re)starts the timed dispense interval timer
def timed_dispense(pin="TO"):
    '''Dispenses a peanut and restarts the timer''' 
    #print("Start timed_dispense()")
    nowTime=int(datetime.now().strftime("%H%M"))
    # If you want to define multiple windows of timer operation
    # of operation on certain days or dates you can do so in
    # the following if statement
    if (nowTime >= TIMED_DISPENSE_START_TIME) & (nowTime <= TIMED_DISPENSE_END_TIME):
        log_event("TMR","DISPENSE",pin)
        sensor_IR_on(pin)
        motor_on(pin)
    else:
        log_event("TMR","SUSPENDED",pin)
    global timed_dispense_timer
    if timed_dispense_timer.is_alive() is True:
        timed_dispense_timer.cancel()
    timed_dispense_timer = threading.Timer(TIMED_DISPENSE_PERIOD, timed_dispense)
    timed_dispense_timer.start()
    #print("End timed_dispense()")

def suspend_timed_dispense(pin=None):
    '''Stops timed dispense until it is toggled back on''' 
    #print("Start suspend_timed_dispense()")
    if GPIO.input(TMR) == 1: # only suspend if TMR is enabled
        if timed_dispense_timer.is_alive() is True:
            timed_dispense_timer.cancel()
    log_event("TMR","SUSPEND",pin)
    #print("End suspend_timed_dispense()")

# When the TMR pin changes state, (re)starts the timed dispense
# timer if it is high, stops it when it is low
def toggle_timed_dispense(pin=None):
    '''Check the TMR gpio pin value and enable(1) or disable(0) timed dispense''' 
    #print("Start toggle_timed_dispense()")
    event="DISABLED"
    global timed_dispense_timer
    if GPIO.input(TMR) == 1:
        event="ENABLED"
        if timed_dispense_timer.is_alive() is True:
            timed_dispense_timer.cancel()
        timed_dispense_timer = threading.Timer(TIMED_DISPENSE_PERIOD, timed_dispense)
        timed_dispense_timer.start()
    else:
        if timed_dispense_timer.is_alive() is True:
            timed_dispense_timer.cancel()
    log_event("TMR",event,pin)
    #print("End toggle_timed_dispense()")

# Suspends the PBKA current sinking, stops PBKA timers
def suspend_PBKA(pin=None):
    '''Stops the PBKA until it is toggled back on''' 
    #print("Start suspend_PBKA()")
    if GPIO.input(PBKA) == 1: # only suspend if PBKA is enabled
        if PBKA_sink_timer.is_alive() is True:
            PBKA_sink_timer.cancel()
        if PBKA_idle_timer.is_alive() is True:
            PBKA_idle_timer.cancel()
    log_event("PBKA","SUSPEND",pin)
    #print("End suspend_PBKA()")

# When the PBKA pin changes state or sensors turn off when the PBKA is enabled,
# (re)starts the PBKA Off timer to start the current sink cycle
# When PBKA is disabled, it stops the PBKA timers
def toggle_PBKA(pin=None):
    '''Check the PBKA gpio pin value and enable(1) or disable(0) current sinking''' 
    #print("Start toggle_PBKA()")
    event="DISABLED"
    if GPIO.input(PBKA) == 1:
        global PBKA_idle_timer
        event="ENABLED"
        if PBKA_idle_timer.is_alive() is True:
            PBKA_idle_timer.cancel()
        PBKA_idle_timer = threading.Timer(PBKA_OFF_PERIOD, PBKA_sink)
        PBKA_idle_timer.start()
    else:
        global PBKA_sink_timer
        if PBKA_sink_timer.is_alive() is True:
            PBKA_sink_timer.cancel()
        if PBKA_idle_timer.is_alive() is True:
            PBKA_idle_timer.cancel()
    log_event("PBKA",event,pin)
    #print("End toggle_PBKA()")

# Turns on sensor LEDs to sink current and keep powerbanks on,
# (re)starts timer to keep them on for number of seconds specified
def PBKA_sink(pin="TO"):
    '''Starts timer to trigger the end of the sink'''
    #print("Start PBKA_sink()")
    log_event("PBKA","SINK",pin)
    GPIO.output(SIR,1)
    global PBKA_sink_timer
    if PBKA_sink_timer.is_alive() is True:
        PBKA_sink_timer.cancel()
    PBKA_sink_timer = threading.Timer(PBKA_ON_PERIOD, PBKA_idle)
    PBKA_sink_timer.start()
    #print("End PBKA_sink()")

# Turns off sensor LEDs, (re)starts timer to turn them back on
def PBKA_idle(pin="TO"):
    '''Starts timer to trigger the next sink'''
    #print("Start PBKA_idle()")
    log_event("PBKA","IDLE",pin)
    GPIO.output(SIR,0)
    global PBKA_idle_timer
    if PBKA_idle_timer.is_alive() is True:
        PBKA_idle_timer.cancel()
    PBKA_idle_timer = threading.Timer(PBKA_OFF_PERIOD, PBKA_sink)
    PBKA_idle_timer.start()
    #print("End PBKA_idle()")

# Disable camera to save power
def disable_camera(pin=None):
    '''Turn the camera off by updating the config and restarting the service'''
    #print("Start disable_camera()")
    new_file_content = ""
    # disable camera in motion.conf
    with open("motion.conf", "r") as reading_file:
        for line in reading_file:
            stripped_line = line.strip()
            new_line = stripped_line.replace("camera camera-1.conf", "")
            new_file_content += new_line +"\n"
    with open("motion.conf", "w") as writing_file:
        for line in new_file_content:
            writing_file.write(line)
    # restart the motioneye server
    os.system('meyectl stopserver -b -c /data/etc/motioneye.conf')
    os.system('meyectl startserver -b -c /data/etc/motioneye.conf')
    log_event("CAM","DISABLE",pin)
    #print("End disable_camera()")

def enable_camera(pin=None):
    '''Turn the camera on by updating the config and restarting the service'''
    #print("Start enable_camera()")
    new_file_content = ""
    # enable camera in motion.conf
    with open("motion.conf", "r") as reading_file:
        for line in reading_file:
            stripped_line = line.strip()
            new_line = stripped_line.replace("camera camera-1.conf", "")
            if new_line != "":
                new_file_content += new_line +"\n"
        new_file_content += "camera camera-1.conf\n"
    with open("motion.conf", "w") as writing_file:
        for line in new_file_content:
            writing_file.write(line)
    # restart the motioneye server
    os.system('meyectl stopserver -b -c /data/etc/motioneye.conf')
    os.system('meyectl startserver -b -c /data/etc/motioneye.conf')
    log_event("CAM","ENABLE",pin)
    #print("End enable_camera()")

# Enables interrupt to call sensor_IR_on() when the PIR triggers
def enable_PIR(pin=None):
    '''Add/restore the event detect to the PIR gpio pin'''
    #print("Start enablePIR()")
    log_event("PIR","ENABLE",pin)
    GPIO.remove_event_detect(PIR)	# Remove interrupt for PIR before adding to avoid exception
    GPIO.add_event_detect(PIR, GPIO.RISING, PIR_event, 100)	# Add interrupt for PIR
    #print("End enablePIR()")

# Disables interrupt to call sensor_IR_on() when the PIR triggers
def disable_PIR(pin=None):
    '''Remove the event detect from the PIR gpio pin'''
    #print("Start disablePIR()")
    GPIO.remove_event_detect(PIR)	# Remove interrupt for PIR
    log_event("PIR","DISABLE",pin)
    #print("End disablePIR()")

# When the CAL pin changes state
def toggle_calibration_mode(pin=None):
    '''Check the CAL gpio pin value and enable(1) or disable(0) calibration mode''' 
    #print("Start toggle_calibration_mode()")
    event="DISABLED"
    if GPIO.input(CAL) == 1: # Calibration mode is enabled
        event="ENABLED"
        disable_PIR(pin) # Disable the PIR interrupt
        sensor_IR_off(pin) # Make sure interrupts are removed for deposit and dispense sensors
        suspend_timed_dispense(pin) # Suspend timed dispense if it is enabled
        suspend_PBKA(pin) # Suspensd the PBKA if it is enabled
        GPIO.output(SIR,1) # Turn on the sensor LEDs
    else: # Calibration mode is disabled
        GPIO.output(SIR,0) # Turn off the sensor LEDs
        enable_PIR(pin) # Enable the PIR interrupt
        toggle_timed_dispense(pin) # Turn on timed dispense if it is enabled
        toggle_PBKA(pin) # Turn on the PBKA if it is enabled
    log_event("CAL",event,pin)
    #print("End toggle_calibration_mode()")

# Log start of script
log_event("SCRIPT","START","INIT")

# Initialize MT Sensor state - enable the sensor LEDs, check the sensor, and disable the sensor LEDs
GPIO.output(SIR,1)
update_MT("INIT")
GPIO.output(SIR,0)

# Set up GPIO interrupts - adding a bouncetime of 100ms to all interrupts
# Moved adding DEP and DIS interrupts to sensor_IR_on and remove them in sensor_IR_off
enable_PIR("INIT")
GPIO.add_event_detect(MAN, GPIO.RISING, manual_dispense, 100)	# manual dispense
GPIO.add_event_detect(TMR, GPIO.BOTH, toggle_timed_dispense, 100)	# timer toggle
GPIO.add_event_detect(PBKA, GPIO.BOTH, toggle_PBKA, 100)	# PBKA toggle
GPIO.add_event_detect(CAL, GPIO.BOTH, toggle_calibration_mode, 100)	# calibration mode toggle

# Set up timers
# Timer for sensors, calls sensor_IR_off when SENSOR_IR_TIMEOUT seconds have passed
sensor_timer = threading.Timer(SENSOR_IR_TIMEOUT, sensor_IR_off)
# Timer for motor, calls motor_off when MOTOR_TIMEOUT seconds have passed
motor_timer = threading.Timer(MOTOR_TIMEOUT, motor_off)
# Timer for timed dispense, triggers a dispense event every TIMED_DISPENSE_PERIOD seconds
timed_dispense_timer = threading.Timer(TIMED_DISPENSE_PERIOD, timed_dispense)
# Timer for PBKA curent sink, sinks current for PBKA_ON_PERIOD
PBKA_sink_timer = threading.Timer(PBKA_ON_PERIOD, PBKA_idle)
# Timer for PBKA interval between current sinks, waits PBKA_OFF_PERIOD seconds between sinks
PBKA_idle_timer = threading.Timer(PBKA_OFF_PERIOD, PBKA_sink)

# Initialize timed dispense and PBKA enable/disable - do this after defining interrupts and timers
if DEFAULT_toggle_timed_dispense == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(TMR_SIG)+'/value')
if DEFAULT_toggle_PBKA == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(PBKA_SIG)+'/value')

# Everything is interrupt- and timer-based, so script
# sleeps until an interrupt or timer calls a function
while True:
    time.sleep(1e6)
