#!/bin/bash
# Derive the per-robot identity from ROBOT_ID. Sourced by build.sh, provision.sh and
# flash.sh so the ROBOT_ID -> target/class/ip mapping lives in ONE place.
#
# Inputs (env): ROBOT_ID (0-9), BOARD, BEACON_IP.
# Sets: TARGET CLASS CLASS_LC SUFFIX HOSTNAME IP_PREFIX IP_LAST COGIP_IP.
#
# Scheme (raspios): 0=beacon, 1=robot, 2=ninja, 3-9=pami. ninja runs the pami
# services (TARGET=pami) but has its own geometry/pins (CLASS=NINJA). Every
# non-beacon host is robot<id> on the network / in /etc/hosts.
cogip_derive() {
    case "${ROBOT_ID}" in ''|*[!0-9]*)
        echo "ROBOT_ID must be a single digit 0-9 (got '${ROBOT_ID}')" >&2; return 1 ;;
    esac
    case "${ROBOT_ID}" in
        0) TARGET=beacon; CLASS=BEACON; SUFFIX=beacon ;;
        1) TARGET=robot;  CLASS=ROBOT;  SUFFIX="robot${ROBOT_ID}" ;;
        2) TARGET=pami;   CLASS=NINJA;  SUFFIX="pami${ROBOT_ID}" ;;
        *) TARGET=pami;   CLASS=PAMI;   SUFFIX="pami${ROBOT_ID}" ;;
    esac
    CLASS_LC=$(printf '%s' "${CLASS}" | tr '[:upper:]' '[:lower:]')
    case "${ROBOT_ID}" in 0) HOSTNAME=beacon ;; *) HOSTNAME="robot${ROBOT_ID}" ;; esac
    IP_PREFIX="${BEACON_IP%.*}"; IP_LAST="${BEACON_IP##*.}"
    COGIP_IP="${IP_PREFIX}.$((IP_LAST + ROBOT_ID))"
}
