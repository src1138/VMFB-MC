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
# Assign pins
PIR=27 
SIRC=25
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

# Sensors
valPIR=$(cat /sys/class/gpio/gpio$PIR/value)
valSIR=$(cat /sys/class/gpio/gpio$SIR/value)
# check that sensors are on
if [ "$valSIR" == "1" ]; then
	# check that PIR is not triggering 
	if [ "$valPIR" == "0" ]; then
		# parse log for last PIR trigger and get datetime
		# subtract last PIR trigger datetime from now
		# if result is >= sensor_timeout, 
			# turn sensors off
			echo "0" >| /sys/class/gpio/gpio$SIR/value
			# update previous value file
			echo "0" >| /data/log/prev_valSIR
			# log sensor timeout event
	fi
fi

# Motor
valMTR=$(cat /sys/class/gpio/gpio$MTR/value)
# check that motor is on
if [ "$valMTR" == "1" ]; then
	# parse log for last Deposit trigger and get datetime
	# subtract last Deposit trigger datetime from now
	# if result is >= motor_timeout, 
		# turn motor off
		echo "0" >| /sys/class/gpio/gpio$MTR/value
		# update previous value file
		echo "0" >| /data/log/prev_valMTR
		# log motor timeout event
fi

#PBKA

# check that PBKA is enabled
if [ $(cat /data/log/PBKA_enable == 1) ] then

	# PBKA Interval

	# parse log for last PIR trigger event and get datetime
	# subtract last PIR trigger datetime from now+pbka_pulse_length
	# if result is >= sensor_timeout+pbka_interval, continue, else exit

		# PBKA Pulse

		# check that Sensors are off 
		if [ "$valSIR" == "0" ]; then
			# parse log for last PBKA pulse off event and get datetime - 
			# if no PBKA pulse event log for today
				#turn on sensors
				# update previous value file
				# log PBKA on event
			# else subtract pbka_pulse_length from now
				# if result is >= pbka_interval, turn on sensors
				# update previous value file
				# log PBKA on event
		else # sensors are on
			# parse log for last PBKA pulse on event and get datetime
			# if no PBKA pulse event log for today, turn off sensors
			# update previous value file
			# log PBKA off event
			# else subtract last PBKA pulse event datetime from now
			# if result is >= pbka_pulse_length, turn off sensors
			# update previous value file
			# log PBKA off event
		fi
	fi
fi

# sleep 1 sec
