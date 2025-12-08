FROM ubuntu:25.10 AS uv_base

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update \
 && apt-get -y dist-upgrade --auto-remove --purge \
 && apt-get -y install curl wait-for-it git socat g++ pkg-config libserial-dev gosu libsystemd-dev swig liblgpio-dev \
 && apt-get -y clean

WORKDIR /src

# Install uv
RUN curl -LsSf https://astral.sh/uv/0.9.15/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Install Python in /opt so regular users can use it
ENV UV_PYTHON_INSTALL_DIR=/opt/python

# Required because mcu-firmware is not compatible with uv
ENV PATH="/src/.venv/bin:${PATH}"

# Set frozen uv.lock globally
ENV UV_FROZEN=1

# Pre-install some Python requirements for COGIP tools
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv sync --no-install-project

FROM uv_base AS cogip-console

RUN apt-get update && \
    apt-get install -y \
        cmake \
        swig \
        libfontconfig1 \
        libgl1 \
        libglib2.0-0 \
        libegl1 \
        libxkbcommon0 \
        libdbus-1-3 \
        libnss3 \
        libxcb-cursor0 \
        libxcomposite1 \
        libxdamage1 \
        libxrender1 \
        libxrandr2 \
        libxtst6 \
        libxi6 \
        libxkbfile1 \
        libxcb-xkb1 libxcb-image0 libxcb-render-util0 libxcb-render0 libxcb-util1 \
        libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxkbcommon-x11-0 \
        yaru-theme-icon

# Create regular user and group if not already present.
ARG UID=1000
ARG GID=1000
RUN group_exists=$(getent group ${GID} || true) && echo $group_exists \
 && if [ -z "$group_exists" ]; then groupadd -g ${GID} cogip_users; fi \
 && user_exists=$(getent passwd ${UID} || true) \
 && if [ -z "$user_exists" ]; then useradd -u ${UID} -g ${GID} -m cogip_user; fi \
 && usermod -aG dialout `getent passwd 1000 | cut -d: -f1`

ADD .python-version uv.lock pyproject.toml CMakeLists.txt LICENSE /src/
ADD cogip /src/cogip
RUN uv sync

CMD ["sleep", "infinity"]


FROM uv_base AS cogip-firmware

RUN apt-get update && \
    apt-get install -y \
        g++-multilib \
        gcc-arm-none-eabi \
        gcc-multilib \
        gdb-multiarch \
        libstdc++-arm-none-eabi-newlib \
        make \
        ncat netcat-openbsd \
        protobuf-compiler \
        quilt \
        unzip

CMD ["sleep", "infinity"]


FROM debian:13 AS build_wheel

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update \
 && apt-get -y dist-upgrade --auto-remove --purge \
 && apt-get -y install curl g++ pkg-config libserial-dev \
 && apt-get -y clean

WORKDIR /src

# Install uv
RUN curl -LsSf https://astral.sh/uv/0.9.15/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
ENV UV_PYTHON_INSTALL_DIR=/opt/python
ENV PATH="/src/.venv/bin:${PATH}"

# Help CMake to find the correct compilers
ENV CC="/usr/bin/aarch64-linux-gnu-gcc"
ENV CXX="/usr/bin/aarch64-linux-gnu-g++"
