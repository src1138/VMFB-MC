#!/usr/bin/python

import RPi.GPIO as GPIO
from datetime import datetime
import time
import threading

# Configuration variables
sensorTimeout=30
motorTimeout=10
timedDispensePeriod=5400
timedDispenseStartTime=0800
timedDispenseEndTime=1700
pbkaOnPeriod=1
pbkaOffPeriod=10

# Initialize RPi GPIO
GPIO.setmode(GPIO.BOARD)

# Disable warnings
GPIO.setwarnings(False)

# Set GPIO pin numbers 
PIR=13 #GPIO 27
MT=16 #GPIO 23
MAN=37 #GPIO 26
PBKA=35 #GPIO 19
TMR=33 #GPIO 13
DIS=19 #GPIO 10
DEP=18 #GPIO 24
SIR=22 #GPIO 25
MTR=23 #GPIO 11
MT_SIG=29 #GPIO 5

# Configure GPIO inputs
GPIO.setup([PIR,MT], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([MAN,PBKA,TMR], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# For DEP and DIS, if using a comparator pull_up_down=GPIO.PUD_UP, 
# if using an op amp, pull_up_down=GPIO.PUD_DOWN
GPIO.setup([DEP, DIS], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Configure GPIO outputs
GPIO.setup([SIR,MTR,MT_SIG], GPIO.OUT)
# Set outputs to low initially
GPIO.output(MT_SIG, 0)
GPIO.output(MTR, 0)
GPIO.output(SIR, 0)

def logEvent(eventType=None,event=None):
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "	" + eventType + "	" + event + "\n")
	
	
def PIREvent(pin=None):
	logEvent("PIR","+")
	sensorsOn
	
def checkMT(pin=None):
	if GPIO.input(MT) == 1:
		GPIO.output(MT_SIG,1)
		logEvent("MT","+")
	else:
		GPIO.output(MT_SIG,0)
		logEvent("MT","-")
	
def sensorsOn(pin=None):
	GPIO.output(SIR,1)
	PBKASuspend
	logEvent("SIR","+")
	checkMT
	global sensorTimer
	if sensorTimer.is_alive() == False:
		sensorTimer = threading.Timer(sensorTimeout,sensorsOff)
		sensorTimer.start()
	else:
		sensorTimer.cancel()
		sensorTimer = threading.Timer(sensorTimeout,sensorsOff)
		sensorTimer.start()
	
def sensorsOff(pin=None):
	checkMT
	GPIO.output(SIR,0)
	PBKAEnable
	logEvent("SIR","-")
	global sensorTimer
	if sensorTimer.is_alive() == True:
		sensorTimer.cancel()

def DEPEvent(pin=None):
	logEvent("DEP","+")
	motorOn
	
def DISEvent(pin=None):
	logEvent("DIS","+")
	motorOff
	
def motorOn(pin=None):
	GPIO.output(MTR,1)
	logEvent("MTR","+")
	global motorTimer
	if motorTimer.is_alive() == False:
		motorTimer = threading.Timer(motorTimeout,motorOff)
		motorTimer.start()
	else:
		motorTimer.cancel()
		motorTimer = threading.Timer(motorTimeout,motorOff)
		motorTimer.start()

def motorOff(pin=None):
	GPIO.output(MTR,0)
	logEvent("MTR","-")
	global motorTimer
	if motorTimer.is_alive() == True:
		motorTimer.cancel()

def MANEvent(pin=None):
	logEvent("MAN","+")
	sensorsOn
	motorOn

def timedDispense(pin=None):
	nowTime=int(datetime.now().strftime("%H%M"))
	if (nowTime >= timedDispenseStartTime) AND (nowTime <= timedDispenseEndTime):
		logEvent("TMR","+")
		sensorsOn
		motorOn
	
def TMREnable(pin=None):
	global timedDispenseTimer
	if GPIO.input(TMR) == 1:
		logEvent("TMR","ON")
		if timedDispenseTimer.is_alive() == False:
			timedDispenseTimer = threading.Timer(timedDispensePeriod,timedDispense)
			timedDispenseTimer.start()
		else:
			timedDispenseTimer.cancel()
			timedDispenseTimer = threading.Timer(timedDispensePeriod,timedDispense)
			timedDispenseTimer.start()
	else:
		logEvent("TMR","OFF")
		if timedDispenseTimer.is_alive() == True:
			timedDispenseTimer.cancel()

def PBKASuspend(pin=None):
	if GPIO.input(PBKA) == 1:
		logEvent("PBKA","SUS")
		if PBKAOnTimer.is_alive() == True:
			PBKAOnTimer.cancel()
		if PBKAOffTimer.is_alive() == True:
			PBKAOffTimer.cancel()
			
def PBKAEnable(pin=None):
	global PBKAOffTimer
	if GPIO.input(PBKA) == 1:
		logEvent("PBKA","ON")
		if PBKAOffTimer.is_alive() == False:
			PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
			PBKAOffTimer.start()
		else:
			PBKAOffTimer.cancel()
			PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
			PBKAOffTimer.start()
	else:
		logEvent("PBKA","OFF")
		if PBKAOnTimer.is_alive() == True:
			PBKAOnTimer.cancel()
		if PBKAOffTimer.is_alive() == True:
			PBKAOffTimer.cancel()
			
def PBKAOn(pin=None):
	logEvent("PBKA","+")
	GPIO.output(SIR,1)
	global PBKAOnTimer
	if PBKAOnTimer.is_alive() == False:
		PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
		PBKAOnTimer.start()
	else:
		PBKAOnTimer.cancel()
		PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
		PBKAOnTimer.start()

def PBKAOff(pin=None):
	logEvent("PBKA","-")
	GPIO.output(SIR,0)
	global PBKAOffTimer
	if PBKAOffTimer.is_alive() == False:
		PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
		PBKAOffTimer.start()
	else:
		PBKAOffTimer.cancel()
		PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
		PBKAOffTimer.start()

# Set up GPIO interrupts
GPIO.add_event_detect(PIR, GPIO.RISING, PIREvent)	
GPIO.add_event_detect(DEP, GPIO.RISING, DEPEvent)
GPIO.add_event_detect(DIS, GPIO.FALLING, DISEvent)

# Set up GPIO interrupts
GPIO.add_event_detect(MAN, GPIO.RISING, MANEvent)	
GPIO.add_event_detect(TMR, GPIO.BOTH, TMREnable)
GPIO.add_event_detect(PBKA, GPIO.BOTH, PBKAEnable)
	
# Set up timers
sensorTimer = threading.Timer(sensorTimeout, sensorsOff)
motorTimer = threading.Timer(motorTimeout, motorOff)
timedDispenseTimer = threading.Timer(timedDispensePeriod, timedDispense)
PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)

