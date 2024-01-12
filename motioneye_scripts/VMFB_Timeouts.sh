#!/bin/bash

# controls timeouts for sensors, motor and PBKA

# sensor timeout in seconds
sensor_timeout=30
# motor timeout in seconds
motor_timeout=10
# powerbank keep-alive interval in seconds
pbka_interval=10
# powerbank keep-alive pulse length in seconds
pbka_pulse_length=1

# Set up pins for Sensor IR and Motor

#THIS SCRIPT NEEDS TO SHUT OFF THE SENSORS 30 SEC AFTER LAST PIR TRIGGER AND THE MOTOR 10 SEC AFTER LAST DEPOSIT TRIGGER

# Sensors
# check if sensors are on, if not, exit
# check if PIR is triggering - if so, exit
# parse log for last PIR trigger and get datetime
# subtract last PIR trigger datetime from now
# if result is >= sensor_timeout, turn sensors off
# 	log sensor timeout event

# Motor
# check if motor is on, if not, exit
# parse log for last Deposit trigger and get datetime
# subtract last Deposit trigger datetime from now
# if result is >= motor_timeout, turn motor off
# 	log motor timeout event

#PBKA

# check if PBKA is enabled (PBKA_enable=$(cat /data/log/PBKA_enable == 1) else exit
# check if PIR is triggering - if so, exit

# PBKA Interval

# parse log for last PIR trigger event and get datetime
# subtract last PIR trigger datetime from now+pbka_pulse_length
# if result is >= sensor_timeout+pbka_interval, continue, else exit

# PBKA Pulse

# if sensors are off
# parse log for last PBKA pulse off event and get datetime - 
# 	if no PBKA pulse event log for today, turn on sensors
# 		log PBKA on event
# 	else subtract pbka_pulse_length from now
# 		if result is >= pbka_interval, turn on sensors
# 			log PBKA on event

# if sensors are on
# parse log for last PBKA pulse on event and get datetime
# 	if no PBKA pulse event log for today, turn off sensors
# 		log PBKA off event
# 	else subtract last PBKA pulse event datetime from now
# 		if result is >= pbka_pulse_length, turn off sensors
# 			log PBKA off event


# sleep 1 sec
