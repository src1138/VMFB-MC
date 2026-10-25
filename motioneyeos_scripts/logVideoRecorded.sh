dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
DEP_flagfile="/data/etc/dep_flag.txt"
touch "$VMFB_logfile"
echo "$dtStamp	VID	SAVED	MP4">> "$VMFB_logfile"
touch "$DEP_flagfile"
if [ $(cat "$DEP_flagfile") == "1" ]; then 
depfile=$(find /data/output/ -type f -exec ls -t {} + | grep -E '.mp4$' | head -n 1);
mv -T $depfile  "${depfile%%.*}"_DEP."${depfile##*.}"; 
echo "0" > "$DEP_flagfile"; fi
