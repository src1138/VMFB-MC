#!/usr/bin/python

# interrupt-based GPIO logging for deposit and dispense sensors and starting and stopping the dispense motor

import RPi.GPIO as GPIO
from datetime import datetime
import time
import threading

# Initialize RPi GPIO
GPIO.setmode(GPIO.BOARD)

# Set pin numbers (not the same as the GPIO Pin number)
DEP = 18 # G24
DIS = 19 # G10
MTRCON = 11 # G23

# Configure input pins
# If using a LM393 comparator pull_up_down=GPIO.PUD_UP, is using an LM358 op amp, pull_up_down=GPIO.PUD_DOWN
GPIO.setup([DEP, DIS], GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Configure output pins
GPIO.setup([MTRCON], GPIO.OUT)
# Set outputs to low initially
GPIO.output(MTRCON, 0)

# logging and monitoring routines
def logDEP(pin=None):
	# Log the deposit event
	DEPtext = "-"
	if (GPIO.input(DEP) == True):
		DEPtext = "+"
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	DEP	" + str(GPIO.input(DEP))	+ "	" + DEPtext + "\n")
	# start the dispense motor
	GPIO.output(MTRCON, 1)
        
def logDIS(pin=None):
    	DIStext = "-"
	if (GPIO.input(DIS) == True):
		DIStext = "+"
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	DIS " + str(GPIO.input(DIS))	+ " " + DIStext + "\n")
	# stop the dispense motor
	GPIO.output(MTRCON, 0)
	
# We want to know about falling and rising edges for deposit and dispense
GPIO.add_event_detect(DEP, GPIO.BOTH, logDEP)
GPIO.add_event_detect(DIS, GPIO.BOTH, logDIS)

while True:
	time.sleep(1e6)
