#!/bin/bash
# Raspberry Pi board specifics, all in one place. Armbian builds a single rpi4b
# image that boots both the Pi4 robots and the Pi5 beacon (Armbian merged Pi5
# into the rpi4b config; the RPi multi-board kernel + firmware pick the right
# DTB), so the hook picks a config.txt fragment by COGIP_TARGET (the actual lines
# live in overlay data files usr/local/lib/cogip-config/<role>.txt). Used in TWO
# contexts:
#  - appended to the Armbian build config by build.sh: registers the config.txt
#    hook below, and reads COGIP_TARGET (also written into that config);
#  - sourced by customize-image.sh in the chroot: provides the variables (the
#    hook function is only defined there, never called).

# --- customize-image.sh variables ---
CONSOLE_TTY="ttyAMA0"                                    # PL011 GPIO14/15, freed by disable-bt
BOARD_MASK_UNITS="rpi-eeprom-update.service rpi-resize.service"
BOARD_GPIO_SWD=1                                         # openocd rpi-cogip.cfg = Pi bcm2835gpio bitbang

# --- Armbian hook: COGIP peripheral overlays in config.txt ---
# Runs at pre_umount_final_image, AFTER the bcm2711 family writes config.txt with
# '>' (pre_umount_final_image__write_raspi_config); the zzz_ suffix sorts last.
function pre_umount_final_image__zzz_cogip_peripherals() {
    local cfg="${MOUNT}/boot/firmware/config.txt"
    [[ -f "${cfg}" ]] || { display_alert "COGIP: no config.txt to patch" "${cfg}" "wrn"; return 0; }
    # The bcm2711 family already wrote camera_auto_detect=1; drop it so whatever the
    # fragment below sets is the only one (last-wins is unreliable here).
    sed -i '/^camera_auto_detect=/d' "${cfg}"

    # The peripheral lines live in data files staged by the overlay (this script
    # keeps the logic, the .txt files the config.txt content). beacon = Pi5,
    # everything else = Pi4 robot/pami. The staging dir is removed at the end so it
    # does not ship in the image.
    local role="robot"; [[ "${COGIP_TARGET:-robot}" == "beacon" ]] && role="beacon"
    local frag="${MOUNT}/usr/local/lib/cogip-config/${role}.txt"
    if [[ -f "${frag}" ]]; then
        display_alert "COGIP: ${role} config.txt" "rpi4b" "info"
        printf '\n' >> "${cfg}"; cat "${frag}" >> "${cfg}"
    else
        display_alert "COGIP: missing config.txt fragment" "${frag}" "wrn"
    fi

    # openocd GPIO-SWD (bcm2835gpio) mmaps /dev/mem, which Armbian's kernel blocks
    # ("mmap: Operation not permitted"); iomem=relaxed on the cmdline lifts the
    # STRICT_DEVMEM restriction so the bitbang adapter can init. Pi4-only.
    if [[ "${role}" == "robot" ]]; then
        local cmd="${MOUNT}/boot/firmware/cmdline.txt"
        if [[ -f "${cmd}" ]] && ! grep -q 'iomem=relaxed' "${cmd}"; then
            sed -i 's/[[:space:]]*$/ iomem=relaxed/' "${cmd}"
            display_alert "COGIP: added iomem=relaxed to cmdline" "rpi4b" "info"
        fi
    fi

    rm -rf "${MOUNT}/usr/local/lib/cogip-config"
}

# --- Armbian hook: build the downstream (legacy) unicam instead of upstream ---
# Armbian enables VIDEO_BCM2835_UNICAM (the mainline/upstream unicam: of-match
# brcm,bcm2835-unicam-upstream, two video nodes + subdev, MC-only) which the
# libcamera vc4 pipeline cannot acquire ("Unable to acquire a Unicam instance",
# -22), so the CSI camera never comes up. The downstream VIDEO_BCM2835_UNICAM_LEGACY
# matches the csi node's brcm,bcm2835-unicam compatible and is what raspios +
# libcamera's vc4 pipeline use. The two share the bcm2835-unicam module name, so
# they are mutually exclusive: disable upstream, enable legacy.
function custom_kernel_config__cogip_unicam_legacy() {
    # This hook runs twice; the version-calc pass has no .config (nor ./scripts/config,
    # which kernel_config_set_* needs). Record the change for kernel-config hashing in
    # both passes, then apply it only when the .config is in place.
    kernel_config_modifying_hashes+=("cogip_unicam_legacy=UNICAM:n,UNICAM_LEGACY:m")
    [[ -f .config ]] || return 0
    kernel_config_set_n CONFIG_VIDEO_BCM2835_UNICAM
    kernel_config_set_m CONFIG_VIDEO_BCM2835_UNICAM_LEGACY
}
