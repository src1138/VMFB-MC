#!/bin/bash

# Assign pins
SIR=25 #RPi ZeroW Pin #22
MTR=11 #RPi ZeroW Pin #23

# timer interval between dispenses in seconods
timer_interval=5400 #90 mins
# time of day for timer to start
timer_ontime="0600" #6:00am
# time of day for timer to stop
timer_offtime="1800" #6:00pm
 
# Verify they are set up, else initialize them
#test -e /sys/class/gpio/gpio$SIR ||
#  (echo $SIR > /sys/class/gpio/export \
#   && echo out > /sys/class/gpio/gpio$SIR/direction)
#test -e /sys/class/gpio/gpio$MTR ||
#  (echo $MTR > /sys/class/gpio/export \
#   && echo out > /sys/class/gpio/gpio$MTR/direction)

while true
do
# check if Timer is enabled 
if [ $(cat /data/log/Timer_enable) == "1" ] 
then
	# Get the current time's hours and minutes (ex. 1430 for 2:30pm)
	nowtime=$(date +%H%M)

	# Swap $ontime and $offtime to disable early and enable late
	if [ "$nowtime" -ge "$timer_ontime" ] 
	then
		if [ "$nowtime" -le "$timer_offtime" ] 
		then
			VMFB_logfile="/data/log/VMFB_$(date +%F).log"
			touch "$VMFB_logfile"
			echo "$(date +%F_%X)	TMR	+">> "$VMFB_logfile"
			echo "$(date +%F_%X)	MTR	+">> "$VMFB_logfile"
			# Set the sensor IR and motor pins to high
			echo "1">/sys/class/gpio/gpio$SIR/value
			echo "1">/sys/class/gpio/gpio$MTR/value
			# Update previous value files
			echo "1" >| /data/log/prev_valSIR
			echo "1" >| /data/log/prev_valMTR
			# prevent PBKA from working while sensors are on due to Timer trigger
			echo "1" >| /data/log/PBKA_hold
		fi
	fi
fi

# Trigger timer every timer_interval (seconds)
sleep $timer_interval

done
