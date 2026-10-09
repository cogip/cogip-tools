#!/bin/bash
# Target: beacon (ROBOT_ID=0) - server-beacon + dashboard + kiosk + AP (dnsmasq).
# Runs its own server, not the robot core. Sourced by customize-image.sh (chroot).
TARGET_PACKAGES="${KIOSK_PACKAGES} ntpsec dnsmasq iptables ifmetric"

enable_services() {
    systemctl enable ntpsec
    systemctl disable systemd-resolved 2>/dev/null || true
    systemctl enable dnsmasq
    systemctl enable cogip-server-beacon cogip-dashboard weston.service
    systemctl set-default graphical.target
    # IP forwarding + NAT (iptables restored by rc.local at boot); the eth0 /
    # dnsmasq IP_ADDRESS placeholder is filled by the provision step.
    chmod +x /etc/rc.local 2>/dev/null || true
    systemctl enable rc-local.service 2>/dev/null || true
}
