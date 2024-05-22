#!/bin/bash

# Set up GPIO pins
MAN_E=20 #RPi ZeroW Pin #38
TMR_E=12 #RPi ZeroW Pin #32
PBKA_E=16 #RPi ZeroW Pin #36
CAL_E=23 #RPi ZeroW Pin #16

# Verify they are set up, else initialize them
test -e /sys/class/gpio/gpio$MAN_E ||
  (echo $MAN_E > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MAN_E/direction)
test -e /sys/class/gpio/gpio$TMR_E ||
  (echo $TMR_E > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$TMR_E/direction)
test -e /sys/class/gpio/gpio$PBKA_E ||
  (echo $PBKA_E > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$PBKA_E/direction)
test -e /sys/class/gpio/gpio$CAL_E ||
  (echo $CAL_E > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$CAL_E/direction)

# Try exporting the python outputs
SIR=18 # pin 12
MTR=4 #pin 7
MT_SIG=24 #pin 18

test -e /sys/class/gpio/gpio$SIR ||
  (echo $SIR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$SIR/direction)
test -e /sys/class/gpio/gpio$MTR ||
  (echo $MTR > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MTR/direction)
test -e /sys/class/gpio/gpio$MT_SIG ||
  (echo $MT_SIG > /sys/class/gpio/export \
   && echo out > /sys/class/gpio/gpio$MT_SIG/direction)

# Exporting the python inputs
PIR=27 	#pin 13
MT=17 	#pin 11
MAN=26 	#pin 37
PBKA=19 #pin 35
TMR=6 	#pin 31
DIS=15 	#pin 10
DEP=14 	#pin 8
CAL=22  #pin 15

test -e /sys/class/gpio/gpio$PIR ||
  (echo $PIR > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$PIR/direction)
test -e /sys/class/gpio/gpio$MT ||
  (echo $MT > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$MT/direction)
test -e /sys/class/gpio/gpio$MAN ||
  (echo $MAN > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$MAN/direction)
test -e /sys/class/gpio/gpio$PBKA ||
  (echo $PBKA > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$PBKA/direction)
test -e /sys/class/gpio/gpio$TMR ||
  (echo $TMR > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$TMR/direction)
test -e /sys/class/gpio/gpio$DIS ||
  (echo $DIS > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$DIS/direction)
test -e /sys/class/gpio/gpio$DEP ||
  (echo $DEP > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$DEP/direction)
test -e /sys/class/gpio/gpio$CAL ||
  (echo $CAL > /sys/class/gpio/export \
   && echo in > /sys/class/gpio/gpio$CAL/direction)
