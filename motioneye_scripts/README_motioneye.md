
Deposit Monitor=24 (input, PD, high trigger  interrupt)
Dispense Monitor=10 (input, PD, high trigger  interrupt)
Motor Control=11 (outut, init low, high to start)

PIR Monitor=27 (input, PD, high trigger)
Sensor IR Control=25 (outut, init low, high to enable)
Feed Level Monitor=23 (input, PD, high trigger)

VMFB_Sensors.sh - enables sensors for interval specified in seconds when the PIR is triggered, logs events for PIR an MT sensors

VMFB_Deposit-Dispense.py - starts motor when the deposit sensor is triggered, stops it when the dispense sensor is triggered, logs  events

VMFB_Timer.sh - overlay button to set conf file variable - on dispenses (enables sensors and starts motor, stops motor on dispense and disables sensors) and repeats based on minutes interval set in conf file, off stops this, logs  events

VMFB_PBKA.sh - overlay button to set conf file variable - on enables sensor for seconds specified in the conf file and repeats based on minutes interval set in conf file, off stops this, logs  events

monitor_1 - shows current state of PIR, Empty, Motor, number of times PIR, Deposit and Dispense are triggered since 00:00 of current day


