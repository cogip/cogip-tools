#!/bin/bash
# Board-agnostic hardware/kernel feasibility probe. Uses only base userspace +
# /sys (no i2c-tools/gpiod/can-utils), so it runs on a minimal image untouched.
# Audits CAN / I2C / SPI / UART / camera / GPIO. Writes a report to $1 (or stdout).
set -uo pipefail

OUT="${1:-/dev/stdout}"
exec > "${OUT}" 2>&1

# Kernel config options worth knowing about, controller drivers included.
CFG='CONFIG_CAN|CONFIG_I2C|CONFIG_SPI|CONFIG_GPIO|CONFIG_PINCTRL|CONFIG_SERIAL_|CONFIG_VIDEO|MCP251|SLCAN|GS_USB|SPIDEV|I2C_CHARDEV'

section() { echo; echo "===== $1 ====="; }

section "system"
uname -a
for f in /etc/armbian-release /etc/os-release; do
    [ -r "$f" ] && { echo "--- $f ---"; grep -E 'BOARD|LINUXFAMILY|BRANCH|VERSION|PRETTY_NAME' "$f"; }
done

section "kernel config"
if [ -r /proc/config.gz ]; then
    zcat /proc/config.gz | grep -E "${CFG}" | sort
elif [ -r "/boot/config-$(uname -r)" ]; then
    grep -E "${CFG}" "/boot/config-$(uname -r)" | sort
else
    echo "no kernel config exposed (CONFIG_IKCONFIG off and no /boot/config-*)"
fi

section "loaded modules (peripherals)"
lsmod | grep -iE 'can|mcp25|slcan|gs_usb|spi|spidev|i2c|gpio|pinctrl|v4l|video|unicam' || echo "none matching"

section "modules available to load (modinfo)"
for m in can can_raw can_bcm mcp251x mcp251xfd slcan gs_usb vcan \
         i2c-dev spidev v4l2-common; do
    if modinfo "$m" >/dev/null 2>&1; then echo "available: $m"; else echo "MISSING : $m"; fi
done

section "boot config / device-tree overlays"
for f in /boot/armbianEnv.txt /boot/firmware/config.txt /boot/config.txt \
         /boot/extlinux/extlinux.conf /boot/boot.cmd; do
    [ -r "$f" ] && { echo "--- $f ---"; grep -vE '^\s*#|^\s*$' "$f"; }
done
echo "--- overlay dirs ---"
for d in /boot/firmware/overlays /boot/overlays /boot/dtb/*/overlay \
         /boot/dtb/overlays /boot/overlay-user; do
    [ -d "$d" ] && echo "present: $d ($(ls "$d" 2>/dev/null | wc -l) overlays)"
done

section "device nodes"
for pat in '/dev/i2c-*' '/dev/spidev*' '/dev/ttyAMA*' '/dev/ttyS*' \
           '/dev/ttyUSB*' '/dev/ttyACM*' '/dev/video*'; do
    # shellcheck disable=SC2086
    ls -ld $pat 2>/dev/null || echo "none: $pat"
done

section "I2C buses"
if command -v i2cdetect >/dev/null; then i2cdetect -l 2>/dev/null; fi
ls -1 /sys/class/i2c-dev/ 2>/dev/null || echo "no i2c-dev class (bus not enabled / i2c-dev not loaded)"

section "SPI (/sys)"
ls -1 /sys/class/spidev/ 2>/dev/null || echo "no spidev (SPI not enabled / spidev not loaded)"
ls -1 /sys/bus/spi/devices/ 2>/dev/null || true

section "CAN interfaces"
ip -details -brief link show type can 2>/dev/null || echo "no CAN netdev (expected until controller driver + DT are active)"

section "GPIO"
if command -v gpiodetect >/dev/null; then gpiodetect 2>/dev/null; fi
ls -1 /sys/bus/gpio/devices/ 2>/dev/null || echo "no gpio devices"
for c in /sys/class/gpio/gpiochip*; do
    [ -e "$c" ] && echo "$(basename "$c"): $(cat "$c/label" 2>/dev/null) ($(cat "$c/ngpio" 2>/dev/null) lines)"
done

section "DONE"
echo "Report: ${OUT}"
