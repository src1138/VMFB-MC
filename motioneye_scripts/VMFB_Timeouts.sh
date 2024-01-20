#!/bin/bash

# controls timeouts for sensors, motor and PBKA

# sensor timeout in seconds
sensor_timeout=30
# motor timeout in seconds
motor_timeout=10

# Set up pins for Sensor IR and Motor
# Assign pins
PIR=27 
SIR=25
MTR=11

# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$PIR ||
  (echo $PIR > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$PIR/direction)
test -e /sys/class/gpio/gpio$SIR ||
  (echo $SIR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$SIR/direction)
test -e /sys/class/gpio/gpio$MTR ||
  (echo $MTR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MTR/direction)

while true
do

# timestamp and logfile for log entries
dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"

# get current datetime in epoch seconds
now=$(date +"%s")

# Sensors
valPIR=$(cat /sys/class/gpio/gpio$PIR/value)
valSIR=$(cat /sys/class/gpio/gpio$SIR/value)
# check that sensors are on
if [ "$valSIR" == "1" ]; then
	# check that PIR is not triggering 
	if [ "$valPIR" == "0" ]; then
		# if no PIR in today's log 
		if [ $(grep 'PIR\|TIMER' $VMFB_logfile  | grep "+")=="" ] then
			# turn sensors off
			echo "0" >| /sys/class/gpio/gpio$SIR/value
			# update previous value file
			echo "0" >| /data/log/prev_valSIR
			# log sensor timeout event
			echo "$dtStamp	SIR	TO">> "$VMFB_logfile"
			# enable PBKA to work while sensors off due to sensor timeout
			echo "0" >| /data/log/PBKA_hold
		else 
		# parse log for last PIR or Timer trigger and get datetime
		lastSensor_event_datetimestring=$(grep 'PIR\|TMR' $VMFB_logfile | grep "+" | tail -1 | awk '{print $1}')
		lastSensor_datetime=$(date --date=$lastSensor_event_datetimestring +"%s")
		# subtract last PIR or Timer trigger datetime from now
		if [ $now-$lastSensor_datetime>=$sensor_timeout ] then
			# if result is >= sensor_timeout, turn sensors off
			echo "0" >| /sys/class/gpio/gpio$SIR/value
			# update previous value file
			echo "0" >| /data/log/prev_valSIR
			# log sensor timeout event
			echo "$dtStamp	SIR	TO">> "$VMFB_logfile"
			# enable PBKA to work while sensors off due to sensor timeout
			echo "0" >| /data/log/PBKA_hold
		fi
	fi
fi

# Motor
valMTR=$(cat /sys/class/gpio/gpio$MTR/value)
# check that motor is on
if [ "$valMTR" == "1" ]; then
	# if there is not a log entry for Deposit or Timer in today's log
		# turn motor off
		echo "0" >| /sys/class/gpio/gpio$MTR/value
		# update previous value file
		echo "0" >| /data/log/prev_valMTR
		# log motor timeout event
		echo "$dtStamp	MTR	TO">> "$VMFB_logfile"
	# else
		# parse log for last Deposit or Timer trigger and get datetime
		lastMTR_event_datetimestring=$(grep 'Deposit\|Timer' $VMFB_logfile | tail -1 | awk '{print $1}')
		lastMTR_datetime=$(date --date=$lastMTR_event_datetimestring +"%s")
		# subtract last Deposit or Timer trigger datetime from now
		if [ $now-$lastMTR_datetime>=$motor_timeout ] then
			# if result is >= motor_timeout turn motor off
			echo "0" >| /sys/class/gpio/gpio$MTR/value
			# update previous value file
			echo "0" >| /data/log/prev_valMTR
			# log motor timeout event
			echo "$dtStamp	MTR	TO">> "$VMFB_logfile"
		fi
	fi
fi

sleep 1

done
