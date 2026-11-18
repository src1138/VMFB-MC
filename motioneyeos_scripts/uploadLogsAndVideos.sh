mount -o remount,rw /
rclone copy /data/output/Camera1 vmfb_gdrive:/<gdrive_video_path> --include "*.mp4"
rclone copy /data/log vmfb_gdrive:/<gdrive_log_path>
