#!/bin/bash
# Armbian customize-image.sh for the COGIP BASE image (runs in the image chroot).
# GENERIC orchestrator: builds the class-generic base for one TARGET (packages,
# the COGIP app /opt/.venv, services). Board- and target-specific bits live in
# customize.d/{board-<BOARD>,target-<TARGET>}.sh, staged by build.sh under
# ${FRAG} and sourced below. NO per-robot instance data here (ROBOT_ID / IP /
# hostname / SSH keys / wlan0 are written later by build.sh's host-side provision).
# Args from Armbian: $1=RELEASE $2=LINUXFAMILY $3=BOARD $4=BUILD_DESKTOP $5=ARCH
set -euo pipefail

RELEASE=${1:-}; LINUXFAMILY=${2:-}; BOARD=${3:-}; ARCH=${5:-}
ROOT_PASSWORD="${COGIP_ROOT_PASSWORD:-cogip}"
FRAG=/usr/local/lib/cogip-build   # board/target fragments, removed at the end

# Peripheral tooling + what the COGIP Python app needs to build (cogip.cpp C++
# wheel: build-essential/cmake/swig + dev libs) and run (can-utils, serial, i2c,
# openocd). Graphical/camera/AP packages belong to the target fragments.
PACKAGES="
build-essential
ca-certificates
can-utils
cmake
curl
git
gpiod
i2c-tools
libbz2-dev
libcap-dev
libffi-dev
libi2c-dev
liblzma-dev
libncurses5-dev
libncursesw5-dev
libreadline-dev
libserial-dev
libsqlite3-dev
libssl-dev
libsystemd-dev
llvm
openocd
picocom
rsyslog
swig
systemd-resolved
tk-dev
vim
zlib1g-dev
"

# Graphical kiosk set, referenced by the target fragments (robot, beacon). Camera
# libs (libcamera) are NOT here: they are target-specific (TARGET_BACKPORTS_PACKAGES
# in the robot/pami fragments) and bridged into the managed venv further down.
KIOSK_PACKAGES="weston chromium libinput-tools libegl1 libgles2 mesa-utils mesa-utils-bin xwayland"

# The cogip core service set, shared by the robot/pami targets. openocd (GPIO-SWD
# via rpi-cogip.cfg) is Pi-only, gated on BOARD_GPIO_SWD (set by the board frag).
enable_cogip_core() {
    systemctl enable cogip-server cogip-dashboard cogip-planner \
                     cogip-copilot cogip-detector cogip-mcu-logger
    [ -n "${BOARD_GPIO_SWD:-}" ] && systemctl enable openocd || true
}

# Overlay is bind-mounted at /tmp/overlay; Armbian does not lay it into the
# rootfs itself. Only class-generic files are in the base overlay.
cp -a /tmp/overlay/. / 2>/dev/null || true
chmod +x /usr/local/sbin/cogip-rfkill-unblock.sh /root/start_chromium.sh 2>/dev/null || true
# The overlay carries the build host's uid/gid and group-write on /root; sshd
# StrictModes then rejects pubkey auth. Restore root ownership + 0700.
chown -R root:root /root /etc/cogip 2>/dev/null || true
chmod 700 /root

# TARGET for this base (robot/pami/beacon), written by build.sh into base.conf.
TARGET=robot
[ -f /etc/cogip/base.conf ] && . /etc/cogip/base.conf
TARGET="${COGIP_TARGET:-${TARGET}}"

# Board + target fragments (staged by build.sh). The board frag sets CONSOLE_TTY
# / BOARD_MASK_UNITS / BOARD_GPIO_SWD; the target frag sets TARGET_PACKAGES +
# enable_services().
CONSOLE_TTY=""; BOARD_MASK_UNITS=""; BOARD_GPIO_SWD=""; TARGET_PACKAGES=""; TARGET_BACKPORTS_PACKAGES=""
[ -f "${FRAG}/board-${BOARD}.sh" ] && . "${FRAG}/board-${BOARD}.sh" \
    || echo "WARNING: no board fragment customize.d/board-${BOARD}.sh" >&2
. "${FRAG}/target-${TARGET}.sh"

# Armbian's default 10-dhcp.network matches Type=ether/wlan and, sorting before
# our 10-eth / 20-wlan0, is the first match networkd applies, shadowing them
# (first match wins). Drop it so our per-type configs govern.
rm -f /etc/systemd/network/10-dhcp.network

# Our overlay ships some conffiles (e.g. beacon's /etc/ntpsec/ntp.conf) before the
# package is installed, so dpkg would prompt on the conflict and hang the qemu
# build. noninteractive + confold keeps our version silently.
export DEBIAN_FRONTEND=noninteractive
APT_CONF='-o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef'
apt-get update
apt-get install -y --no-install-recommends ${APT_CONF} ${PACKAGES} ${TARGET_PACKAGES}

# Camera libs (libcamera) for the robotcam picamera2 path. The Debian/Armbian
# candidate is the rpt 0.7.2 build whose matching libcamera0.7 (= 0.7.2) is in no
# enabled repo, so it is uninstallable; the coherent pair is 0.7.1 in
# trixie-backports. The Armbian trixie image already lists trixie-backports in
# debian.sources (add it only if a future release drops it). trixie-backports is
# NotAutomatic, so the explicit `-t trixie-backports` install is the only thing
# that takes from it (apt upgrade stays on Debian/Armbian main).
if [ -n "${TARGET_BACKPORTS_PACKAGES}" ]; then
    if ! grep -rqs trixie-backports /etc/apt/sources.list /etc/apt/sources.list.d; then
        echo "deb http://deb.debian.org/debian trixie-backports main" \
            > /etc/apt/sources.list.d/trixie-backports.list
        apt-get update
    fi
    apt-get install -y --no-install-recommends ${APT_CONF} -t trixie-backports ${TARGET_BACKPORTS_PACKAGES}
fi
apt-get clean

# Root-only, auto password, no interactive firstlogin wizard.
echo "root:${ROOT_PASSWORD}" | chpasswd
rm -f /root/.not_logged_in_yet
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config || true
systemctl enable ssh || true

# Serial console on the board's UART (device is board-specific).
[ -n "${CONSOLE_TTY}" ] && systemctl enable "serial-getty@${CONSOLE_TTY}.service" 2>/dev/null || true

# Locale/timezone.
ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
echo "Europe/Paris" > /etc/timezone

# Trim noisy/unneeded periodic jobs (generic Debian/Armbian; ignore names absent
# on this release) plus any board-specific units. The ssh host-key regeneration
# stays masked: the provision ships fixed keys.
for u in e2scrub_reap.service \
         apt-daily.timer apt-daily-upgrade.timer dpkg-db-backup.timer \
         e2scrub_all.timer fstrim.timer fstrim.service man-db.timer \
         sshswitch.service regenerate_ssh_host_keys.service \
         sshd-keygen.service ${BOARD_MASK_UNITS}; do
    systemctl mask "$u" 2>/dev/null || true
done

# Network name resolution + syslog (mcu-logger/openocd log to the syslog target).
systemctl enable systemd-resolved.service 2>/dev/null || true
systemctl enable rsyslog.service 2>/dev/null || true

# Drop desktop/cloud bloat if the base pulled any in (harmless if absent).
apt-get purge -y --auto-remove network-manager cloud-init apparmor avahi-daemon 2>/dev/null || true

# The PyPI `lgpio` wheel links the system liblgpio (it does NOT bundle it), and
# liblgpio-dev is an RPi OS package absent from Debian (bookworm and trixie). So
# build the lg library from source into /usr/local (install also drops the
# `liblgpio.so` dev symlink + runs ldconfig); its optional python bits are
# non-fatal. LIBRARY_PATH/C_INCLUDE_PATH let the wheel find it at build time.
curl -fsSL -o /tmp/lg.tar.gz https://github.com/joan2937/lg/archive/refs/heads/master.tar.gz
mkdir -p /tmp/lg && tar -xzf /tmp/lg.tar.gz -C /tmp/lg --strip-components=1
# Build + install only the liblgpio C library (not rgpiod/rgs/docs; `make
# install` is avoided because it also runs the lg python bindings' setup.py,
# which we do not use and which needs setuptools).
make -C /tmp/lg liblgpio.so
install -m 0644 /tmp/lg/lgpio.h /usr/local/include/
install -m 0755 /tmp/lg/liblgpio.so.1 /usr/local/lib/
ln -sf liblgpio.so.1 /usr/local/lib/liblgpio.so
ldconfig
rm -rf /tmp/lg /tmp/lg.tar.gz
export LIBRARY_PATH="/usr/local/lib:${LIBRARY_PATH:-}"
export C_INCLUDE_PATH="/usr/local/include:${C_INCLUDE_PATH:-}"

# COGIP Python app: uv + venv + install the cogip tools into /opt. build.sh
# staged the project there (pyproject/uv.lock/.python-version/CMakeLists/cogip).
# HEAVY: builds the cogip.cpp C++ wheel inside the image (qemu aarch64), slow.
# This is why it lives in the base (built once per TARGET, not per robot).
curl -LsSf https://astral.sh/uv/0.9.15/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
cd /opt
uv venv --system-site-packages
uv sync --no-dev --no-install-project --frozen
uv sync --no-dev --no-editable --frozen
# Runtime needs the venv + project metadata only (services use the installed
# package / `uv run`); drop the source tree and build inputs to slim the image.
rm -rf /opt/cogip /opt/CMakeLists.txt /opt/build /opt/uv-*.lock /root/.cache/uv
cd /

# Camera venv wiring (only when the target pulled libcamera). The venv is managed
# CPython 3.13 (uv), so the apt python3-libcamera bindings in the system
# dist-packages are invisible to it. Bridge that dir in with a .pth (same cp313
# ABI, so the extension loads). picamera2 then imports its DRM preview at load,
# which pulls pykms (python3-kms++): that is RPi-only and absent here, but robotcam
# is headless and never instantiates DrmPreview, so an empty stub satisfies the
# import (pykms.Card() is only reached on the unused preview path).
if [ -n "${TARGET_BACKPORTS_PACKAGES}" ]; then
    for sp in /opt/.venv/lib/python3.*/site-packages; do
        [ -d "${sp}" ] || continue
        echo "/usr/lib/python3/dist-packages" > "${sp}/cogip-system-libcamera.pth"
        # picamera2's DrmPreview class body reads pykms.PixelFormat.* at import; an
        # inert stub whose every attribute resolves is enough (pykms.Card() is only
        # reached on the unused preview path).
        [ -d "${sp}/picamera2" ] && cat > "${sp}/pykms.py" <<'PYKMS'
class _Inert:
    def __getattr__(self, name):
        return _Inert()

    def __call__(self, *a, **k):
        return _Inert()


def __getattr__(name):
    return _Inert()
PYKMS
    done
fi

apt-get clean

# Wi-Fi (board-agnostic: .link renames the iface to wlan0). The wpa config is
# provisioned later; enable the template now and mask systemd-rfkill so it cannot
# restore a soft block (we do not use BT either).
systemctl enable wpa_supplicant@wlan0.service || true
systemctl mask systemd-rfkill.service systemd-rfkill.socket || true

# Target dispatch (defined by the target fragment).
enable_services

# Drop the staged fragments so they do not ship in the image.
rm -rf "${FRAG}"
