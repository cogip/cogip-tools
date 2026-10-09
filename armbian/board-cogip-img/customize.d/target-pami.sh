#!/bin/bash
# Target: pami / ninja (ROBOT_ID>=2) - headless, no kiosk. The ninja (id 2) has a
# camera: robotcam imports opencv (cv2), which links libGL.so.1, so libgl1 is
# needed even headless. Sourced by customize-image.sh (chroot).
TARGET_PACKAGES="systemd-timesyncd libgl1"
# Only the ninja (ROBOT_ID 2) has a camera, but the pami base is shared; robotcam
# (picamera2 -> libcamera) runs only where the provision enables it. The coherent
# libcamera pair is 0.7.1 from trixie-backports (the rpt 0.7.2 is uninstallable).
# Generic customize installs these with `-t trixie-backports` + bridges the venv.
TARGET_BACKPORTS_PACKAGES="python3-libcamera libcamera0.7 libcamera-ipa"

enable_services() {
    systemctl enable systemd-timesyncd
    enable_cogip_core
    systemctl set-default multi-user.target
}
