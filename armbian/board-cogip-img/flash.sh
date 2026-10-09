#!/bin/bash
# Flash a built COGIP image to an SD card. Same ROBOT_ID scheme as build.sh.
#
#   ROBOT_ID=2 ./flash.sh /dev/sdb        # ninja (image board-cogip-img-pami2-<board>)
#   ROBOT_ID=0 ./flash.sh /dev/sdb        # beacon
#   BOARD=rock-5b ROBOT_ID=3 ./flash.sh /dev/sdb
#
# Destructive: the target device is wiped. It must be given explicitly; the
# script refuses the host's system disk and asks for confirmation before writing.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)

BOARD="${BOARD:-rpi4b}"
ROBOT_ID="${ROBOT_ID:-1}"
BEACON_IP="${BEACON_IP:-192.168.2.100}"
DEV="${1:-}"

[ -n "${DEV}" ] || { echo "usage: ROBOT_ID=<0-9> $0 /dev/sdX" >&2; exit 1; }

# Same ROBOT_ID -> suffix / hostname / IP mapping as build.sh (single source).
source "${SCRIPT_DIR}/lib/derive.sh"
cogip_derive

ARMBIAN_BUILD_DIR="${ARMBIAN_BUILD_DIR:-${SCRIPT_DIR}/../../../armbian-build}"
IMAGES_DIR="${ARMBIAN_BUILD_DIR}/output/images"
IMG="${IMAGES_DIR}/board-cogip-img-${SUFFIX}-${BOARD}.img"

[ -f "${IMG}" ] || { echo "Image not found: ${IMG} (build it first with ROBOT_ID=${ROBOT_ID} ./build.sh)" >&2; exit 1; }

# Device sanity: must be a whole block device, and NOT the host system disk.
[ -b "${DEV}" ] || { echo "${DEV} is not a block device" >&2; exit 1; }
if [ "$(lsblk -dno TYPE "${DEV}" 2>/dev/null)" != "disk" ]; then
    echo "${DEV} is not a whole disk (give the disk, e.g. /dev/sdb, not a partition)" >&2; exit 1
fi
ROOT_SRC=$(findmnt -no SOURCE / 2>/dev/null || true)
ROOT_DISK=$(lsblk -no PKNAME "${ROOT_SRC}" 2>/dev/null | head -1 || true)
if [ -n "${ROOT_DISK}" ] && [ "/dev/${ROOT_DISK}" = "${DEV}" ]; then
    echo "REFUSING: ${DEV} is the host system disk." >&2; exit 1
fi

# Verify the image checksum if present.
if [ -f "${IMG}.sha" ]; then
    echo "Verifying ${IMG##*/}.sha ..."
    ( cd "${IMAGES_DIR}" && sha256sum -c "$(basename "${IMG}").sha" )
fi

# Show the target and confirm (no silent write).
echo
echo "About to flash:"
echo "  image : ${IMG##*/}"
echo "  to    : ${DEV}"
lsblk -dno NAME,SIZE,MODEL,TRAN "${DEV}" 2>/dev/null | sed 's/^/          /'
echo "  robot : ROBOT_ID=${ROBOT_ID} hostname=${HOSTNAME} ip=${COGIP_IP}"
echo
printf 'This ERASES %s. Type "yes" to proceed: ' "${DEV}"
read -r ANS
[ "${ANS}" = "yes" ] || { echo "Aborted."; exit 1; }

# Unmount any mounted partitions of the target first.
for p in $(lsblk -lnpo NAME "${DEV}" | tail -n +2); do
    sudo umount "${p}" 2>/dev/null || true
done

# Flash: prefer bmaptool (fast, uses the .bmap), else dd.
if command -v bmaptool >/dev/null 2>&1 && [ -f "${IMG}.bmap" ]; then
    sudo bmaptool copy --bmap "${IMG}.bmap" "${IMG}" "${DEV}"
else
    echo "bmaptool/.bmap unavailable, falling back to dd ..."
    sudo dd if="${IMG}" of="${DEV}" bs=4M conv=fsync status=progress
fi
sync

echo
echo "Done. ${HOSTNAME} flashed to ${DEV}."
echo "First boot resizes the rootfs automatically; then:  ssh root@${COGIP_IP}"
