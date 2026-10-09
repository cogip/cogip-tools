#!/bin/bash
# Target: robot (full robot, ROBOT_ID=1) - graphical kiosk + camera.
# Sourced by customize-image.sh (chroot). Uses KIOSK_PACKAGES + enable_cogip_core
# from the generic customize-image.sh.
TARGET_PACKAGES="${KIOSK_PACKAGES} systemd-timesyncd"
# robotcam rpicam path = picamera2, which links libcamera. The Armbian/Debian
# candidate (rpt 0.7.2) is uninstallable (its libcamera0.7 0.7.2 is in no repo);
# the coherent pair lives in trixie-backports at 0.7.1. Installed with
# `-t trixie-backports` + bridged into the managed venv by the generic customize.
TARGET_BACKPORTS_PACKAGES="python3-libcamera libcamera0.7 libcamera-ipa"

enable_services() {
    systemctl enable systemd-timesyncd
    enable_cogip_core
    systemctl enable weston.service cogip-robotcam.service
    systemctl set-default graphical.target
}
