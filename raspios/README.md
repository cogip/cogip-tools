# Raspberry Pi OS Customization

The `raspios` directory provides a series of scripts to build and flash
a custom Raspberry Pi OS images running COGIP tools on the Pi 4
embedded in the beacon and robots.

It works by creating a Docker image based on Raspberry Pi OS Lite, use Dockerfiles
to install/configure/remove softwares and services, extract and build the customized image,
and flash it on a SDCard.

## Network Configuration

Default network configuration is represented on the following schema:

![Network Configuration](img/cogip-network.svg)

## Requirements

 - Docker

See [Docker installation instructions](https://docs.docker.com/engine/install/).

 - ARM Emulation

```
$ sudo apt-get install binfmt-support qemu-user-static zerofree
$ docker run --rm --privileged tonistiigi/binfmt --install all
```

## Configuration

Two configuration profiles are provided:
  - `cup`: a configuration for the cup, to setup robots and beacon
  - `dev`: a configuration for development environment without beacon
Select a profile by setting the `PROFILE` variable to either `cup` or `dev`.

The following variables must be set before running any script:
  - ROBOT_ID
  - PUBLIC_WLAN_SSID
  - PUBLIC_WLAN_PSK
Those variables are set to `NOT_SET` by default and will be checked will loading the config files.

`ROBOT_ID` possible values:
  - 0:   for the beacon
  - 1-9: for the robots

The PSK value can be generated from the WiFi password using the following command:
```sh
$ wpa_passphrase MYSSID passphrase
network={
        ssid="MYSSID"
        #psk="passphrase"
        psk=59e0d07fa4c7741797a4e394f38a5c321e3bed51d54ad5fcbd3f84bc7415d73d
}
```

The micro SD card device can be customized using related environment variables
Example for micro-SD card to SD card adapter on `/dev/mmcblk0` (default values):
```sh
SDCARD_DEV=/dev/mmcblk0
SDCARD_DEV_BOOT=${SDCARD_DEV}p1
SDCARD_DEV_ROOTFS=${SDCARD_DEV}p2
```

Example for micro-SD card to USB adapter on `/dev/sda`:
```sh
SDCARD_DEV=/dev/sda
SDCARD_DEV_BOOT=${SDCARD_DEV}1
SDCARD_DEV_ROOTFS=${SDCARD_DEV}2
```

Customized variables can be set in the environment or in a local, not-committed `.env` file
in the `raspios` directory.

Example of a complete `.env` file:
```sh
PROFILE=dev
ROBOT_ID=1
PUBLIC_WLAN_SSID=MYSSID
PUBLIC_WLAN_PSK=59e0d07fa4c7741797a4e394f38a5c321e3bed51d54ad5fcbd3f84bc7415d73d
SDCARD_DEV=/dev/sda
SDCARD_DEV_BOOT=${SDCARD_DEV}1
SDCARD_DEV_ROOTFS=${SDCARD_DEV}2
```

## Stage 0

First stage builds a docker image from original Raspios image.

```
$ ./stage0_base_image.sh
```

## Stage 1

Build a customized docker image:
 - install required Debian and Python packages
 - configure required services
 - install COGIP tools

```
$ ./stage1_customize_image.sh
```

## Stage 1b (under development)

This stage is optional and allow to build a custom kernel image.
It is not working yet so not documented.

## Stage 2

Create the custom filesystem image.

```
$ ./stage2_create_image.sh
```

## Stage 3

Flash the filesystem image on SDCard.

```
$ ./stage3_flash_image.sh
```
