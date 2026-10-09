# board-cogip-img: the COGIP Armbian image

Port of the `raspios/` image to Armbian (vendor kernel, `BUILD_MINIMAL`). Built
incrementally:

- step 1 [done]: base system + peripherals.
- step 2 [done]: COGIP app, headless (uv venv + cogip tools built in `/opt`).
- step 3 [done]: targets (robot / pami / beacon): per-target packages +
  service enablement, graphical kiosk (weston/chromium), beacon AP (dnsmasq).
- step 4 [done]: per-robot config, all selected by `ROBOT_ID`: per-class
  resolved `/etc/environment` (geometry / detector / pins / servos), static
  wlan0 IP, beacon AP IP, hostname + `/etc/hosts` peer map, fixed SSH host keys
  (`ssh/`), wpa PSK via the gitignored drop-in.
- step 5 [done]: flash helper (`flash.sh`, same `ROBOT_ID` scheme, device
  guards + confirmation, bmaptool/dd).

## Flash

```sh
ROBOT_ID=2 ./flash.sh /dev/sdX      # resolve + verify + flash pami2 (ninja)
ROBOT_ID=0 ./flash.sh /dev/sdX      # beacon
```

Destructive and refuses the host system disk; asks for `oui` before writing.
First boot resizes the rootfs; then `ssh root@<ip>` (key already baked).

## Host prerequisites

The Armbian base build runs inside Armbian's own Docker container (it relaunches
itself there), so the host stays minimal. On a Debian/Ubuntu host:

```sh
sudo apt install docker.io git qemu-user-static binfmt-support util-linux bmap-tools
sudo usermod -aG docker "$USER"   # then re-login
```

- `docker`: Armbian builds the base image in its container (user in the `docker`
  group). Armbian pulls its own cross-toolchain and build deps inside it.
- `qemu-user-static` + `binfmt-support`: the container runs the aarch64 rootfs
  chroot through binfmt (qemu registered on the host kernel).
- `git`: clones `armbian/build` at `ARMBIAN_REF` and feeds the base hash.
- `sudo` + util-linux (`losetup`/`mount`/`umount`): the host-side provision
  loop-mounts the rootfs to write per-robot data (no qemu here).
- `bmap-tools` (`bmaptool`): `flash.sh`, with a `dd` fallback.

## Build

```sh
./build.sh                 # BOARD=rpi4b ROBOT_ID=1 (robot)
ROBOT_ID=2 ./build.sh      # ninja
ROBOT_ID=3 ./build.sh      # pami
ROBOT_ID=0 ./build.sh      # beacon
BOARD=rock-5b ./build.sh
```

`ROBOT_ID` is the single knob: `0`=beacon, `1`=robot, `2`=ninja, `3-9`=pami. It
selects the service target and the value class, and is added to `BEACON_IP`'s
last octet for the static IP.

Two phases (needs `sudo` for the provision's loop-mount):
1. **Base** (`lib/build-base.sh`): heavy, per-TARGET, built once under qemu
   (packages + `cogip.cpp` wheel + services). Rebuilt only when the app source
   hash changes (or `BASE_REBUILD=1`). Kept as `base-<target>-<board>.img`.
2. **Provision** (`lib/provision.sh`): fast, host-side, writes the per-robot data
   (env / hostname / hosts / IP / SSH keys / authorized_keys / wpa) onto a copy
   of the base. So `ROBOT_ID=2` then `ROBOT_ID=3` reuse one pami base.

Scripts: `build.sh` (orchestrator) + `lib/{derive,build-base,provision}.sh`;
`lib/derive.sh` (the `ROBOT_ID` mapping) is shared with `flash.sh`.

Output image: `board-cogip-img-<suffix>-<board>.img` (suffix `robot<id>`,
`pami<id>` or `beacon`).

Env: `BOARD` (default `rpi4b`), `ROBOT_ID` (default `1`, see above),
`BEACON_IP` (default `192.168.2.100`), `BASE_REBUILD` (force base rebuild),
`BRANCH` (`current`), `RELEASE` (`trixie`, Debian 13 so system python is 3.13
like `.python-version`; uv is only-managed so the venv is managed-3.13
regardless), `COGIP_ROOT_PASSWORD` (`cogip`), `ARMBIAN_BUILD_DIR`, `ARMBIAN_REF`
(pinned Armbian release, default `v26.08` (the 26.8 release branch); bump to upgrade, build.sh switches
an existing checkout and the base rebuilds). The base hash tracks the app
source, the recipe (`customize-image.sh` + the `customize.d/` fragments +
overlays) and the Armbian release/branch/commit, so any of those changing forces
a base rebuild; env / SSH keys / wpa are provision-level and do not.

Board- and target-specific logic lives in `customize.d/`, kept apart from the
generic `customize-image.sh`: one file per board (`board-<board>.sh`: console
UART, board-only service masks, GPIO-SWD flag, and the `config.txt` peripheral
hook) and one per target (`target-<target>.sh`: extra packages + service
enablement). build.sh stages the matching pair into the chroot (and appends the
board file to the Armbian config so its hook registers). Adding a board or
target = one new file; the generic path (packages, app) is untouched.

## What steps 1-2 produce

Step 1 (base + peripherals):
- Minimal Armbian, root-only, auto password, firstlogin wizard disabled, SSH on.
- Serial console on `ttyAMA0` (freed by `disable-bt`).
- Peripheral overlays in `config.txt` (board-specific, `customize.d/board-<board>.sh`):
  CAN-FD `mcp251xfd` on SPI1 CE0, UART2/4, I2C, RTC, cameras imx219/imx296.
  (No UART5: it would claim GPIO12/13 and steal the ninja/pami LED on BCM13.)
- `can0` brought up by networkd (500k/1M, FD); `vcan0` for sim/tests.
- `i2c-dev` / `i2c-bcm2835` auto-loaded.
- Wi-Fi: robot/pami/ninja default to the committed cup network
  (`wpa_supplicant.cup.conf`, `COGIP_5G`); drop a gitignored `wpa_supplicant.conf`
  next to `build.sh` to override with a dev network. Static IP is derived from
  `ROBOT_ID` at provision time (no `wlan0.network`). beacon needs a drop-in (venue
  uplink).

Step 2 (COGIP app, headless):
- uv (pinned) installed; the cogip tools are built and installed into
  `/opt/.venv` (`uv sync --no-editable`). The `cogip.cpp` C++ wheel is built in
  the image under qemu, so this step is slow. The source tree is staged into
  `/opt` by `build.sh` and removed after install.
- App config: `/etc/environment` resolved per class from `env/environment.*`
  (step 4 picks it by `ROBOT_ID`; only `ROBOT_ID` itself is injected at build),
  venv `profile.d` + `sudoers`.
- Service units staged but NOT enabled (step 3 enables per target):
  `cogip-server/dashboard/planner/copilot/detector/mcu-logger`, `openocd`.
- `systemd-resolved` + `rsyslog` enabled.

## Why a build hook for config.txt

The Armbian bcm2711 family writes `config.txt` with `>` late in the build
(`pre_umount_final_image__write_raspi_config`), after `customize-image.sh`. So
the peripheral overlays are appended by a hook defined in the board fragment
(`customize.d/board-<board>.sh`, function suffix `zzz_` to sort after it),
registered by appending that fragment to the generated userpatches config
(`lib.config` is no longer supported). The same fragment is also sourced inside
`customize-image.sh` for its board variables.

The hook keeps only the logic; the actual `config.txt` lines live in overlay data
files (`usr/local/lib/cogip-config/<role>.txt`, `robot` or `beacon`), staged into
the rootfs by the overlay and picked by `COGIP_TARGET`. The hook appends the right
one and removes the staging dir so it does not ship.
