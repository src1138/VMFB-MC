# Turn off HDMI to save ~24mA
/usr/bin/tvservice -o >> /data/log/userinit.log
# Start deposit/dispense monitor/logger
nohup /data/etc/VMFB_deposit-dispense_monitor.py >> /data/log/userinit.log &
# Start logger for PIR, Sensor IR, Timer and Empty sensors
nohup /data/etc/VMFB_monitor-control.sh >> /data/log/userinit.log &
# Pause motion detection on startup
curl http://localhost:7999/1/detection/pause >> /data/log/userinit.log
