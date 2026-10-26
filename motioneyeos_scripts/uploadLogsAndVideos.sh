mount -o remount,rw /
rclone copy /data/output/Camera1 vmfb_gdrive:/VMFB_2026-2027_Trial/Testing/Videos --include "*.mp4"
rclone copy /data/log vmfb_gdrive:/VMFB_2026-2027_Trial/Testing/Logs
