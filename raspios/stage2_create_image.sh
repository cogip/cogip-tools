#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
source ${SCRIPT_DIR}/common.sh

# Variables depending on robot id
## Beacon vs robots
case ${ROBOT_ID} in
    0) # Beacon
        DOCKER_TAG=beacon
        HOSTNAME=beacon
        GATEWAY=${PUBLIC_GATEWAY}
        IP_ADDRESS_WLAN0=${IP_ADDRESS_BEACON_WLAN0}
        IP_ADDRESS_ETH0=${IP_ADDRESS_BEACON_ETH0}
        WLAN_SSID=${PUBLIC_WLAN_SSID}
        WLAN_PSK=${PUBLIC_WLAN_PSK}
        VC4_V3D_DRIVER=${BEACON_VC4_V3D_DRIVER}
        SCREEN_WIDTH=${BEACON_SCREEN_WIDTH}
        SCREEN_HEIGHT=${BEACON_SCREEN_HEIGHT}
        ;;
    *) # Robots common
        HOSTNAME=robot${ROBOT_ID}
        GATEWAY=${IP_ADDRESS_BEACON_ETH0}
        IP_ADDRESS_WLAN0_VAR=IP_ADDRESS_ROBOT${ROBOT_ID}_WLAN0
        IP_ADDRESS_ETH0_VAR=IP_ADDRESS_ROBOT${ROBOT_ID}_ETH0
        IP_ADDRESS_WLAN0=${!IP_ADDRESS_WLAN0_VAR}
        IP_ADDRESS_ETH0=${!IP_ADDRESS_ETH0_VAR}
        WLAN_SSID=${BEACON_WLAN_SSID}
        WLAN_PSK=${BEACON_WLAN_PSK}
        VC4_V3D_DRIVER=${ROBOT_VC4_V3D_DRIVER}
        SCREEN_WIDTH=${ROBOT_SCREEN_WIDTH}
        SCREEN_HEIGHT=${ROBOT_SCREEN_HEIGHT}
esac

## Robot vs PAMIs
case ${ROBOT_ID} in
    1) # Robot
        DOCKER_TAG=robot
        ROBOT_WIDTH=${ROBOT_WIDTH}
        ROBOT_LENGTH=${ROBOT_LENGTH}
        DETECTOR_LIDAR_PORT=${ROBOT_DETECTOR_LIDAR_PORT}
        DETECTOR_MIN_DISTANCE=${ROBOT_DETECTOR_MIN_DISTANCE}
        DETECTOR_MAX_DISTANCE=${ROBOT_DETECTOR_MAX_DISTANCE}
        DETECTOR_MIN_INTENSITY=${ROBOT_DETECTOR_MIN_INTENSITY}
        DETECTOR_REFRESH_INTERVAL=${ROBOT_DETECTOR_REFRESH_INTERVAL}
        DETECTOR_SENSOR_DELAY=${ROBOT_DETECTOR_SENSOR_DELAY}
        DETECTOR_CLUSTER_MIN_SAMPLES=${ROBOT_DETECTOR_CLUSTER_MIN_SAMPLES}
        DETECTOR_CLUSTER_EPS=${ROBOT_DETECTOR_CLUSTER_EPS}
        PLANNER_OBSTACLE_BB_MARGIN=${ROBOT_PLANNER_OBSTACLE_BB_MARGIN}
        ;;
    [2-9]) # PAMIs
        DOCKER_TAG=robot
        ROBOT_WIDTH=${PAMI_WIDTH}
        ROBOT_LENGTH=${PAMI_LENGTH}
        DETECTOR_LIDAR_PORT=${PAMI_DETECTOR_LIDAR_PORT}
        DETECTOR_MIN_DISTANCE=${PAMI_DETECTOR_MIN_DISTANCE}
        DETECTOR_MAX_DISTANCE=${PAMI_DETECTOR_MAX_DISTANCE}
        DETECTOR_MIN_INTENSITY=${PAMI_DETECTOR_MIN_INTENSITY}
        DETECTOR_REFRESH_INTERVAL=${PAMI_DETECTOR_REFRESH_INTERVAL}
        DETECTOR_SENSOR_DELAY=${PAMI_DETECTOR_SENSOR_DELAY}
        DETECTOR_CLUSTER_MIN_SAMPLES=${PAMI_DETECTOR_CLUSTER_MIN_SAMPLES}
        DETECTOR_CLUSTER_EPS=${PAMI_DETECTOR_CLUSTER_EPS}
        PLANNER_OBSTACLE_BB_MARGIN=${PAMI_PLANNER_OBSTACLE_BB_MARGIN}
        ;;
esac

WORKING_DIR=${SCRIPT_DIR}/work
OVERLAY_ROOTFS=${SCRIPT_DIR}/overlay-rootfs
OVERLAY_KERNEL=${SCRIPT_DIR}/overlay-kernel
MOUNT_DIR=${WORKING_DIR}/mnt
RASPIOS_COGIP_IMG="${WORKING_DIR}/raspios-arm64-${HOSTNAME}.img"
ROOTFS=${WORKING_DIR}/rootfs-${HOSTNAME}.tar
RSYNC_FLAGS="-vh --progress --modify-window=1 --recursive --ignore-errors"

rm -rf ${RASPIOS_COGIP_IMG} ${ROOTFS}

# Extract rootfs
container=$(docker run -d cogip/raspios:${DOCKER_TAG} sleep infinity)
docker export -o ${ROOTFS} ${container}
docker rm -f ${container}

# Build custom image
ALIGN="$((4 * 1024 * 1024))"

BOOT_SIZE="$((256 * 1024 * 1024))"
ROOTFS_SIZE=$(du --apparent-size -s --block-size=1 ${ROOTFS} | cut -f 1)
ROOT_MARGIN="$(echo "($ROOTFS_SIZE * 0.2 + 200 * 1024 * 1024) / 1" | bc)"
BOOT_PART_START=$((ALIGN))
BOOT_PART_SIZE=$(((BOOT_SIZE + ALIGN - 1) / ALIGN * ALIGN))
ROOT_PART_START=$((BOOT_PART_START + BOOT_PART_SIZE))
ROOT_PART_SIZE=$(((ROOTFS_SIZE + ROOT_MARGIN + ALIGN  - 1) / ALIGN * ALIGN))
IMG_SIZE=$((BOOT_PART_START + BOOT_PART_SIZE + ROOT_PART_SIZE))

rm -rf ${RASPIOS_COGIP_IMG}
truncate -s ${IMG_SIZE} ${RASPIOS_COGIP_IMG}

parted --script "${RASPIOS_COGIP_IMG}" mklabel msdos
parted --script "${RASPIOS_COGIP_IMG}" unit B mkpart primary fat32 "${BOOT_PART_START}" "$((BOOT_PART_START + BOOT_PART_SIZE - 1))"
parted --script "${RASPIOS_COGIP_IMG}" unit B mkpart primary ext4 "${ROOT_PART_START}" "$((ROOT_PART_START + ROOT_PART_SIZE - 1))"

PARTED_OUT=$(parted -sm "${RASPIOS_COGIP_IMG}" unit b print)
BOOT_OFFSET=$(echo "$PARTED_OUT" | grep -e '^1:' | cut -d':' -f 2 | tr -d B)
BOOT_LENGTH=$(echo "$PARTED_OUT" | grep -e '^1:' | cut -d':' -f 4 | tr -d B)

ROOT_OFFSET=$(echo "$PARTED_OUT" | grep -e '^2:' | cut -d':' -f 2 | tr -d B)
ROOT_LENGTH=$(echo "$PARTED_OUT" | grep -e '^2:' | cut -d':' -f 4 | tr -d B)

BOOT_DEV=$(sudo losetup --show -f -o "${BOOT_OFFSET}" --sizelimit "${BOOT_LENGTH}" "${RASPIOS_COGIP_IMG}")
ROOT_DEV=$(sudo losetup --show -f -o "${ROOT_OFFSET}" --sizelimit "${ROOT_LENGTH}" "${RASPIOS_COGIP_IMG}")

ROOT_FEATURES="^huge_file"
for FEATURE in metadata_csum 64bit; do
    if grep -q "$FEATURE" /etc/mke2fs.conf; then
        ROOT_FEATURES="^$FEATURE,$ROOT_FEATURES"
    fi
done

sudo mkdosfs -n boot -F 32 -v "$BOOT_DEV"
sudo mkfs.ext4 -L rootfs -O "$ROOT_FEATURES" "$ROOT_DEV"

sudo mount -v "$ROOT_DEV" "${MOUNT_DIR}" -t ext4
sudo mkdir -p "${MOUNT_DIR}/boot/firmware"
sudo mount -v "$BOOT_DEV" "${MOUNT_DIR}/boot/firmware" -t vfat

sudo tar xf ${ROOTFS} -C ${MOUNT_DIR} --numeric-owner
if [ -d "${OVERLAY_KERNEL}" ] ; then
    sudo rsync ${RSYNC_FLAGS} ${OVERLAY_KERNEL}/ ${MOUNT_DIR}/
fi
sudo cp ${OVERLAY_ROOTFS}/etc/hostname ${MOUNT_DIR}/etc/hostname
sudo cp ${OVERLAY_ROOTFS}/etc/hosts ${MOUNT_DIR}/etc/hosts
sudo chmod 600 ${MOUNT_DIR}/etc/ssh/ssh_host_*
sudo chmod 644 ${MOUNT_DIR}/etc/ssh/ssh_host_*.pub
sudo chmod 600 ${MOUNT_DIR}/root/.ssh/id_rsa

# Fix boot and root devices
IMGID="$(dd if="${RASPIOS_COGIP_IMG}" skip=440 bs=1 count=4 2>/dev/null | xxd -e | cut -f 2 -d' ')"
sudo sed -i "s/ROOTDEV/PARTUUID=${IMGID}/" ${MOUNT_DIR}/etc/fstab
sudo sed -i "s/ROOTDEV/PARTUUID=${IMGID}/" ${MOUNT_DIR}/boot/firmware/cmdline.txt

# Apply custom parameters

sudo sed -i "s/IP_ADDRESS/${IP_ADDRESS_WLAN0}/" ${MOUNT_DIR}/etc/systemd/network/00-wlan0.network
sudo sed -i "s/IP_ADDRESS/${IP_ADDRESS_ETH0}/" ${MOUNT_DIR}/etc/systemd/network/00-eth0.network
sudo sed -i "s/GATEWAY/${GATEWAY}/" ${MOUNT_DIR}/etc/systemd/network/00-wlan0.network
sudo sed -i "s/GATEWAY/${GATEWAY}/" ${MOUNT_DIR}/etc/systemd/network/00-eth0.network
sudo sed -i "s/WLAN_SSID/${WLAN_SSID}/" ${MOUNT_DIR}/etc/wpa_supplicant/wpa_supplicant-wlan0.conf
sudo sed -i "s/WLAN_PSK/${WLAN_PSK}/" ${MOUNT_DIR}/etc/wpa_supplicant/wpa_supplicant-wlan0.conf
sudo sed -i "s/HOSTNAME/${HOSTNAME}/" ${MOUNT_DIR}/etc/hostname
sudo sed -i "s/HOSTNAME/${HOSTNAME}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/HOSTNAME/${HOSTNAME}/" ${MOUNT_DIR}/etc/ssh/sshd_config
sudo sed -i "s/IP_ADDRESS_BEACON/${IP_ADDRESS_BEACON_ETH0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/IP_ADDRESS_ROBOT1/${IP_ADDRESS_ROBOT1_WLAN0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/IP_ADDRESS_ROBOT2/${IP_ADDRESS_ROBOT2_WLAN0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/IP_ADDRESS_ROBOT3/${IP_ADDRESS_ROBOT3_WLAN0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/IP_ADDRESS_ROBOT4/${IP_ADDRESS_ROBOT4_WLAN0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/IP_ADDRESS_ROBOT5/${IP_ADDRESS_ROBOT5_WLAN0}/" ${MOUNT_DIR}/etc/hosts
sudo sed -i "s/ROBOT_ID/${ROBOT_ID}/" ${MOUNT_DIR}/root/start_chromium.sh
sudo sed -i "s/VC4_V3D_DRIVER/${VC4_V3D_DRIVER}/" ${MOUNT_DIR}/boot/firmware/config.txt
sudo sed -i "s/SCREEN_WIDTH/${SCREEN_WIDTH}/" ${MOUNT_DIR}/boot/firmware/config.txt
sudo sed -i "s/SCREEN_HEIGHT/${SCREEN_HEIGHT}/" ${MOUNT_DIR}/boot/firmware/config.txt
sudo sed -i "s/ROBOT_ID/${ROBOT_ID}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/HOSTNAME/${HOSTNAME}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_ROBOT_WIDTH/${ROBOT_WIDTH}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_ROBOT_LENGTH/${ROBOT_LENGTH}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s|CUSTOM_DETECTOR_LIDAR_PORT|${DETECTOR_LIDAR_PORT}|" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_MIN_DISTANCE/${DETECTOR_MIN_DISTANCE}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_MAX_DISTANCE/${DETECTOR_MAX_DISTANCE}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_MIN_INTENSITY/${DETECTOR_MIN_INTENSITY}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_REFRESH_INTERVAL/${DETECTOR_REFRESH_INTERVAL}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_SENSOR_DELAY/${DETECTOR_SENSOR_DELAY}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_CLUSTER_MIN_SAMPLES/${DETECTOR_CLUSTER_MIN_SAMPLES}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_DETECTOR_CLUSTER_EPS/${DETECTOR_CLUSTER_EPS}/" ${MOUNT_DIR}/etc/environment
sudo sed -i "s/CUSTOM_PLANNER_OBSTACLE_BB_MARGIN/${PLANNER_OBSTACLE_BB_MARGIN}/" ${MOUNT_DIR}/etc/environment
sudo echo "ROBOT_ID=${ROBOT_ID}" | sudo tee -a ${MOUNT_DIR}/etc/environment 1> /dev/null
sudo chmod 600 ${MOUNT_DIR}/etc/sudoers.d/*
sudo chmod 600 ${MOUNT_DIR}/etc/wpa_supplicant/wpa_supplicant-wlan0.conf
sudo ln -sf /run/systemd/resolve/resolv.conf ${MOUNT_DIR}/etc/resolv.conf
sudo rm -f ${MOUNT_DIR}/.dockerenv
sudo rm -f ${MOUNT_DIR}/etc/sshd_config.d/rename_user.conf

if [[ "${ROBOT_ID}" -gt 0 && "${PROFILE}" == "cup" ]]; then
    sudo mv -f "${MOUNT_DIR}/etc/systemd/timesyncd-cup.conf" "${MOUNT_DIR}/etc/systemd/timesyncd.conf"
fi

case ${ROBOT_ID} in
    0) # Beacon
        sudo sed -i "s/IP_ADDRESS/${IP_ADDRESS_ETH0}/" ${MOUNT_DIR}/etc/dnsmasq.conf
        ;;
    1) # Robot
        sudo sed -i "s/# PLANNER_STARTER_PIN=/PLANNER_STARTER_PIN=${ROBOT_STARTER_PIN}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s|# PLANNER_SCSERVOS_PORT=|PLANNER_SCSERVOS_PORT=${ROBOT_SCSERVOS_PORT}|" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_SCSERVOS_BAUD_RATE=/PLANNER_SCSERVOS_BAUD_RATE=${ROBOT_SCSERVOS_BAUD_RATE}/" ${MOUNT_DIR}/etc/environment
        ;;
    [2-9]) # PAMIs
        sudo sed -i "s/# PLANNER_LED_RED_PIN=/PLANNER_LED_RED_PIN=${PAMI_LED_RED_PIN}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_LED_GREEN_PIN=/PLANNER_LED_GREEN_PIN=${PAMI_LED_GREEN_PIN}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_LED_BLUE_PIN=/PLANNER_LED_BLUE_PIN=${PAMI_LED_BLUE_PIN}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_FLAG_MOTOR_PIN=/PLANNER_FLAG_MOTOR_PIN=${PAMI_FLAG_MOTOR_PIN}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_OLED_BUS=/PLANNER_OLED_BUS=${PAMI_OLED_BUS}/" ${MOUNT_DIR}/etc/environment
        sudo sed -i "s/# PLANNER_OLED_ADDRESS=/PLANNER_OLED_ADDRESS=${PAMI_OLED_ADDRESS}/" ${MOUNT_DIR}/etc/environment
        sudo rm -f ${MOUNT_DIR}/root/.bash_profile
        ;;
esac

sudo umount ${MOUNT_DIR}/boot/firmware
sudo umount ${MOUNT_DIR}
sudo zerofree "${ROOT_DEV}"
sync
sudo losetup -d ${BOOT_DEV}
sudo losetup -d ${ROOT_DEV}
