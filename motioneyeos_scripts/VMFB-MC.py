#!/usr/bin/python

from datetime import datetime	# to handle dates
import time			# to handle timers
import threading		# to handle timer and interupt threads
import os 			# needed to execute system commands to start/stop motioneye server
import smtplib			# for sending event alert emails
import RPi.GPIO as GPIO		# for GPIO access

# Configuration variables
SENSOR_IR_TIMEOUT=30		# seconds the sensors stay on after last PIR trigger
MOTOR_TIMEOUT=10		# soconds dispenser motor stays on before it times out
TIMED_DISPENSE_PERIOD=3600	# seconds between timed dispense when it is enabled
TIMED_DISPENSE_START_TIME=600	# time of day timed dispense will start when enabled
				# (HHMM format, don't use leading zeros)
TIMED_DISPENSE_END_TIME=1800	# time of day timed dispense will stop when enabled
				# (HHMM format, don't use leading zeros)
PBKA_ON_PERIOD=1		# seconds the PBKA will sink current to keep a powerbank on
PBKA_OFF_PERIOD=10		# seconds between PBKA current sinks
DEFAULT_TOGGLE_TIMED_DISPENSE=1 # set to 1 to enable timer on startup
DEFAULT_TOGGLE_PBKA=0      	# set to 1 to enable PBKA on startup

# Email alert variables
SMTP_SERVER="<SMTP server address>"	# SMTP server URL
SMTP_PORT=587 				# port to use
SMTP_LOGIN="<email login>"		# SMTP server login
SMTP_P="<email password>"		# SMTP server pass
SMTP_SENDER="<email sender address>"	# SMTP sender address
SMTP_RECEIVER="<email receiver address>"	# SMTP receiver address

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

# Logs events as <timestamp>\t<event_type>\t<event>, casts areguments as strings
def log_event(event_type=None,event=None,pin=None):
    '''logs interrupt and timer events'''
    #print("Start log_event()")
    timestamp = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
        file.write(timestamp + "	" + str(event_type) + "	" + str(event) + "	" + str(pin) + "\n")
    #print("End log_event()")

# When PIR signal goes high, enables sensors
def pir_event(pin=None):
    '''Turns the sensor IR LEDs on'''
    #print("Start pir_event()")
    log_event("PIR",1,pin)
    # Turn on the sensors if not in calibration mode
    sensor_ir_on(pin)
    #print("End pir_event()")

# When sensors are on, checks the empty sensor and updates the MT_SIG pin state
# Takes this approach because when the sensor LEDs are off the signal is always low
def update_mt(pin=None):
    '''Updates the value of the empty indicator output pin'''
    #print("Start update_mt()")
    event=0
    if GPIO.input(MT) == 1:
        # Send email alert if state is changing
        if GPIO.input(MT_SIG) == 0:
            threading.Thread(target=send_email_alert,args=["NOT EMPTY"]).start()
        GPIO.output(MT_SIG,1)
        event=1
    else:
        # Send email alert if state is changing
        if GPIO.input(MT_SIG) == 1:
            threading.Thread(target=send_email_alert,args=["EMPTY"]).start()
        GPIO.output(MT_SIG,0)
    log_event("MT",event,pin)
    #print("End update_mt()")

# Suspends PBKA if it is enabled, turns on sensor LEDs,
# updates empty sensor status, and (re)starts sensor timeout timer
def sensor_ir_on(pin=None):
    '''Turns the IR LEDs for the sensors on'''
    #print("Start sensor_ir_on()")
    log_event("SIR","ON",pin)
    if GPIO.input(PBKA) == 1:
        suspend_pbka(pin)
    GPIO.output(SIR,1)
    global sensor_timer
    if sensor_timer.is_alive() is True:
        sensor_timer.cancel()
    sensor_timer = threading.Timer(SENSOR_IR_TIMEOUT, sensor_ir_off)
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
    update_mt(pin)
    # if the trigger came from the PIR, enable camera, enable motion detection in motioneye
    # and log the event
    if pin == PIR:
        # enable the camera
        # enable_camera(pin)
        # enable motion detection
        # urllib2.urlopen("http://localhost:7999/1/detection/start").read()
        os.system('curl http://localhost:7999/1/detection/start')
        log_event("MOD","START",pin)
    #print("End sensor_ir_on()")

# Updates empty sensor status, turns off sensor LEDs, stops sensor timeout timer,
# re-enables PBKA if it is enabled
def sensor_ir_off(pin="TO"):
    '''Turns the IR LEDs for the sensors off'''
    #print("Start sensor_ir_off()")
    # Some PIR sensors stay on until they don't detect anything
    # this will check again to make sure the PIR is not triggering before disabling the sensors
    if GPIO.input(PIR) == 1:
        sensor_ir_on(PIR)
    else:
        update_mt(pin)
        log_event("SIR","OFF",pin)
        GPIO.output(SIR,0)
        global sensor_timer
        if sensor_timer.is_alive() is True:
            sensor_timer.cancel()
        if GPIO.input(PBKA) == 1:
            toggle_pbka(pin)
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
    #print("End sensor_ir_off()")

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
    # Send email alert
    threading.Thread(target=send_email_alert,args=["DEP"]).start()
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
    if GPIO.input(CAL) == 0:
        log_event("MTR","ON",pin)
        GPIO.output(MTR,1)
        global motor_timer
        if motor_timer.is_alive() is True:
            motor_timer.cancel()
        motor_timer = threading.Timer(MOTOR_TIMEOUT, motor_off)
        motor_timer.start()
    else:
        log_event("MTR","SUSPENDED",pin)
    #print("End motor_on()")

# Turns off the motor and stops the motor timeout timer
def motor_off(pin="TO"):
    '''Turns the dispense motor off''' 
    #print("Start motor_off()")
    log_event("MTR","OFF",pin)
    GPIO.output(MTR,0)
    global motor_timer
    if motor_timer.is_alive() is True:
        motor_timer.cancel()
    if pin == "TO":
        # Send email alert
        threading.Thread(target=send_email_alert,args=["DIS TIMEOUT"]).start()
    #print("End motor_off()")

# When a manual dispense event is detected, turns on the sensors and starts the dispense motor
def manual_dispense(pin=None):
    '''Dispenses a peanut''' 
    #print("Start manual_dispense()")
    log_event("MAN","DISPENSE",pin)
    sensor_ir_on(pin)
    motor_on(pin)
    #print("End manual_dispense()")

# if current time is equal to or after the start time and equal to
# or before the end time, turns on the sensor LEDs and starts the
# motor and (re)starts the timed dispense interval timer
def timed_dispense(pin="TO"):
    '''Dispenses a peanut and restarts the timer''' 
    #print("Start timed_dispense()")
    now_time=int(datetime.now().strftime("%H%M"))
    # If you want to define multiple windows of timer operation
    # of operation on certain days or dates you can do so in
    # the following if statement
    if (now_time >= TIMED_DISPENSE_START_TIME) & (now_time <= TIMED_DISPENSE_END_TIME):
        log_event("TMR","DISPENSE",pin)
        sensor_ir_on(pin)
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
        global timed_dispense_timer
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
def suspend_pbka(pin=None):
    '''Stops the PBKA until it is toggled back on''' 
    #print("Start suspend_pbka()")
    if GPIO.input(PBKA) == 1: # only suspend if PBKA is enabled
        global pbka_sink_timer
        if pbka_sink_timer.is_alive() is True:
            pbka_sink_timer.cancel()
        global pbka_idle_timer
        if pbka_idle_timer.is_alive() is True:
            pbka_idle_timer.cancel()
    log_event("PBKA","SUSPEND",pin)
    #print("End suspend_pbka()")

# When the PBKA pin changes state or sensors turn off when the PBKA is enabled,
# (re)starts the PBKA Off timer to start the current sink cycle
# When PBKA is disabled, it stops the PBKA timers
def toggle_pbka(pin=None):
    '''Check the PBKA gpio pin value and enable(1) or disable(0) current sinking''' 
    #print("Start toggle_pbka()")
    event="DISABLED"
    if GPIO.input(PBKA) == 1:
        global pbka_idle_timer
        event="ENABLED"
        if pbka_idle_timer.is_alive() is True:
            pbka_idle_timer.cancel()
        pbka_idle_timer = threading.Timer(PBKA_OFF_PERIOD, pbka_sink)
        pbka_idle_timer.start()
    else:
        global pbka_sink_timer
        if pbka_sink_timer.is_alive() is True:
            pbka_sink_timer.cancel()
        if pbka_idle_timer.is_alive() is True:
            pbka_idle_timer.cancel()
    log_event("PBKA",event,pin)
    #print("End toggle_pbka()")

# Turns on sensor LEDs to sink current and keep powerbanks on,
# (re)starts timer to keep them on for number of seconds specified
def pbka_sink(pin="TO"):
    '''Starts timer to trigger the end of the sink'''
    #print("Start pbka_sink()")
    log_event("PBKA","SINK",pin)
    GPIO.output(SIR,1)
    global pbka_sink_timer
    if pbka_sink_timer.is_alive() is True:
        pbka_sink_timer.cancel()
    pbka_sink_timer = threading.Timer(PBKA_ON_PERIOD, pbka_idle)
    pbka_sink_timer.start()
    #print("End pbka_sink()")

# Turns off sensor LEDs, (re)starts timer to turn them back on
def pbka_idle(pin="TO"):
    '''Starts timer to trigger the next sink'''
    #print("Start pbka_idle()")
    log_event("PBKA","IDLE",pin)
    GPIO.output(SIR,0)
    global pbka_idle_timer
    if pbka_idle_timer.is_alive() is True:
        pbka_idle_timer.cancel()
    pbka_idle_timer = threading.Timer(PBKA_OFF_PERIOD, pbka_sink)
    pbka_idle_timer.start()
    #print("End pbka_idle()")

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

# When the CAL pin changes state
def toggle_calibration_mode(pin=None):
    '''Check the CAL gpio pin value and enable(1) or disable(0) calibration mode''' 
    #print("Start toggle_calibration_mode()")
    event="DISABLED"
    if GPIO.input(CAL) == 1: # Calibration mode is enabled
        event="ENABLED"
    log_event("CAL",event,pin)
    #print("End toggle_calibration_mode()")

# Call this to send an email alerting that an event has occurred
def send_email_alert(event):
    ''' Sends an email notifying that an event juts occurred '''
    # Set email subject and message
    message = "Subject: " + event + " Event at " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " \n\n " + event + " event detected at " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Send the email
    try:
        server = smtplib.SMTP(SMTP_SERVER,SMTP_PORT)
        server.ehlo() # Can be omitted
        server.starttls()
        server.ehlo() # Can be omitted
        server.login(SMTP_LOGIN, SMTP_P)
        server.sendmail(SMTP_SENDER, SMTP_RECEIVER, message)
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()
    log_event("SMTP","SEND",event)

# Log start of script
log_event("SCRIPT","START","INIT")
# Send email alert
threading.Thread(target=send_email_alert,args=["SCRIPT STARTUP"]).start()

# Initialize MT Sensor state - enable the sensor LEDs, check the sensor, and disable the sensor LEDs
GPIO.output(SIR,1)
update_mt("INIT")
GPIO.output(SIR,0)

# Set up GPIO interrupts - adding a bouncetime of 100ms to all interrupts
# Moved adding DEP and DIS interrupts to sensor_ir_on and remove them in sensor_ir_off
GPIO.add_event_detect(PIR, GPIO.RISING, pir_event, 100)	# PIR trigger
GPIO.add_event_detect(MAN, GPIO.RISING, manual_dispense, 100)	# manual dispense
GPIO.add_event_detect(TMR, GPIO.BOTH, toggle_timed_dispense, 100)	# timer toggle
GPIO.add_event_detect(PBKA, GPIO.BOTH, toggle_pbka, 100)	# PBKA toggle
GPIO.add_event_detect(CAL, GPIO.BOTH, toggle_calibration_mode, 100)	# calibration mode toggle

# Set up timers
# Timer for sensors, calls sensor_ir_off when SENSOR_IR_TIMEOUT seconds have passed
sensor_timer = threading.Timer(SENSOR_IR_TIMEOUT, sensor_ir_off)
# Timer for motor, calls motor_off when MOTOR_TIMEOUT seconds have passed
motor_timer = threading.Timer(MOTOR_TIMEOUT, motor_off)
# Timer for timed dispense, triggers a dispense event every TIMED_DISPENSE_PERIOD seconds
timed_dispense_timer = threading.Timer(TIMED_DISPENSE_PERIOD, timed_dispense)
# Timer for PBKA curent sink, sinks current for PBKA_ON_PERIOD
pbka_sink_timer = threading.Timer(PBKA_ON_PERIOD, pbka_idle)
# Timer for PBKA interval between current sinks, waits PBKA_OFF_PERIOD seconds between sinks
pbka_idle_timer = threading.Timer(PBKA_OFF_PERIOD, pbka_sink)

# Initialize timed dispense and PBKA enable/disable - do this after defining interrupts and timers
if DEFAULT_TOGGLE_TIMED_DISPENSE == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(TMR_SIG)+'/value')
if DEFAULT_TOGGLE_PBKA == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(PBKA_SIG)+'/value')

# Everything is interrupt- and timer-based, so script
# sleeps until an interrupt or timer calls a function
while True:
    time.sleep(1e6)
