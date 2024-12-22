# Setup

There are two ways to setup the environment to develop and run the tools.

- The [Manual method](#manual-method) requires to configure the environment on the development computer and to run tools one by one.
This method also briefly explains how to build the firmware for the real MCU.

- The [Docker method](#docker-method) provides a complete Docker Compose stack that configure, compile and run each tool using only one command.

To prepare SDCards for Raspberry Pi SDCards for robots and beacon, refer to the [Raspberry Pi OS section](raspios.md).

## Common Setup

### OS

Linux only.

Tested on Ubuntu 24.04 (with Xorg instead of Wayland for proper display of the Monitor).

### Debian packages

```bash
sudo apt install git build-essential
```

### Git Submodules

The tools depend on the compatible version of [cogip/mcu-firmware](https://github.com/cogip/mcu-firmware) which also depends on a specific version of [RIOT-OS/RIOT](https://github.com/RIOT-OS/RIOT). So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`.
Do not forget to fetch the submodules after `git clone`:

```bash
git submodule update --init
```

## Manual Method

### Debian packages

```bash
sudo apt install libxcb-xinerama0 socat protobuf-compiler build-essential swig cmake pkg-config libserial-dev
```

### Build mcu-firmware

See the `Requirements` section of `submodules/mcu-firmware/README.md` to setup the build environment.

Use the following command to build the native version of the firmware:

#### Native build

```bash
make -C submodules/mcu-firmware/applications/cup2023 BOARD=cogip-native
```

#### ARM build

Use the following command to build the ARM version of the firmware:

```bash
make -C submodules/mcu-firmware/applications/cup2023 BOARD=cogip-board-ng
```

### Installation

All tools can be installed on the development PC.

!!! note "Python installation is managed by [uv](https://docs.astral.sh/uv), so it is independent from Python version provided by the OS."

* Install uv following the
[official documentation](https://docs.astral.sh/uv/getting-started/installation/), like with the following command:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

!!! note "Read carefully advices to make uv accessible on your PATH."

* Install the required Python version:

```bash
uv python install
```

* Create a new virtual environment (it will be automatically used by `uv` commands, no need to source it):

```bash
uv venv
```

* Patch Python installation:

!!! note "Note on uv-managed Python installation"
    This Python version is compiled using clang
    so uv will use clang by default to build wheels with C/C++ extensions. Some packages are not compatible
    with clang. `sysconfigpatcher` will revert sysconfig variables to the default values
    of a Python system installation to use gcc to build wheels."

```bash
uvx --isolated --from "git+https://github.com/bluss/sysconfigpatcher" sysconfigpatcher $(dirname $(dirname $(readlink .venv/bin/python)))
```

* Install the package in dev/editable mode (default mode for uv):

```bash
uv sync
```

### Linting and Formatting

While installing the `dev` environment, `ruff` and `pre-commit` package have been installed.

To run `ruff` manually, just run:

```bash
uv run ruff check [--fix]
uv run ruff format
```

To enable pre-commit hooks prevent committing code not respecting linting and formatting rules, run:

```bash
pre-commit install
```

### Packaging and Deployment

This section explains how to build a new binary package and deploy it on a Raspberry Pi.

A Docker Compose service is provided to build a binary distribution package for linux/arm64 platform.

```bash
docker compose up --build build_wheel
```

This will produce `dist/cogip_tools-1.0.0-cp312-cp312-linux_aarch64.whl`.

This package can be copied to the Raspberry Pi and installed to deploy the Python tools:

```bash
uv pip install cogip_tools-1.0.0-cp312-cp312-linux_aarch64.whl
```

!!! warning "Docker image for linux/arm64"
    The `build_wheel` service is based on a image built from a Ubuntu image. If this image was already pulled for
    the `linux/amd64` platform, the `linux/arm64` may not be pulled automatically.
    If the `docker compose` command is failing for this reason, the required image can be pulled manually:
    ```bash
    docker pull --platform "linux/arm64" ubuntu:24.04
    ```

## Docker Method

### Docker Installation

See [Docker installation instructions](https://docs.docker.com/engine/install/).

### Virtual CAN Interface Setup

`Firmware` communicates with `Copilot` using a CAN interface. In emulation mode, a virtual CAN interface (`vcan0`)
must be configured on host before running the Compose stack.

Configure `vcan0` using the two following files:

- `/etc/systemd/network/80-vcan.network`

```ini
[Match]
Name=vcan0

[CAN]
BitRate=500000
DataBitRate=1000000
SamplePoint=87.5%
FDMode=yes
```

- `/etc/systemd/network/vcan0.netdev`

```ini
[NetDev]
Name=vcan0
Kind=vcan
MTUBytes=72
Description=Virtual CAN0 network interface
```

Restart systemd-networkd service to setup:
```bash
sudo systemctl restart systemd-networkd
```

Check `vcan0` is up:

```bash
$ networkctl | grep vcan0
  3 vcan0           can      carrier     configured```

$ ip address show dev vcan0
3: vcan0: <NOARP,UP,LOWER_UP> mtu 72 qdisc noqueue state UNKNOWN group default qlen 1000
    link/can
```

### X Server

The `Monitor` is working with X11 but does not behave correctly with Wayland.

To allow the `Monitor` process running in a Docker container to access the X Server running on the host,
you need to run the following command in a terminal:

`$ xhost +local:`

### Configuration

The configuration of the tools is done by setting environment variables in the `.env` file.

All variables supported by the tools are forwarded inside Docker containers.

### Compose Profiles

Several profiles are defined to select which containers to run:

- `beacon`: for the beacon container
- `robotX`: for robot X containers (1 <= X <= 4)
- `monitorX`: for `Monitor` container of robot X (1 <= X <= 4)

Profiles are set in the `.env` file:

`COMPOSE_PROFILES=beacon,robot1,robot2`

### Build Images

Build Docker images:

`docker compose build`

### Run All Tools

Start the Compose stack:

`docker compose up`

Use `--build` option to build images and start the stack:

`docker compose up --build`

### Automatic Restart on Changes

To automatically restart the services on Python source files changes
or rebuild C++ extensions on C++ source files changes, use the `--watch` option:

`docker compose up --build --watch`

### Dashboards Access

The `Beacon Dashboard` (if enabled in `.env`) is accessible using a web browser at `http://localhost:8080`.

The `Dashboard` for robot X (if enabled in `.env`) is accessible using a web browser at `http://localhost:808X`.

### Running Monitor

Instead of running `Monitor` from the Compose stack, it can be launched for robot X (if enabled in `.env`) with:

```bash
uv run cogip-monitor http://localhost:809X
```
