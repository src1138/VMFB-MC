#!/bin/bash

# Set up GPIO pins
MAN=21 #RPi ZeroW Pin #40
TMR=16 #RPi ZeroW Pin #36
PBKA=20 #RPi ZeroW Pin #38
 
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

