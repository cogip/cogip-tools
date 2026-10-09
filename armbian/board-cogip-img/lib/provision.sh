#!/bin/bash
# Provision per-robot instance data onto a COPY of the base image, host-side (no
# qemu). Loop-mounts the rootfs and writes the files that differ per robot:
# /etc/environment (class values + ROBOT_ID), hostname, hosts, SSH host keys,
# root authorized_keys, static wlan0 IP, beacon AP IP, build.conf, wpa config.
# Needs sudo for the mount; everything written is owned root (no uid fixups).
#
# Relies on vars set by build.sh: SCRIPT_DIR BASE_IMG IMAGES_DIR BOARD TARGET
# CLASS CLASS_LC SUFFIX HOSTNAME ROBOT_ID BEACON_IP COGIP_IP IP_PREFIX IP_LAST.
# Sets: IMG (final image path).

# All per-robot writes onto the mounted rootfs ($1 = mount point).
_cogip_provision_files() {
    local m="$1"

    # /etc/environment: resolved per class, then inject ROBOT_ID (socketio port
    # 809<id>, the ROBOT_ID line, kiosk 808<id>).
    sudo install -m 644 "${SCRIPT_DIR}/env/environment.${CLASS_LC}" "${m}/etc/environment"
    sudo sed -i "s/809ROBOT_ID/809${ROBOT_ID}/g" "${m}/etc/environment"
    sudo grep -q '^ROBOT_ID=' "${m}/etc/environment" || sudo sed -i "1i ROBOT_ID=${ROBOT_ID}" "${m}/etc/environment"
    [ -f "${m}/root/start_chromium.sh" ] && sudo sed -i "s/808ROBOT_ID/808${ROBOT_ID}/g" "${m}/root/start_chromium.sh"

    # Hostname + peer map (beacon + robot1-6 from BEACON_IP).
    printf '%s\n' "${HOSTNAME}" | sudo tee "${m}/etc/hostname" >/dev/null
    {
        echo "127.0.0.1	localhost"
        echo "127.0.1.1	${HOSTNAME}"
        echo "${IP_PREFIX}.${IP_LAST} beacon"
        local n; for n in 1 2 3 4 5 6; do echo "${IP_PREFIX}.$((IP_LAST + n)) robot${n}"; done
    } | sudo tee "${m}/etc/hosts" >/dev/null

    # Fixed SSH host keys for this HOSTNAME (stable identity across reflash).
    local ssrc="${SCRIPT_DIR}/ssh" t k
    if [ -d "${ssrc}" ] && ls "${ssrc}/ssh_host_"*"_key_${HOSTNAME}" >/dev/null 2>&1; then
        sudo mkdir -p "${m}/etc/ssh"
        for t in ecdsa ed25519 rsa; do
            k="${ssrc}/ssh_host_${t}_key_${HOSTNAME}"
            [ -f "${k}" ]     && sudo install -m 600 -o root -g root "${k}"     "${m}/etc/ssh/ssh_host_${t}_key"
            [ -f "${k}.pub" ] && sudo install -m 644 -o root -g root "${k}.pub" "${m}/etc/ssh/ssh_host_${t}_key.pub"
        done
    else
        echo "WARNING: no fixed SSH host keys for '${HOSTNAME}' in ${ssrc}." >&2
    fi

    # ssh-copy-id at build: operator pubkey(s) into root authorized_keys. Drop-in
    # next to build.sh wins, else the builder's ~/.ssh/*.pub.
    local auth="${SCRIPT_DIR}/authorized_keys" tmp=""
    if [ ! -f "${auth}" ]; then
        tmp=$(mktemp); cat "${HOME}"/.ssh/*.pub > "${tmp}" 2>/dev/null || true
        [ -s "${tmp}" ] && auth="${tmp}" || auth=""
    fi
    if [ -n "${auth}" ] && [ -s "${auth}" ]; then
        sudo install -D -m 600 -o root -g root "${auth}" "${m}/root/.ssh/authorized_keys"
        sudo chmod 700 "${m}/root/.ssh"
        echo "Root authorized_keys baked ($(grep -c . "${auth}") key(s))."
    else
        echo "No operator public key found; root login will need the password." >&2
    fi
    [ -n "${tmp}" ] && rm -f "${tmp}"

    # Static wlan0 for robot/pami (beacon keeps DHCP wlan0 = venue uplink).
    case "${TARGET}" in
        robot|pami)
            printf '[Match]\nType=wlan\n\n[Network]\nAddress=%s/24\nGateway=%s\nDNS=%s\n' \
                "${COGIP_IP}" "${BEACON_IP}" "${BEACON_IP}" \
                | sudo tee "${m}/etc/systemd/network/20-wlan0.network" >/dev/null
            ;;
        beacon)
            # Beacon eth0 is the AP side at COGIP_IP; dnsmasq listens on it.
            sudo sed -i "s|IP_ADDRESS|${COGIP_IP}|g" \
                "${m}/etc/systemd/network/00-eth0.network" "${m}/etc/dnsmasq.conf" 2>/dev/null || true
            ;;
    esac

    # Instance record (documents what this image is).
    sudo mkdir -p "${m}/etc/cogip"
    printf 'COGIP_TARGET=%s\nCOGIP_CLASS=%s\nCOGIP_ROBOT_ID=%s\nCOGIP_BEACON_IP=%s\nCOGIP_IP=%s\n' \
        "${TARGET}" "${CLASS}" "${ROBOT_ID}" "${BEACON_IP}" "${COGIP_IP}" \
        | sudo tee "${m}/etc/cogip/build.conf" >/dev/null

    # Wi-Fi config. A gitignored drop-in next to build.sh wins (dev network);
    # otherwise robot/pami/ninja fall back to the committed cup default
    # (COGIP_5G). beacon has no default (its wlan0 is the venue uplink, so it
    # needs a drop-in).
    local wpa="${SCRIPT_DIR}/wpa_supplicant.conf"
    [ -f "${wpa}" ] || wpa="${SCRIPT_DIR}/wpa_supplicant-wlan0.conf"
    if [ ! -f "${wpa}" ] && [ "${TARGET}" != "beacon" ]; then
        wpa="${SCRIPT_DIR}/wpa_supplicant.cup.conf"
    fi
    if [ -f "${wpa}" ]; then
        sudo mkdir -p "${m}/etc/wpa_supplicant"
        sudo install -m 600 -o root -g root "${wpa}" "${m}/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
        echo "Wi-Fi staged (${wpa##*/})."
    else
        echo "No Wi-Fi config for ${TARGET}; drop a wpa_supplicant.conf next to build.sh." >&2
    fi

    # Camera: only the ninja (ROBOT_ID 2) has one; the pami base does not enable
    # robotcam, so enable it here per-robot (offline, by [Install] WantedBy).
    if [ "${ROBOT_ID}" = "2" ]; then
        sudo systemctl --root="${m}" enable cogip-robotcam.service >/dev/null 2>&1 \
            && echo "robotcam enabled (ninja)." \
            || echo "WARNING: could not enable robotcam" >&2
    fi
}

cogip_provision() {
    IMG="${IMAGES_DIR}/board-cogip-img-${SUFFIX}-${BOARD}.img"
    echo "Provisioning ${HOSTNAME} (ROBOT_ID=${ROBOT_ID}) from $(basename "${BASE_IMG}")..."
    cp --reflink=auto -f "${BASE_IMG}" "${IMG}"

    local loop mnt root_part
    loop=$(sudo losetup --show -Pf "${IMG}")
    mnt=$(mktemp -d)
    # rootfs = the ext4 partition (last partition of the image).
    root_part=$(lsblk -lnpo NAME "${loop}" | tail -1)
    sudo mount "${root_part}" "${mnt}"
    # shellcheck disable=SC2064
    trap "sudo umount '${mnt}' 2>/dev/null || true; sudo losetup -d '${loop}' 2>/dev/null || true; rmdir '${mnt}' 2>/dev/null || true" RETURN

    _cogip_provision_files "${mnt}"
    sync

    sudo umount "${mnt}"; sudo losetup -d "${loop}"; rmdir "${mnt}"; trap - RETURN

    ( cd "${IMAGES_DIR}" && sha256sum "$(basename "${IMG}")" > "${IMG}.sha" )
    command -v bmaptool >/dev/null 2>&1 && bmaptool create -o "${IMG}.bmap" "${IMG}" || true
}
