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

while true
do

# timestamp and logfile for log entries
dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"

# Sensors
valPIR=$(cat /sys/class/gpio/gpio$PIR/value)
valSIR=$(cat /sys/class/gpio/gpio$SIR/value)
# check that sensors are on
if [ "$valSIR" == "1" ]; then
	# check that PIR is not triggering 
	if [ "$valPIR" == "0" ]; then
		# parse log for last PIR trigger and get datetime
		# if no PIR in today's log 
			# turn sensors off
			echo "0" >| /sys/class/gpio/gpio$SIR/value
			# update previous value file
			echo "0" >| /data/log/prev_valSIR
			# log sensor timeout event
			echo "$dtStamp	SIR	TO">> "$VMFB_logfile"
		# else subtract last PIR trigger datetime from now (dtStamp)
			# if result is >= sensor_timeout, 
				# turn sensors off
				echo "0" >| /sys/class/gpio/gpio$SIR/value
				# update previous value file
				echo "0" >| /data/log/prev_valSIR
				# log sensor timeout event
				echo "$dtStamp	SIR	TO">> "$VMFB_logfile"
			fi
		fi
	fi
fi

# Motor
valMTR=$(cat /sys/class/gpio/gpio$MTR/value)
# check that motor is on
if [ "$valMTR" == "1" ]; then
	# parse log for last Deposit or timer trigger and get datetime
	# grep Deposit|Timer file | tail -1 | awk '{print $1}'
	# date --date=datetimestring +"%s"
	# if no deposit or timer trigger in today's log, turn motor off
	# else subtract last Deposit or timer trigger datetime from now
		# if result is >= motor_timeout, 
			# turn motor off
			echo "0" >| /sys/class/gpio/gpio$MTR/value
			# update previous value file
			echo "0" >| /data/log/prev_valMTR
			# log motor timeout event
			echo "$dtStamp	MTR	TO">> "$VMFB_logfile"
		fi
	fi
fi

#PBKA

# check that PBKA is enabled
if [ $(cat /data/log/PBKA_enable == 1) ] then

	# PBKA Interval

	# parse log for last PIR or Timer trigger event and get datetime
	lastPIR=
	# subtract last PIR or Timer trigger datetime from now+pbka_pulse_length
	# if result is >= sensor_timeout+pbka_interval, continue, else exit

		# PBKA Pulse

		# check that Sensors are off 
		if [ "$valSIR" == "0" ]; then
			# parse log for last PBKA pulse off event and get datetime - 
			# if no PBKA pulse event log for today
				#turn on sensors
				# log PBKA on event
				echo "$dtStamp	PBKA	+">> "$VMFB_logfile"
			# else subtract pbka_pulse_length from now
				# if result is >= pbka_interval, turn on sensors
				# log PBKA on event
				echo "$dtStamp	PBKA	+">> "$VMFB_logfile"
		else # sensors are on
			# parse log for last PBKA pulse on event and get datetime
			# if no PBKA pulse event log for today, turn off sensors
			# log PBKA off event
			echo "$dtStamp	PBKA	-">> "$VMFB_logfile"
			# else subtract last PBKA pulse event datetime from now
			# if result is >= pbka_pulse_length, turn off sensors
			# log PBKA off event
			echo "$dtStamp	PBKA	-">> "$VMFB_logfile"
		fi
	fi
fi

sleep 1

done
