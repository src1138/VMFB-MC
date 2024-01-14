# Turn off HDMI to save ~24mA
/usr/bin/tvservice -o >> /data/log/userinit.log
# Start deposit/dispense monitor/logger
nohup /data/etc/VMFB_Deposit-Dispense.py >> /data/log/userinit.log &
# Start PIR, Sensor IR and Empty sensors monitor/logger
nohup /data/etc/VMFB_Sensors.sh >> /data/log/userinit.log &
# Start Sensor IR, Motor and PBKA timeout monitor/logger
nohup /data/etc/VMFB_Timeouts.sh >> /data/log/userinit.log &
# Start dispense timer monitor/logger
nohup /data/etc/VMFB_Timer.sh >> /data/log/userinit.log &
# Pause motion detection on startup
curl http://localhost:7999/1/detection/pause >> /data/log/userinit.log
