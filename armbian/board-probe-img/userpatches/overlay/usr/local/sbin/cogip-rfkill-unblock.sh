#!/bin/sh
# Clear the WLAN rfkill soft block. Minimal images leave the radio blocked;
# run from wpa_supplicant@wlan0's ExecStartPre, once the wlan0 device (and its
# rfkill node) exists. sysfs only, so no rfkill package is needed.
for r in /sys/class/rfkill/*; do
    [ "$(cat "$r/type" 2>/dev/null)" = wlan ] && echo 0 > "$r/soft"
done
exit 0
