#!/bin/bash
# Build a COGIP image. Two phases (see lib/): a heavy per-TARGET BASE image built
# once under qemu (packages + cogip wheel + services), then a fast host-side
# PROVISION of the per-robot data (env/hostname/IP/keys) onto a copy of that base.
#
#   ./build.sh                 # BOARD=rpi4b ROBOT_ID=1 (robot)
#   ROBOT_ID=2 ./build.sh      # ninja   (reuses the pami base)
#   ROBOT_ID=3 ./build.sh      # pami
#   ROBOT_ID=0 ./build.sh      # beacon
#   BASE_REBUILD=1 ROBOT_ID=3 ./build.sh   # force a base rebuild
#   BOARD=rock-5b ./build.sh
#
# The base is rebuilt only when the app source changes; a different ROBOT_ID of
# the same TARGET just re-provisions (seconds). The provision needs sudo (loop-mount).
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)

BOARD="${BOARD:-rpi4b}"
BRANCH="${BRANCH:-legacy}"                  # rpi-6.12.y: downstream unicam (CSI camera via libcamera); 6.18/current ships the upstream unicam that the vc4 pipeline cannot drive
RELEASE="${RELEASE:-trixie}"
ROBOT_ID="${ROBOT_ID:-1}"                  # 0=beacon, 1=robot, 2=ninja, 3-9=pami
BEACON_IP="${BEACON_IP:-192.168.2.100}"    # base addr; ROBOT_ID adds to the last octet

source "${SCRIPT_DIR}/lib/derive.sh"
source "${SCRIPT_DIR}/lib/build-base.sh"
source "${SCRIPT_DIR}/lib/provision.sh"

cogip_derive   # -> TARGET CLASS CLASS_LC SUFFIX HOSTNAME IP_PREFIX IP_LAST COGIP_IP

ARMBIAN_BUILD_DIR="${ARMBIAN_BUILD_DIR:-${SCRIPT_DIR}/../../../armbian-build}"
ARMBIAN_REPO="https://github.com/armbian/build"
ARMBIAN_REF="${ARMBIAN_REF:-v26.08}"   # Armbian release branch (not main/trunk) for reproducibility
if [ ! -d "${ARMBIAN_BUILD_DIR}/.git" ]; then
    echo "Cloning armbian/build @ ${ARMBIAN_REF} into ${ARMBIAN_BUILD_DIR}"
    git clone --depth=1 --branch "${ARMBIAN_REF}" "${ARMBIAN_REPO}" "${ARMBIAN_BUILD_DIR}"
else
    cur=$(git -C "${ARMBIAN_BUILD_DIR}" describe --tags --exact-match 2>/dev/null \
          || git -C "${ARMBIAN_BUILD_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
    if [ "${cur}" != "${ARMBIAN_REF}" ]; then
        echo "Switching armbian/build ${cur:-?} -> ${ARMBIAN_REF}"
        git -C "${ARMBIAN_BUILD_DIR}" fetch --depth 1 origin "${ARMBIAN_REF}"
        # -B lands on a local ref named ARMBIAN_REF (works for a tag or a branch)
        # so the check above is stable on the next run instead of detached HEAD.
        git -C "${ARMBIAN_BUILD_DIR}" checkout -qB "${ARMBIAN_REF}" FETCH_HEAD
    fi
fi

UP="${ARMBIAN_BUILD_DIR}/userpatches"
IMAGES_DIR="${ARMBIAN_BUILD_DIR}/output/images"
REPO_ROOT=$(cd "${SCRIPT_DIR}/../.." && pwd)
mkdir -p "${UP}" "${IMAGES_DIR}"

echo "Target: ROBOT_ID=${ROBOT_ID} TARGET=${TARGET} CLASS=${CLASS} HOSTNAME=${HOSTNAME} IP=${COGIP_IP}"
cogip_ensure_base   # -> BASE_IMG
cogip_provision         # -> IMG

echo
echo "Done. Image: ${IMG}"
