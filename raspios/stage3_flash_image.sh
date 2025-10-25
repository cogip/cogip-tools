#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
source ${SCRIPT_DIR}/common.sh

# Variables depending on robot id
case ${ROBOT_ID} in
    0) # Beacon
        DOCKER_TAG=beacon
        HOSTNAME=beacon
        ;;
    1) # Robot
        DOCKER_TAG=robot
        HOSTNAME=robot${ROBOT_ID}
        ;;
    [2-9]) # PAMIs
        DOCKER_TAG=pami
        HOSTNAME=robot${ROBOT_ID}
        ;;
esac

WORKING_DIR=${SCRIPT_DIR}/work
RASPIOS_COGIP_IMG="${WORKING_DIR}/raspios-arm64-${HOSTNAME}.img"
if [ ! -d "${WORKING_DIR}" ] ; then
    echo "Error: ${WORKING_DIR} not found"
    exit 1
fi
if [ ! -f "${RASPIOS_COGIP_IMG}" ] ; then
    echo "Error: ${RASPIOS_COGIP_IMG} not found"
    exit 1
fi

sudo umount ${SDCARD_DEV_BOOT} || true
sudo umount ${SDCARD_DEV_ROOTFS} || true
sudo dd if=${RASPIOS_COGIP_IMG} of=${SDCARD_DEV} bs=4M status=progress
sync
sudo umount ${SDCARD_DEV_BOOT} || true
sudo umount ${SDCARD_DEV_ROOTFS} || true
sudo parted ${SDCARD_DEV} --script "resizepart 2 -1"
sudo e2fsck -f ${SDCARD_DEV_ROOTFS}
sudo resize2fs ${SDCARD_DEV_ROOTFS}
