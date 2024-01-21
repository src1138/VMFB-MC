# Turn off HDMI to save ~24mA
/usr/bin/tvservice -o >> /data/log/userinit.log
# Start deposit/dispense 
nohup /data/etc/VMFB_Deposit-Dispense.py >> /data/log/userinit.log &
# Start PIR, Sensor IR and Empty sensors
nohup /data/etc/VMFB_Sensors.sh >> /data/log/userinit.log &
# Start Sensor IR and Motor timeout
nohup /data/etc/VMFB_Timeouts.sh >> /data/log/userinit.log &
# Start dispense timer
nohup /data/etc/VMFB_Timer.sh >> /data/log/userinit.log &
# Start PBKA 
nohup /data/etc/VMFB_PBKA.sh >> /data/log/userinit.log &
# Pause motion detection on startup
curl http://localhost:7999/1/detection/pause >> /data/log/userinit.log
