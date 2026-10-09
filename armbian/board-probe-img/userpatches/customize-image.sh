#!/bin/bash
# Armbian customize-image.sh (runs in the image chroot during build).
# Phase 0: keep the image minimal. Root-only, auto password, no firstlogin
# wizard, and a first-boot service that writes the hardware report to the
# boot partition. A few small, on-topic probe tools are installed; nothing else.
set -euo pipefail

# Armbian does not lay the overlay into the rootfs itself; it mounts it at
# /tmp/overlay in this chroot. Copy it in (service units, networkd, probe).
cp -a /tmp/overlay/. / 2>/dev/null || true
chmod +x /usr/local/sbin/cogip-check-hw.sh /usr/local/sbin/cogip-rfkill-unblock.sh 2>/dev/null || true

# Armbian's default 10-dhcp.network matches Type=ether/wlan and, sorting before
# our 10-eth / 20-wlan0, is the first match networkd applies, shadowing them
# (first match wins). Drop it so our per-type configs govern.
rm -f /etc/systemd/network/10-dhcp.network

ROOT_PASSWORD="${COGIP_ROOT_PASSWORD:-cogip}"

# Small tools the probe uses (i2cdetect, gpiodetect/gpioinfo, candump). The
# probe still falls back to /sys when a tool is absent, but these make the
# report complete and they are tiny.
apt-get update
apt-get install -y --no-install-recommends i2c-tools gpiod can-utils
apt-get clean

# Root-only: set its password and skip Armbian's interactive firstlogin wizard
# (the wizard, which would also create a normal user, is gated by this file).
echo "root:${ROOT_PASSWORD}" | chpasswd
rm -f /root/.not_logged_in_yet

# SSH in as root with a password (minimal image, lab use).
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config || true
systemctl enable ssh || true

# Serial console, handy to watch the boot on any board.
systemctl enable serial-getty@ttyAMA0.service 2>/dev/null || true
systemctl enable serial-getty@ttyS0.service 2>/dev/null || true

# First-boot hardware report.
systemctl enable cogip-hw-report.service

# Optional Wi-Fi, enabled only if build.sh staged the config. A .link renames
# any wireless interface to wlan0 (board-agnostic), so the static template unit
# wpa_supplicant@wlan0 just works; networkd does DHCP (Type=wlan).
if [ -f /etc/wpa_supplicant/wpa_supplicant-wlan0.conf ]; then
    systemctl enable wpa_supplicant@wlan0.service || true
    # Minimal images leave WLAN soft-blocked by rfkill. A drop-in on the wpa
    # unit (ExecStartPre) clears it at the right moment; mask systemd-rfkill so
    # it cannot restore a blocked state.
    systemctl mask systemd-rfkill.service systemd-rfkill.socket || true
fi
