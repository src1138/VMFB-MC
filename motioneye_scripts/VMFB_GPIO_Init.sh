#!/bin/bash

# Set up GPIO pins
# Assign pins
PIR=27 #RPi ZeroW Pin #13
SIR=25 #RPi ZeroW Pin #22
EMT=23 #RPi ZeroW Pin #16
MTR=11 #RPi ZeroW Pin #23
 
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
test -e /sys/class/gpio/gpio$MTR ||
  (echo $MTR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MTR/direction)

# Make sure prev_* files exist
touch "/data/log/prev_valPIR"
touch "/data/log/prev_valSIR"
touch "/data/log/prev_valEMT"
