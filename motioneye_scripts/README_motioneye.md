
Control: requires 6 GPIO pins - 2 outputs and 4 inputs
Power: 3 additional pins are used for +5V, +3V3 and GND.
Monioring and Configuration: 7 additional pins to allow for peanut level monitoring, enable/disable PBKA and timed dispense, and manual dispense

Pins for Raspberry Pi Zero W

RPi Zero W GPIO pins
Controlled by VMFB-MC.py
- Deposit Monitor= 24 (pin 18) Interrupt-driven input detecting when something is deposited
- Dispense Monitor=10 (pin 19) Interrupt-driven input detecting when something is dispensed 
- Motor Control=11 (pin 23) Output turning dispense motor on or off
- PIR Monitor=27 (pin 13)  Interrupt-driven input detecting when the sensors should be turned on
- Sensor IR Control=25 (pin 22) Output turning sensors on or off
- Feed Level Monitor=23 (pin 16) Input detecting when the feed level is low
- Feed Level Indicator=5 (pin 29) Output indicating when the feed level is low
- Manual Dispense Input=26 (pin 37) Input detecting when a manual dispense is initiated
- Enable/Disable Timed Dispense Input=13 (pin 33) Input detecting if the Dispense Timer is enabed or not
- Enable/Disable PBKA Input=19 (pin 35) Input detecting if the PBKA is enabled or not
- 
Controlled by overlay buttons
- Manual Dispense Output=21 (pin 40) Output to trigger a manual dispense event
- Enable/Disable Timed Dispense Output=16 (pin 36) Output to toggle Timer enable/disable
- Enable/Disable PBKA Output=20 (pin 38) Output to toggle PBKA enable/disable

* for Deposit and Dispense, if using a comparator enable pull-ups and consider that the signal will go from high to low when triggered, if using an op amp enable pull downs and consider the signal will go from low to high when triggered.

config.txt goes in the /boot/ directory
all other scripts go in the /data/etc/ directory

Configs
- config.txt - config file where you add GPIO pin configurations to control state on startup, goes in the /boot/ directory
- userinit.sh - config file where you can disable HDMI (for power saving), start scripts and pause motion detection at startup, goes in the /data/etc/ directory

VMFB Scripts (go in the /data/etc/ directory)
- VMFB_GPIO_Init.sh - sets up GPIO used by overlay button scripts
- VMFB-MC.py - main program controlling the VMFB-MC

Motioneye Scripts (go in the /data/etc/ directory)
- monitor_1 - shows current state of PIR, Empty, Motor, Timed Dispense, PBKA, number of times PIR, Deposit and Dispense are triggered since 00:00 of current day
- down_1 - overlay button to manually dispense a peanut
- alarm_on_1 - overlay button to toggle timed dispense
- light_on_1 - overlay button to toggle power bank keep-alive


