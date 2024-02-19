#!/usr/bin/python

import RPi.GPIO as GPIO		# for GPIO access
from datetime import datetime	# to handle dates
import time			# to handle timers
import threading		# to handle timer and interupt threads

# Configuration variables
sensorTimeout=30		# seconds the sensors stay on after last PIR trigger
motorTimeout=10			# soconds dispenser motor stays on before it times out
timedDispensePeriod=600		# seconds between timed dispense when it is enabled
timedDispenseStartTime=800	# time of day timed dispense will start when enabled (HHMM format, don't use leading zeros)
timedDispenseEndTime=1700	# time of day timed dispense will stop when enabled (HHMM format, don't use leading zeros)
pbkaOnPeriod=1			# seconds the PBKA will turn the sensors on to sink current to keep a powerbank on
pbkaOffPeriod=10		# seconds between PBKA current sinks

# Initialize RPi GPIO
# GPIO.setmode(GPIO.BOARD)	# uses board pin numbers to reference pins
GPIO.setmode(GPIO.BCM)		# uses gpio numbers to reference pins

# Disable warnings
GPIO.setwarnings(False)		# disables GPIO warnings (ex. pin already in use)

# Set GPIO pin numbers 
PIR=27 		#PIN 13 - input to sense PIR signal (high signal means PIR was triggered)
MT=23 		#PIN 16	- input to sense hopper (almost) empty signal (high initiates a dispense event)
MAN=26 		#PIN 37 - input to sense manual dispense event (high=ok, low= (almost) empty
PBKA=19 	#PIN 35 - input to sense if PBKA is enabled (high=enabled, low=disabled)
TMR=13 		#PIN 33 - input to sense if timer is enabled (high=enabled, low=disabled)
DIS=10 		#PIN 19 - input to sense a deposit event
DEP=24 		#PIN 18 - input to sense a dispense event
SIR=25 		#PIN 22 - output to turn on IR sensor LEDs
MTR=11 		#PIN 23 - output to turn on dispense motor
MT_SIG=5	#PIN 29 - output to indicate if hopper is (almost) empty

# Configure GPIO inputs with pull-downs
GPIO.setup([PIR,MT,MAN,PBKA,TMR], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([DEP,DIS], GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Configure GPIO outputs and set them to low initially
GPIO.setup([SIR,MTR,MT_SIG], GPIO.OUT, initial=GPIO.LOW)

# Logs events as <timestamp>\t<eventType>\t<event>, casts areguments as strings 
def logEvent(eventType=None,event=None,pin=None):
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "	" + str(eventType) + "	" + str(event) + "	" + str(pin) + "\n")

# When PIR signal goes high, enables sensors
# When PIR goes low, it just logs the event	
def PIREvent(pin=None):
	logEvent("PIR",1,pin)
	sensorsOn(pin)

# When sesors are on, checks the empty sensor and updates the MT_SIG pin state
# Takes this approach because when the sensor LEDs are off the signal is always low 	
def updateMT(pin=None):
	event=0
	if GPIO.input(MT) == 1:
		GPIO.output(MT_SIG,1)
		event=1
	else:
		GPIO.output(MT_SIG,0)
	logEvent("MT",event,pin)

# Suspends PBKA if it is enabled, turns on sensor LEDs, 
# updates empty sensor status, and (re)starts sensor timeout timer	
def sensorsOn(pin=None):
	logEvent("SIR","ON",pin)
	if GPIO.input(PBKA) == 1:
		PBKASuspend(pin)
    	GPIO.output(SIR,1)
	updateMT(pin)
	global sensorTimer
	if sensorTimer.is_alive() == True:
		sensorTimer.cancel()
	sensorTimer = threading.Timer(sensorTimeout,sensorsOff)
	sensorTimer.start()

# Updates empty sensor status, turns off sensor LEDs, stops sensor timeout timer, re-enables PbKA if it is enabled
def sensorsOff(pin="TO"):
	logEvent("SIR","OFF",pin)
	updateMT(pin)
	GPIO.output(SIR,0)
   	global sensorTimer
	if sensorTimer.is_alive() == True:
		sensorTimer.cancel()
	if GPIO.input(PBKA) == 1:
		PBKAEnable(pin)

# When a deposit event is detected, turn on the dispense motor
def DEPEvent(pin=None):
	logEvent("DEP",1,pin)
	motorOn(pin)

# When a dispense event is detected, turns off the dispense motor	
def DISEvent(pin=None):
	logEvent("DIS",1,pin)
	motorOff(pin)
	
# Turns on the motor and (re)starts the motor timeout timer
def motorOn(pin=None):
	logEvent("MTR_ON",event,pin)
	GPIO.output(MTR,1)
	global motorTimer
	if motorTimer.is_alive() == True:
		motorTimer.cancel()
	motorTimer = threading.Timer(motorTimeout,motorOff)
	motorTimer.start()

# Turns off the motor and stops the motor timeout timer
def motorOff(pin="TO"):
	GPIO.output(MTR,0)
	logEvent("MTR_OFF",event,pin)
	global motorTimer
	if motorTimer.is_alive() == True:
		motorTimer.cancel()

# When a manual dispense event is detected, turns on the sensors and starts the dispense motor
def MANEvent(pin=None):
	logEvent("MAN","DISPENSE",pin)
	sensorsOn(pin)
	motorOn(pin)

# if current time is equal to or after the start time and equal to
# or before the end time, turns on the sensor LEDs and starts the 
# motor and (re)starts the timed dispense interval timer
def timedDispense(pin="TO"):
	nowTime=int(datetime.now().strftime("%H%M"))
	# If you want to define multiple windows of timer operation
	# of operation on certain days or dates you can do so in 
	# the following if statement    
	if (nowTime >= timedDispenseStartTime) & (nowTime <= timedDispenseEndTime):
		logEvent("TMR","DISPENSE",pin)
		sensorsOn(pin)
		motorOn(pin)
	global timedDispenseTimer
	if timedDispenseTimer.is_alive() == True:
		timedDispenseTimer.cancel()
 	timedDispenseTimer = threading.Timer(timedDispensePeriod,timedDispense)
 	timedDispenseTimer.start()

# When the TMR pin changes state, (re)starts the timed dispense
# timer if it is high, stops it when it is low
def TMREnable(pin=None):
	event="DISABLED"
	global timedDispenseTimer
	if GPIO.input(TMR) == 1:
		event="ENABLED"
		if timedDispenseTimer.is_alive() == True:
			timedDispenseTimer.cancel()
		timedDispenseTimer = threading.Timer(timedDispensePeriod,timedDispense)
		timedDispenseTimer.start()
	else:
		if timedDispenseTimer.is_alive() == True:
			timedDispenseTimer.cancel()
	logEvent("TMR",event,pin)

# Suspends the PBKA current sinking, stops PBKA timers
def PBKASuspend(pin=None):
	if GPIO.input(PBKA) == 1: # only suspend if PBKA is enabled
		if PBKAOnTimer.is_alive() == True:
			PBKAOnTimer.cancel()
		if PBKAOffTimer.is_alive() == True:
			PBKAOffTimer.cancel()
		logEvent("PBKA","SUSPEND",pin)

# Then the PBKA pin changes state or sensors turn off when the PBKA is enabled,
# (re)starts the PBKA Off timer to start the current sink cycle
# When PBKA is disabled, it stops the PBKA timers
def PBKAEnable(pin=None):
	event="DISABLED"
	global PBKAOffTimer
	if GPIO.input(PBKA) == 1:
		event="ENABLED"
		if PBKAOffTimer.is_alive() == True:
			PBKAOffTimer.cancel()
		PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
		PBKAOffTimer.start()
	else:
		if PBKAOnTimer.is_alive() == True:
			PBKAOnTimer.cancel()
		if PBKAOffTimer.is_alive() == True:
			PBKAOffTimer.cancel()
	logEvent("PBKA",event,pin)
        
# Turns on sensor LEDs to sink current and keep powerbanks on, 
# (re)starts timer to keep them on for number of seconds specified			
def PBKAOn(pin="TO"):
	logEvent("PBKA","SINK",pin)
	GPIO.output(SIR,1)
	global PBKAOnTimer
	if PBKAOnTimer.is_alive() == True:
		PBKAOnTimer.cancel()
	PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
	PBKAOnTimer.start()

# Turns off sensor LEDs, (re)starts timer to turn them back on
def PBKAOff(pin="TO"):
	logEvent("PBKA","IDLE",pin)
	GPIO.output(SIR,0)
	global PBKAOffTimer
	if PBKAOffTimer.is_alive() == True:
		PBKAOffTimer.cancel()
	PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
	PBKAOffTimer.start()

# Set up GPIO interrupts
GPIO.add_event_detect(PIR, GPIO.RISING, PIREvent)	# Interrupt for PIR when signal goes low>high
GPIO.add_event_detect(DEP, GPIO.FALLING, DEPEvent)	# Interrupt for Deposit when signal goes high>low - so it triggers only when the object has passed by the sensor
GPIO.add_event_detect(DIS, GPIO.FALLING, DISEvent)	# Interupt for Dispense when signal goes high>low - so it triggers only when the nut/nugget/pellet/kibble has passed by the sensor
GPIO.add_event_detect(MAN, GPIO.RISING, MANEvent)	# Interrupt for manual dispense when signal goes low>high
GPIO.add_event_detect(TMR, GPIO.BOTH, TMREnable)	# Interupt for timer enable when pin changes state
GPIO.add_event_detect(PBKA, GPIO.BOTH, PBKAEnable)	# Interrupt for PBKA enable when pin changes state
	
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

# Everything is interrupt- and timer-based, so script sleeps until an interrupt or timer calls a function 
while True:
	time.sleep(1e6) 
