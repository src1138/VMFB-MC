#!/usr/bin/python

import RPi.GPIO as GPIO
from datetime import datetime
import time
import threading

# Configuration variables
sensorTimeout=30
motorTimeout=10
timedDispensePeriod=600
timedDispenseStartTime=800
timedDispenseEndTime=1700
pbkaOnPeriod=1
pbkaOffPeriod=10

# Initialize RPi GPIO
# GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)

# Disable warnings
GPIO.setwarnings(False)

# Set GPIO pin numbers 
PIR=27 		#PIN 13
MT=23 		#PIN 16
MAN=26 		#PIN 37
PBKA=19 	#PIN 35
TMR=13 		#PIN 33
DIS=10 		#PIN 19
DEP=24 		#PIN 18
SIR=25 		#PIN 22
MTR=11 		#PIN 23
MT_SIG=5	#PIN 29

# Configure GPIO inputs
GPIO.setup([PIR,MT], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([MAN,PBKA,TMR], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# For DEP and DIS, if using a comparator pull_up_down=GPIO.PUD_UP, 
# if using an op amp, pull_up_down=GPIO.PUD_DOWN
GPIO.setup([DEP, DIS], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Configure GPIO outputs and set them to low initially
GPIO.setup([SIR,MTR,MT_SIG], GPIO.OUT, initial=GPIO.LOW)

def logEvent(eventType=None,event=None):
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "	" + str(eventType) + "	" + str(event) + "\n")
	
def PIREvent(pin=None):
	logEvent("PIR","+")
	sensorsOn()
	
def updateMT(pin=None):
	if GPIO.input(MT) == 1:
		GPIO.output(MT_SIG,1)
		logEvent("MT","+")
	else:
		GPIO.output(MT_SIG,0)
		logEvent("MT","-")
	
def sensorsOn(pin=None):
	if GPIO.input(PBKA) == 1:
		PBKASuspend()
    	GPIO.output(SIR,1)
	logEvent("SIR","+")
	updateMT()
	global sensorTimer
	if sensorTimer.is_alive() == True:
		sensorTimer.cancel()
	sensorTimer = threading.Timer(sensorTimeout,sensorsOff)
	sensorTimer.start()
	
def sensorsOff(pin=None):
	updateMT()
	GPIO.output(SIR,0)
	logEvent("SIR","-")
   	global sensorTimer
	if sensorTimer.is_alive() == True:
		sensorTimer.cancel()
	if GPIO.input(PBKA) == 1:
		PBKAEnable()

def DEPEvent(pin=None):
	logEvent("DEP","+")
	motorOn()
	
def DISEvent(pin=None):
	logEvent("DIS","+")
	motorOff()
	
def motorOn(pin=None):
	GPIO.output(MTR,1)
	logEvent("MTR","+")
	global motorTimer
	if motorTimer.is_alive() == True:
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
	sensorsOn()
	motorOn()

def timedDispense(pin=None):
	nowTime=int(datetime.now().strftime("%H%M"))
	logEvent("TMR",nowTime)
	logEvent("TMR","timedDispense")
	if (nowTime >= timedDispenseStartTime) & (nowTime <= timedDispenseEndTime):
		logEvent("TMR","+")
		sensorsOn()
		motorOn()
	global timedDispenseTimer
	if timedDispenseTimer.is_alive() == True:
		timedDispenseTimer.cancel()
 	timedDispenseTimer = threading.Timer(timedDispensePeriod,timedDispense)
 	timedDispenseTimer.start()
	
def TMREnable(pin=None):
	global timedDispenseTimer
	if GPIO.input(TMR) == 1:
		logEvent("TMR","ON")
		if timedDispenseTimer.is_alive() == True:
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
		if PBKAOffTimer.is_alive() == True:
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
	if PBKAOnTimer.is_alive() == True:
		PBKAOnTimer.cancel()
	PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
	PBKAOnTimer.start()

def PBKAOff(pin=None):
	logEvent("PBKA","-")
	GPIO.output(SIR,0)
	global PBKAOffTimer
	if PBKAOffTimer.is_alive() == True:
		PBKAOffTimer.cancel()
	PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)
	PBKAOffTimer.start()

# Set up GPIO interrupts
GPIO.add_event_detect(PIR, GPIO.RISING, PIREvent)
GPIO.add_event_detect(DEP, GPIO.RISING, DEPEvent)
GPIO.add_event_detect(DIS, GPIO.FALLING, DISEvent)
GPIO.add_event_detect(MAN, GPIO.RISING, MANEvent)
GPIO.add_event_detect(TMR, GPIO.BOTH, TMREnable)
GPIO.add_event_detect(PBKA, GPIO.BOTH, PBKAEnable)
	
# Set up timers
sensorTimer = threading.Timer(sensorTimeout, sensorsOff)
motorTimer = threading.Timer(motorTimeout, motorOff)
timedDispenseTimer = threading.Timer(timedDispensePeriod, timedDispense)
PBKAOnTimer = threading.Timer(pbkaOnPeriod, PBKAOff)
PBKAOffTimer = threading.Timer(pbkaOffPeriod, PBKAOn)

while True:
	time.sleep(1e6)
