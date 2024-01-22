
Control and monitoring interface requires 6 GPIO pins - 2 outputs and 4 inputs
If using a comparator, that input needs pull-up, the rest pull down
If using op amp, all 4 inputs need pull down

Pins for Raspberry Pi Zero W

RPi Zero W GPIO pins
Deposit Monitor= 24 (pin 18) (input, *PU, high trigger  interrupt)
Dispense Monitor=10 (pin 19) (input, *PU, high trigger  interrupt)
Motor Control=11 (pin 23) (outut, init low, high to start)
PIR Monitor=27 (pin 13) (input, PD, high trigger)
Sensor IR Control=25 (pin 22) (outut, init low, high to enable)
Feed Level Monitor=23 (pin 16) (input, PD, high trigger)

* for Deposit and Dispense, if using a comparator enable pull-ups and consider that the signal will go from high to low when triggered, if using an op amp enable pull downs and consider the signal will go from low to high when triggered.

Configs

config.txt - config file where you add GPIO pin configurations for startup
userinit.sh - config file where you can disable HDMI (for power saving), start scripts and pause motion detection at startup

VMFB Scripts

VMFB_Sensors.sh - enables sensors when the PIR is triggered, logs events for PIR an MT sensors
VMFB_Deposit-Dispense.py - starts motor when the deposit sensor is triggered, stops it when the dispense sensor is triggered, logs  events
VMFB_Timeouts.sh - disables sensors X seconds after PIR or Timer is last triggered, shuts off motor X seconds after deposit is last triggered
VMFB_Timer.sh - dispenses (enables sensors and starts motor) and repeats based on minutes interval set in conf file
VMFB_PBKA.sh - enables sensor for seconds specified in the conf file and repeats based on minutes interval set in conf file, off stops this, logs  events

Motioneye Scripts
monitor_1 - shows current state of PIR, Empty, Motor, number of times PIR, Deposit and Dispense are triggered since 00:00 of current day
down_1 - overlay button to manually dispense a peanut
alarm_on_1 - overlay button to enable timer
alarm_off_1 - overlay button to disnable timer
light_on_1 - overlay button to enable power bank keep-alive
light_off_1 - overlay button to disnable power bank keep-alive


