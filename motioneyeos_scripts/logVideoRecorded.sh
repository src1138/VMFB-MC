dtStamp=$(date +%F_%X)
VMFB_logfile="/data/log/VMFB_$(date +%F).log"
touch "$VMFB_logfile"
echo "$dtStamp	VID	SAVED	MP4">> "$VMFB_logfile"
if [ $(cat /etc/motioneye/dep_flag.txt) -eq 1 ]; then 
depfile=$(find /var/lib/motioneye/ -type f -exec ls -t {} + | grep -E '.mp4$' | head -n 1);
mv -T $depfile  "${depfile%%.*}"_DEP."${depfile##*.}"; 
echo "0" > /etc/motioneye/dep_flag.txt; fi
