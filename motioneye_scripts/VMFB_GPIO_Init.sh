#!/bin/bash

# Set up GPIO pins
MAN=26 #RPi ZeroW Pin #37
TMR=13 #RPi ZeroW Pin #33
PBKA=19 #RPi ZeroW Pin #35
 
# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$MAN || 
  (echo $MAN > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MAN/direction)
test -e /sys/class/gpio/gpio$TMR ||
  (echo $TMR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$TMR/direction)
test -e /sys/class/gpio/gpio$PBKA ||
  (echo $PBKA > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$PBKA/direction)

