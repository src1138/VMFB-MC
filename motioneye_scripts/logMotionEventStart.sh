dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"
echo "$dtStamp	MDE	START	ME">> "$VMFB_logfile"
