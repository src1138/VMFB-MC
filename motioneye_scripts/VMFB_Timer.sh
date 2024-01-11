#!/bin/bash

# check if Timer is enabled (Timer_enable=$(cat /data/log/Timer_enable == 1) else exit

# Assign pins
SIRCON=25
MTRCON=11

# timer interval between dispenses in seconods
timer_interval=5400 #90 mins
# time of day for timer to start
timer_ontime="0600" #6:00am
# time of day for timer to stop
timer_offtime="1800" #6:00pm


# Assumes you want to enable the camera early and disable it late
# To do the opposite, you can swap the $ontime and $offtime variables below

# Set the time you want to enable and disable the camera
ontime="0600" #6:00am
offtime="1800" #6:00pm

# Set pins 11 and 25 to be outputs driving low to avoid them going high on start up.
# Add the following line to your /boot/config.txt
# gpio=11,25=op,dl
 
# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$SIRCON ||
  (echo $SIRCON > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$SIRCON/direction)
test -e /sys/class/gpio/gpio$MTRCON ||
  (echo $MTRCON > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MTRCON/direction)

while true
do
# check if Timer is enabled (Timer_enable=$(cat /data/log/PBKA_enable == 1) else exit

# Get the current time's hours and minutes (ex. 1430 for 2:30pm)
nowtime=$(date +%H%M)

# Get the target on/off state
targetState="0"
# Swap $ontime and $offtime to disable early and enable late
if [[ "$nowtime" > "$ontime" ]]; then
    if [[ "$nowtime" < "$offtime" ]]; then
        targetState="1"
    fi
fi

if [ "$targetState"=="1" ]; then
	VMFB_logfile="/data/log/VMFB_$(date +%F).log"
	touch "$VMFB_logfile"
	echo "$(date +%F_%X)	TMR	START">> "$VMFB_logfile"
	# Set the sensor IR and motor pins to high
	echo "1">/sys/class/gpio/gpio$SIRCON/value
	echo "1">/sys/class/gpio/gpio$MTRCON/value
fi

# Trigger timer every timer_interval
sleep timer_interval

done
