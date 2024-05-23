#!/usr/bin/python

from datetime import datetime	# to handle dates
import time			# to handle timers
import threading		# to handle timer and interupt threads
# import urllib2		# to handle http requests to enable/disable motion detection
import os 			# needed to execute system commands to start/stop motioneye server
import RPi.GPIO as GPIO		# for GPIO access

# Configuration variables
sensorTimeout=30		# seconds the sensors stay on after last PIR trigger
motorTimeout=10			# soconds dispenser motor stays on before it times out
timedDispensePeriod=3600	# seconds between timed dispense when it is enabled
timedDispenseStartTime=500	# time of day timed dispense will start when enabled
				# (HHMM format, don't use leading zeros)
timedDispenseEndTime=1600	# time of day timed dispense will stop when enabled
				# (HHMM format, don't use leading zeros)
pbkaOnPeriod=1			# seconds the PBKA will sink current to keep a powerbank on
pbkaOffPeriod=10		# seconds between PBKA current sinks
defaultEnableTimer=1   		# set to 1 to enable timer on startup
defaultEnablePBKA=0      	# set to 1 to enable PBKA on startup

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
def logEvent(eventType=None,event=None,pin=None):
    #print("Start logEvent()")
    with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
        file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "	" + str(eventType) + "	" + str(event) + "	" + str(pin) + "\n")
    #print("End logEvent()")

# When PIR signal goes high, enables sensors
def PIREvent(pin=None):
    #print("Start PIREvent()")
    logEvent("PIR",1,pin)
    sensorsOn(pin)
    #print("End PIREvent()")

# When sensors are on, checks the empty sensor and updates the MT_SIG pin state
# Takes this approach because when the sensor LEDs are off the signal is always low
def updateMT(pin=None):
    #print("Start updateMT()")
    event=0
    if GPIO.input(MT) == 1:
        GPIO.output(MT_SIG,1)
        event=1
    else:
        GPIO.output(MT_SIG,0)
    logEvent("MT",event,pin)
    #print("End updateMT()")

# Suspends PBKA if it is enabled, turns on sensor LEDs,
# updates empty sensor status, and (re)starts sensor timeout timer
def sensorsOn(pin=None):
    #print("Start sensorsOn()")
    logEvent("SIR","ON",pin)
    if GPIO.input(PBKA) == 1:
        PBKASuspend(pin)
    GPIO.output(SIR,1)
    global sensorTimer
    if sensorTimer.is_alive() is True:
        sensorTimer.cancel()
    sensorTimer = threading.Timer(sensorTimeout, sensorsOff)
    sensorTimer.start()
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
    GPIO.add_event_detect(DEP, GPIO.RISING, DEPEvent, 100)
    GPIO.add_event_detect(DIS, GPIO.RISING, DISEvent, 100)
    updateMT(pin)
    # if the trigger came from the PIR, enable camera, enable motion detection in motioneye
    # and log the event
    if pin == PIR:
        # enable the camera
        # enableCamera(pin)
        # enable motion detection
        # urllib2.urlopen("http://localhost:7999/1/detection/start").read()
        os.system('curl http://localhost:7999/1/detection/start')
        logEvent("MOD","START",pin)
    #print("End sensorsOn()")

# Updates empty sensor status, turns off sensor LEDs, stops sensor timeout timer,
# re-enables PBKA if it is enabled
def sensorsOff(pin="TO"):
    #print("Start sensorsOff()")
    # Some PIR sensors stay on until they don't detect anything
    # this will check again to make sure the PIR is not triggering before disabling the sensors
    if GPIO.input(PIR) == 1:
        sensorsOn(PIR)
    else:
        updateMT(pin)
        logEvent("SIR","OFF",pin)
        GPIO.output(SIR,0)
        if sensorTimer.is_alive() is True:
            sensorTimer.cancel()
        if GPIO.input(PBKA) == 1:
            PBKAEnable(pin)
        # Remove event detect for DEP and DIS
        GPIO.remove_event_detect(DEP)
        GPIO.remove_event_detect(DIS)
	# Make sure the motor is off since the sensors are off
        motorOff(pin)
        # end any recording disable motion detection in motioneye and log the response
        # urllib2.urlopen("http://localhost:7999/1/detection/pause").read()
        os.system('curl http://localhost:7999/1/detection/pause')
        logEvent("MOD","PAUSE",pin)
        # urllib2.urlopen("http://localhost:7999/1/action/eventend").read()
        os.system('curl http://localhost:7999/1/action/eventend')
        logEvent("REC","STOP",pin)
        # disable the camera to save power while sensors are off
        # disableCamera(pin)
    #print("End sensorsOff()")

# When a deposit event is detected, turn on the dispense motor
def DEPEvent(pin=None):
    #print("Start DEPEvent()")
    if GPIO.input(DIS) == 0:
        logEvent("DEP",1,pin)
        motorOn(pin)
    else:
        # If there is something triggering the dispense sensor
        # when a deposit is sensed, log it and don't turn on the motor
        logEvent("DEP","DISJAM",pin)
    #print("End DEPEvent()")

# When a dispense event is detected, turns off the dispense motor
def DISEvent(pin=None):
    #print("Start DISEvent()")
    logEvent("DIS",1,pin)
    motorOff(pin)
    #print("End DISEvent()")

# Turns on the motor and (re)starts the motor timeout timer
def motorOn(pin=None):
    #print("Start motorOn()")
    logEvent("MTR","ON",pin)
    GPIO.output(MTR,1)
    global motorTimer
    if motorTimer.is_alive() is True:
        motorTimer.cancel()
    motorTimer = threading.Timer(motorTimeout, motorOff)
    motorTimer.start()
    #print("End motorOn()")

# Turns off the motor and stops the motor timeout timer
def motorOff(pin="TO"):
    #print("Start motorOff()")
    logEvent("MTR","OFF",pin)
    GPIO.output(MTR,0)
    if motorTimer.is_alive() is True:
        motorTimer.cancel()
    #print("End motorOff()")

# When a manual dispense event is detected, turns on the sensors and starts the dispense motor
def MANEvent(pin=None):
    #print("Start MANEvent()")
    logEvent("MAN","DISPENSE",pin)
    sensorsOn(pin)
    motorOn(pin)
    #print("End MANEvent()")

# if current time is equal to or after the start time and equal to
# or before the end time, turns on the sensor LEDs and starts the
# motor and (re)starts the timed dispense interval timer
def timedDispense(pin="TO"):
    #print("Start timedDispense()")
    nowTime=int(datetime.now().strftime("%H%M"))
    # If you want to define multiple windows of timer operation
    # of operation on certain days or dates you can do so in
    # the following if statement
    if (nowTime >= timedDispenseStartTime) & (nowTime <= timedDispenseEndTime):
        logEvent("TMR","DISPENSE",pin)
        sensorsOn(pin)
        motorOn(pin)
    else:
        logEvent("TMR","SUSPENDED",pin)
    global timedDispenseTimer
    if timedDispenseTimer.is_alive() is True:
        timedDispenseTimer.cancel()
    timedDispenseTimer = threading.Timer(timedDispensePeriod, timedDispense)
    timedDispenseTimer.start()
    #print("End timedDispense()")

def TMRSuspend(pin=None):
    #print("Start TMRSuspend()")
    if GPIO.input(TMR) == 1: # only suspend if TMR is enabled
        if timedDispenseTimer.is_alive() is True:
            timedDispenseTimer.cancel()
    logEvent("TMR","SUSPEND",pin)
    #print("End TMRSuspend()")

# When the TMR pin changes state, (re)starts the timed dispense
# timer if it is high, stops it when it is low
def TMREnable(pin=None):
    #print("Start TMREnable()")
    event="DISABLED"
    global timedDispenseTimer
    if GPIO.input(TMR) == 1:
        event="ENABLED"
        if timedDispenseTimer.is_alive() is True:
            timedDispenseTimer.cancel()
        timedDispenseTimer = threading.Timer(timedDispensePeriod, timedDispense)
        timedDispenseTimer.start()
    else:
        if timedDispenseTimer.is_alive() is True:
            timedDispenseTimer.cancel()
    logEvent("TMR",event,pin)
    #print("End TMREnable()")

# Suspends the PBKA current sinking, stops PBKA timers
def PBKASuspend(pin=None):
    #print("Start PBKASuspend()")
    if GPIO.input(PBKA) == 1: # only suspend if PBKA is enabled
        if PBKAOnTimer.is_alive() is True:
            PBKAOnTimer.cancel()
        if PBKAOffTimer.is_alive() is True:
            PBKAOffTimer.cancel()
    logEvent("PBKA","SUSPEND",pin)
    #print("End PBKASuspend()")

# When the PBKA pin changes state or sensors turn off when the PBKA is enabled,
# (re)starts the PBKA Off timer to start the current sink cycle
# When PBKA is disabled, it stops the PBKA timers
def PBKAEnable(pin=None):
    #print("Start PBKAEnable()")
    event="DISABLED"
    if GPIO.input(PBKA) == 1:
        global PBKAOffTimer
        event="ENABLED"
        if PBKAOffTimer.is_alive() is True:
            PBKAOffTimer.cancel()
        PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
        PBKAOffTimer.start()
    else:
        global PBKAOnTimer
        if PBKAOnTimer.is_alive() is True:
            PBKAOnTimer.cancel()
        if PBKAOffTimer.is_alive() is True:
            PBKAOffTimer.cancel()
    logEvent("PBKA",event,pin)
    #print("End PBKAEnable()")

# Turns on sensor LEDs to sink current and keep powerbanks on,
# (re)starts timer to keep them on for number of seconds specified
def PBKAOn(pin="TO"):
    #print("Start PBKAOn()")
    logEvent("PBKA","SINK",pin)
    GPIO.output(SIR,1)
    global PBKAOnTimer
    if PBKAOnTimer.is_alive() is True:
        PBKAOnTimer.cancel()
    PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
    PBKAOnTimer.start()
    #print("End PBKAOn()")

# Turns off sensor LEDs, (re)starts timer to turn them back on
def PBKAOff(pin="TO"):
    #print("Start PBKAOff()")
    logEvent("PBKA","IDLE",pin)
    GPIO.output(SIR,0)
    global PBKAOffTimer
    if PBKAOffTimer.is_alive() is True:
        PBKAOffTimer.cancel()
    PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
    PBKAOffTimer.start()
    #print("End PBKAOff()")

# Disable camera to save power
def disableCamera(pin=None):
    #print("Start disableCamera()")
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
    logEvent("CAM","DISABLE",pin)
    #print("End disableCamera()")

def enableCamera(pin=None):
    #print("Start enableCamera()")
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
    logEvent("CAM","ENABLE",pin)
    #print("End enableCamera()")

# Enables interrupt to call sensorsOn() when the PIR triggers
def PIREnable(pin=None):
    #print("Start enablePIR()")
    logEvent("PIR","ENABLE",pin)
    GPIO.remove_event_detect(PIR)	# Remove interrupt for PIR before adding to avoid exception
    GPIO.add_event_detect(PIR, GPIO.RISING, PIREvent, 100)	# Add interrupt for PIR
    #print("End enablePIR()")

# Disables interrupt to call sensorsOn() when the PIR triggers
def PIRDisable(pin=None):
    #print("Start disablePIR()")
    GPIO.remove_event_detect(PIR)	# Remove interrupt for PIR
    logEvent("PIR","DISABLE",pin)
    #print("End disablePIR()")

def sensorsDisable(pin=None):
    #print("Start sensorsDisable()")
    # Stop the sensor IR timeout timer
    if sensorTimer.is_alive() is True:
        sensorTimer.cancel()
    # Remove event detect for DEP and DIS
    GPIO.remove_event_detect(DEP)
    GPIO.remove_event_detect(DIS)
    logEvent("SENSORS","DISABLE",pin)
    #print("End sensorsDisable()")

# When the CAL pin changes state
def CALEnable(pin=None):
    #print("Start CALenable()")
    event="DISABLED"
    if GPIO.input(CAL) == 1: # Calibration mode is enabled
        event="ENABLED"
        PIRDisable(pin) # Disable the PIR interrupt
        sensorsDisable(pin) # Make sure interrupts are removed for deposit and dispense sensors
        motorOff(pin) # Turn off the motor in case it is running
        TMRSuspend(pin) # Suspend timed dispense if it is enabled
        PBKASuspend(pin) # Suspensd the PBKA if it is enabled
        GPIO.output(SIR,1) # Turn on the sensor LEDs
    else: # Calibration mode is disabled
        GPIO.output(SIR,0) # Turn off the sensor LEDs
        PIREnable(pin) # Enable the PIR interrupt
        TMREnable(pin) # Turn on timed dispense if it is enabled
        PBKAEnable(pin) # Turn on the PBKA if it is enabled
    logEvent("CAL",event,pin)
    #print("End CALenable()")

# Log start of script
logEvent("SCRIPT","START","INIT")

# Initialize MT Sensor state - enable the sensor LEDs, check the sensor, and disable the sensor LEDs
GPIO.output(SIR,1)
updateMT("INIT")
GPIO.output(SIR,0)

# Set up GPIO interrupts - adding a bouncetime of 100ms to all interrupts
# Moved adding DEP and DIS interrupts to sensorsOn and remove them in sensorsOff
PIREnable("INIT")
GPIO.add_event_detect(MAN, GPIO.RISING, MANEvent, 100)	# Interrupt for manual dispense
GPIO.add_event_detect(TMR, GPIO.BOTH, TMREnable, 100)	# Interupt for timer enable
GPIO.add_event_detect(PBKA, GPIO.BOTH, PBKAEnable, 100)	# Interrupt for PBKA enable
GPIO.add_event_detect(CAL, GPIO.BOTH, CALEnable, 100)	# Interrupt for calibration mode enable

# Set up timers
# Timer for sensors, calls sensorsOff when sensorTimeout seconds have passed
sensorTimer = threading.Timer(sensorTimeout, sensorsOff)
# Timer for motor, calls motorOff when motorTimeout seconds have passed
motorTimer = threading.Timer(motorTimeout, motorOff)
# Timer for timed dispense, triggers a dispense event every timedDispensePeriod seconds
timedDispenseTimer = threading.Timer(timedDispensePeriod, timedDispense)
# Timer for PBKA curent sink, sinks current for pbkaOnPeriod
PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
# Timer for PBKA interval between current sinks, waits pbkaOffPeriod seconds between sinks
PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)

# Initialize timed dispense and PBKA enable/disable - do this after defining interrupts and timers
if defaultEnableTimer == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(TMR_SIG)+'/value')
if defaultEnablePBKA == 1:
    os.system('echo "1" >| /sys/class/gpio/gpio'+str(PBKA_SIG)+'/value')

# Everything is interrupt- and timer-based, so script
# sleeps until an interrupt or timer calls a function
while True:
    time.sleep(1e6)
