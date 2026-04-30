set -xe

sudo -v

# Load .env file if any
DOT_ENV_FILE=${SCRIPT_DIR}/.env
if [ -f ${DOT_ENV_FILE} ] ; then
    source ${DOT_ENV_FILE}
fi

# Check PROFILE variable
if [ -z "${PROFILE}" ] ; then
    echo "Error: Variable PROFILE not defined"
    exit 1
fi
if [ "${PROFILE}" != "cup" -a "${PROFILE}" != "dev" ]; then
    echo "Error: Variable PROFILE can only be set to 'cup' or 'dev'"
    exit 1
fi

source ${SCRIPT_DIR}/utils.sh
source ${SCRIPT_DIR}/config-common.env
source ${SCRIPT_DIR}/config-${PROFILE}.env

ROBOT_ID=$(get_robot_id $@)

# Check variables
check_vars RASPIOS_URL \
           IP_ADDRESS_BEACON_WLAN0 IP_ADDRESS_BEACON_ETH0 \
           IP_ADDRESS_ROBOT1_WLAN0 IP_ADDRESS_ROBOT1_ETH0 \
           IP_ADDRESS_ROBOT2_WLAN0 IP_ADDRESS_ROBOT2_ETH0 \
           IP_ADDRESS_ROBOT3_WLAN0 IP_ADDRESS_ROBOT3_ETH0 \
           IP_ADDRESS_ROBOT4_WLAN0 IP_ADDRESS_ROBOT4_ETH0 \
           IP_ADDRESS_ROBOT5_WLAN0 IP_ADDRESS_ROBOT5_ETH0 \
           IP_ADDRESS_ROBOT6_WLAN0 IP_ADDRESS_ROBOT6_ETH0 \
           PUBLIC_GATEWAY PUBLIC_WLAN_SSID PUBLIC_WLAN_PSK \
           BEACON_GATEWAY BEACON_WLAN_SSID BEACON_WLAN_PSK \
           BEACON_VC4_V3D_DRIVER BEACON_SCREEN_WIDTH BEACON_SCREEN_HEIGHT \
           ROBOT_VC4_V3D_DRIVER ROBOT_SCREEN_WIDTH ROBOT_SCREEN_HEIGHT \
           SDCARD_DEV SDCARD_DEV_BOOT SDCARD_DEV_ROOTFS
