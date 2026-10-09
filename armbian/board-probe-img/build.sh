#!/bin/bash
# Build a minimal Armbian feasibility image for ANY board, to probe what the
# stock vendor kernel offers (CAN/I2C/SPI/UART/camera/GPIO). Board-agnostic:
#
#   BOARD=rpi4b   ./build.sh
#   BOARD=rock-5b ./build.sh
#   BOARD=rock-5b BRANCH=vendor RELEASE=noble ./build.sh
#
# The image boots root-only (auto password), no firstlogin wizard, and writes
# the report to the boot partition (cogip-hw-report.txt) at first boot.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)

BOARD="${BOARD:-rpi4b}"           # override for other boards, e.g. BOARD=rock-5b ./build.sh
BRANCH="${BRANCH:-current}"       # vendor/stable Armbian kernel
RELEASE="${RELEASE:-trixie}"
CONFIG_NAME="cogip-board-probe-${BOARD}"

# armbian/build checkout, kept next to the cogip-tools repo by default.
ARMBIAN_BUILD_DIR="${ARMBIAN_BUILD_DIR:-${SCRIPT_DIR}/../../../armbian-build}"
ARMBIAN_REPO="https://github.com/armbian/build"
ARMBIAN_REF="${ARMBIAN_REF:-main}"

if [ ! -d "${ARMBIAN_BUILD_DIR}/.git" ]; then
    echo "Cloning armbian/build into ${ARMBIAN_BUILD_DIR}"
    git clone --depth=1 --branch "${ARMBIAN_REF}" "${ARMBIAN_REPO}" "${ARMBIAN_BUILD_DIR}"
fi

UP="${ARMBIAN_BUILD_DIR}/userpatches"
mkdir -p "${UP}/overlay/usr/local/sbin"

# Generated, minimal build config (authoritative source is this heredoc).
cat > "${UP}/config-${CONFIG_NAME}.conf" <<EOF
BOARD="${BOARD}"
BRANCH="${BRANCH}"
RELEASE="${RELEASE}"
KERNEL_CONFIGURE="no"
BUILD_DESKTOP="no"
BUILD_MINIMAL="yes"
KERNEL_GIT="shallow"
COMPRESS_OUTPUTIMAGE="sha,img"
EOF

cp "${SCRIPT_DIR}/userpatches/customize-image.sh" "${UP}/customize-image.sh"
cp -r "${SCRIPT_DIR}/userpatches/overlay/." "${UP}/overlay/"
cp "${SCRIPT_DIR}/check-hw.sh" "${UP}/overlay/usr/local/sbin/cogip-check-hw.sh"
chmod +x "${UP}/customize-image.sh" "${UP}/overlay/usr/local/sbin/cogip-check-hw.sh"

# Optional Wi-Fi: drop a filled wpa_supplicant-wlan0.conf next to this script
# (gitignored, holds the passphrase) and it gets baked + enabled.
WPA="${SCRIPT_DIR}/wpa_supplicant.conf"
[ -f "${WPA}" ] || WPA="${SCRIPT_DIR}/wpa_supplicant-wlan0.conf"   # accept the old name too
if [ -f "${WPA}" ]; then
    mkdir -p "${UP}/overlay/etc/wpa_supplicant"
    # A .link renames any wireless iface to wlan0, so this is what the static
    # wpa_supplicant@wlan0 template reads, on every board.
    install -m 600 "${WPA}" "${UP}/overlay/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    echo "Wi-Fi staged (any wireless iface renamed to wlan0 at boot)."
else
    echo "No wpa_supplicant.conf: Ethernet-only (report still lands on the boot partition)."
fi

# Optional static IP for wlan0: drop a wlan0.network next to this script
# (gitignored, site-specific) and it replaces the default DHCP for wlan0.
WLAN_NET="${SCRIPT_DIR}/wlan0.network"
if [ -f "${WLAN_NET}" ]; then
    install -m 644 "${WLAN_NET}" "${UP}/overlay/etc/systemd/network/20-wlan0.network"
    echo "wlan0 static network staged."
fi

echo "Building ${CONFIG_NAME} (BOARD=${BOARD} BRANCH=${BRANCH} RELEASE=${RELEASE})..."
cd "${ARMBIAN_BUILD_DIR}"
./compile.sh "${CONFIG_NAME}"

IMAGES_DIR="${ARMBIAN_BUILD_DIR}/output/images"
OUTPUT_NAME="board-probe-img-${BOARD}"

# Rename Armbian's output to a stable name, then regenerate .sha and .bmap for
# it (Armbian's COMPRESS bmap token emits none for these minimal images, and a
# stale sha/bmap breaks the flash tools).
IMG=$(ls -t "${IMAGES_DIR}"/*.img 2>/dev/null | head -1 || true)
if [ -n "${IMG}" ]; then
    NEW="${IMAGES_DIR}/${OUTPUT_NAME}.img"
    if [ "${IMG}" != "${NEW}" ]; then
        rm -f "${NEW}" "${NEW}".*
        mv "${IMG}" "${NEW}"
        rm -f "${IMG}".sha "${IMG}".bmap
        IMG="${NEW}"
    fi
    ( cd "${IMAGES_DIR}" && sha256sum "$(basename "${IMG}")" > "${IMG}.sha" )
    command -v bmaptool >/dev/null 2>&1 && bmaptool create -o "${IMG}.bmap" "${IMG}"
fi

echo
echo "Done. Image: ${IMG}"
echo "Flash, boot. Pull the SD and read cogip-hw-report.txt from the boot partition."
