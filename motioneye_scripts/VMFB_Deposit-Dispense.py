#!/usr/bin/python

# interrupt-based GPIO logging for deposit and dispense sensors and starting and stopping the dispense motor

import RPi.GPIO as GPIO
from datetime import datetime
import time
import threading

# Initialize RPi GPIO
GPIO.setmode(GPIO.BOARD)

# Set pin numbers (not the same as the GPIO Pin number)
DEP = 18 #RPi ZeroW Pin #24
DIS = 19 #RPi ZeroW Pin #10
MTRCON = 11 #RPi ZeroW Pin #23

# Configure input pins
# If using a comparator pull_up_down=GPIO.PUD_UP, is using an op amp, pull_up_down=GPIO.PUD_DOWN
GPIO.setup([DEP, DIS], GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Configure output pins
GPIO.setup([MTRCON], GPIO.OUT)
# Set outputs to low initially
GPIO.output(MTRCON, 0)

# logging and monitoring routines
def deposit(pin=None):
	# Log the deposit event
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	DEP +\n")
	# start the dispense motor and log the event
	GPIO.output(MTRCON, 1)
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	MTR	+\n")
        
def dispense(pin=None):
    # Log the dispense event
    # Consider making this 
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	DIS	+\n")
	# stop the dispense motor and log the event
	GPIO.output(MTRCON, 0)
	with open("/data/log/VMFB_"+str(datetime.now().strftime("%Y-%m-%d"))+".log", "a+") as file:
		file.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "	MTR	-\n")
	
# If using a comparator, we want to know about rising edges for the deposit and falling edges for the dispense events
# to avoid jams and unjamming to trigger events and to avoid triggering two interrupt events per deposit/dispense
# If using an op amp, this is reversed
GPIO.add_event_detect(DEP, GPIO.RISING, deposit)
GPIO.add_event_detect(DIS, GPIO.FALLING, dispense)

while True:
	time.sleep(1e6)
