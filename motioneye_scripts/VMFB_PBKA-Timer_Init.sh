#!/bin/bash

# If you want the PBKA enabled on startup 
# (in case of reboot, etc.), uncomment the following five lines
# PBKA_E=20 #RPi ZeroW Pin #38
# test -e /sys/class/gpio/gpio$PBKA_E ||
#  (echo $PBKA_E > /sys/class/gpio/export \
#   && echo out > /sys/class/gpio/gpio$PBKA_E/direction)
# echo "1" >| /sys/class/gpio/gpio$PBKA_E/value

# If you want timed dispense enabled on startup 
# (in case of reboot, etc.), uncomment the following five lines
# TMR_E=16 #RPi ZeroW Pin #36
# test -e /sys/class/gpio/gpio$TMR_E ||
#  (echo $TMR_E > /sys/class/gpio/export \
#   && echo out > /sys/class/gpio/gpio$TMR_E/direction)
# echo "1" >| /sys/class/gpio/gpio$TMR_E/value