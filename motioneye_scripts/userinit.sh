# Turn off HDMI to save ~24mA
/usr/bin/tvservice -o >> /data/log/userinit.log
# Initialize GPIO
nohup /data/etc/VMFB_GPIO_Init.sh >> /data/log/userinit.log &
# Start the main program to read sensors and control motor and IR LEDs 
nohup /data/etc/VMFB-MC.py >> /data/log/userinit.log &
# Initialize PBKA and timed dispense state
nohup /data/etc/VMFB_PBKA-Timer_Init.sh >> /data/log/userinit.log &
# Pause motion detection on startup and stop any recording that may have started
curl http://localhost:7999/1/detection/pause >> /data/log/userinit.log
curl http://localhost:7999/1/action/eventend >> /data/log/userinit.log
