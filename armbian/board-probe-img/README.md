# board-probe-img: board feasibility probe

Goal: on **any** board (rpi4b, Rockchip rock-5b, ...), build a minimal Armbian
image that boots on its own and reports, on real hardware, what the stock
vendor kernel offers for the COGIP peripherals: CAN, I2C, SPI, UART, camera,
GPIO. This decides, per board, what is ready as modules/overlays vs what (if
anything) needs a kernel change, before porting any COGIP customization.

The image is deliberately minimal (`BUILD_MINIMAL=yes`, no desktop). Only a few
small, on-topic probe tools are installed (`i2c-tools`, `gpiod`, `can-utils`);
the probe still falls back to `/sys` when a tool is missing.

## 1. Build

Needs Docker (Armbian builds in a container) and ~25 GB free disk. Pick the
board; the name is whatever `armbian/build`'s `./compile.sh` lists.

```sh
./build.sh                # defaults to BOARD=rpi4b
BOARD=rock-5b ./build.sh
BOARD=rock-5b BRANCH=vendor RELEASE=noble ./build.sh
```

Env vars: `BOARD` (default `rpi4b`), `BRANCH` (default `current`), `RELEASE`
(default `trixie`), `ARMBIAN_BUILD_DIR`, `ARMBIAN_REF`, `COGIP_ROOT_PASSWORD`
(default `cogip`). Output image lands in `armbian-build/output/images/`.

The built image:
- is **root-only**, password `cogip` (override with `COGIP_ROOT_PASSWORD`), with
  the Armbian firstlogin wizard disabled (no interactive user creation);
- runs `cogip-hw-report.service` once at first boot;
- brings Ethernet up by DHCP; Wi-Fi only if you stage a config (below).

## 2. Boot and collect the report

Flash (`dd` or balena-etcher), boot the board, wait ~1 min. The report is
written to the **boot partition** as `cogip-hw-report.txt` (and `/root/`), so
you can just pull the SD and read it from any PC, no network needed:

```sh
# boot partition is the first one; mount it and read the report
cat /media/$USER/*/cogip-hw-report.txt
```

Over the network instead: `ssh root@<ip>` then `cat /root/cogip-hw-report.txt`.

Send the report back; it drives the per-board decision.

## 3. Wi-Fi (optional)

The feasibility report does not need the network. If you still want Wi-Fi,
drop a filled `wpa_supplicant.conf` next to `build.sh` (gitignored, holds the
passphrase) before building:

```
country=FR
ctrl_interface=DIR=/run/wpa_supplicant GROUP=netdev
update_config=1
network={
    ssid="YOUR_SSID"
    psk="YOUR_PASSPHRASE"
}
```

It is board-agnostic: a systemd `.link` renames any wireless interface to
`wlan0` at boot (whatever the board calls it, e.g. `wlP1p1s0`), so the stock
`wpa_supplicant@wlan0` template unit just works; systemd-networkd does DHCP by
matching `Type=wlan`.

Note: Armbian's `armbian_first_run.txt` no longer configures the network (its
`FR_net_*` keys are ignored); the stack is systemd-networkd + wpa_supplicant.

## What this probe reports

- kernel + board/Armbian release
- kernel config for CAN / I2C / SPI / UART / camera / GPIO (`/proc/config.gz`)
- loaded modules + which of the key drivers are loadable (`modinfo`)
- boot config and device-tree overlay dirs present
- device nodes (`/dev/i2c-*`, `/dev/spidev*`, UARTs, `/dev/video*`)
- I2C/SPI/GPIO via `/sys`, CAN netdevs via `ip`
