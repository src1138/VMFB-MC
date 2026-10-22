# Turn off HDMI to save ~24mA, leave on for easier debugging when network fails
#wlr-randr --output HDMI-A-1 --off

# Start the main program to read sensors and control motor and IR LEDs 
nohup /usr/local/bin/VMFB-MC.py >> /var/log/vmfb/vmfbinit.log &

# Pause motion detection on startup and stop any recording that may have started
curl http://localhost:7999/1/detection/pause >> /var/log/vmfb/vmfbinit.log
curl http://localhost:7999/1/action/eventend >> /var/log/vmfb/vmfbinit.log
