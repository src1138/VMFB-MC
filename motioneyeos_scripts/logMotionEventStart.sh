dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
DEP_flagfile="/data/etc/dep_flag.txt"
touch "$VMFB_logfile"
echo "$dtStamp	MDE	START	ME">> "$VMFB_logfile"
touch "$DEP_flagfile"
echo "0" > "$DEP_flagfile"

