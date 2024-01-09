#!/bin/bash

# Set up input pins and check their values
# Assign pins
PIR=27 #13
SIR=25 #22
EMT=23 #16
 
# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$PIR ||
  (echo $PIR > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$PIR/direction)
test -e /sys/class/gpio/gpio$SIR || 
  (echo $SIR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$SIR/direction)
test -e /sys/class/gpio/gpio$EMT ||
  (echo $EMT > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$EMT/direction)

while true
do

# Get the values for the last script execution
prev_valPIR=$(cat /data/log/prev_valPIR)
prev_valSIR=$(cat /data/log/prev_valSIR)
prev_valEMT=$(cat /data/log/prev_valEMT)

# Get the current pin values
valPIR=$(cat /sys/class/gpio/gpio$PIR/value)
valSIR=$(cat /sys/class/gpio/gpio$SIR/value)
# Only get the EMT pin value if the sensors are on, else reuse the previous value
if [ "$valSIR" == "1" ]; then
    valEMT=$(cat /sys/class/gpio/gpio$EMT/value)
else
    valEMT=$prev_valEMT
fi

# Update the previous values to the current values
echo $valPIR >| /data/log/prev_valPIR
echo $valSIR >| /data/log/prev_valSIR
# Only update the EMT previous value if the sensors are on
if [ "$valSIR" == "1" ]; then
    echo $valEMT >| /data/log/prev_valEMT
fi

# Set the display text for the pin values 

if [ "$valPIR" == "0" ]; then
    PIR_text="-"
else
    PIR_text="+"
fi
 
if [ "$valSIR" == "0" ]; then
    SIR_text="-"
    if [ "$valSIR" != "$prev_valSIR" ]; then
        curl http://localhost:7999/1/action/eventend
    fi
else
    SIR_text="+"
    if [ "$valSIR" != "$prev_valSIR" ]; then
        curl  http://localhost:7999/1/detection/start
        curl http://localhost:7999/1/action/eventstart
        curl  http://localhost:7999/1/detection/pause
    fi
fi

if [ "$valEMT" == "0" ]; then
    EMT_text="-"
else
    EMT_text="+"
fi

# Log any values that changed since the last execution
dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"

if [ "$valPIR" != "$prev_valPIR" ]; then
    echo "$dtStamp	PIR	$valPIR	$PIR_text">> "$VMFB_logfile"
fi

if [ "$valSIR" != "$prev_valSIR" ]; then
    echo "$dtStamp	IR	$valSIR	$SIR_text">> "$VMFB_logfile"
fi

if [ "$valEMT" != "$prev_valEMT" ]; then
    if [ "$valSIR" == "0" ]; then
        echo "$dtStamp	EMT	$valEMT	$EMT_text">> "$VMFB_logfile"
    fi
fi

sleep 1

done
