#!/bin/bash

# controls the powerbank keep-alive which turns on the sensors for a moment when the VMFB is idle
# to enable the PBKA, /data/log/PBKA_enable should be set to "1"

# powerbank keep-alive interval in seconds
pbka_interval=10
# powerbank keep-alive pulse length in seconds
pbka_pulse_length=1

# Assign pins
SIR=25 #RPi ZeroW Pin #22

# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$SIR ||
  (echo $SIR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$SIR/direction)

while true
do

# timestamp and logfile for log entries
dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"

# check that PBKA is enabled
if [ $(cat /data/log/PBKA_enable) == "1") ] then
	# check that PBKA is not on hold
	if [ $(cat /data/log/PBKA_hold) == "0") ] then
		echo "1" >| /sys/class/gpio/gpio$SIR/value
		echo "$dtStamp	PBKA	+">> "$VMFB_logfile"
		sleep $pbka_pulse_length
	fi
	# check that PBKA is not on hold after the pulse and turn the sensors off
	if [ $(cat /data/log/PBKA_hold) == 0) ] then
		echo "0" >| /sys/class/gpio/gpio$SIR/value
		echo "$dtStamp	PBKA	-">> "$VMFB_logfile"
	fi
fi

# Trigger PBKA every pbka_interval (seconds)
sleep $pbka_interval

done
