FROM ubuntu:24.04 AS uv_base

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update \
 && apt-get -y dist-upgrade --auto-remove --purge \
 && apt-get -y install curl wait-for-it git socat g++ \
 && apt-get -y clean

WORKDIR /src

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Install Python, version is specified in .python-version, a bind mount from root directory.
RUN --mount=type=bind,source=.python-version,target=.python-version \
    uv python install

# Create a virtual environmnent to respect PEP 668
RUN uv venv

# Required because mcu-firmware is not compatible with uv
ENV PATH="/src/.venv/bin:${PATH}"

# Patch sysconfig of uv-managed Python installation. This Python version is compiled using clang
# so uv will use clang by default to build wheels with C/C++ extensions. Some packages are not compatible
# with clang. sysconfigpatcher will revert sysconfig variables to the default values
# of a Python system installation to use gcc to build wheels.
RUN uvx --isolated --from "git+https://github.com/bluss/sysconfigpatcher" sysconfigpatcher $(dirname $(dirname $(readlink .venv/bin/python)))

# Pre-install some Python requirements for COGIP tools
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --frozen

FROM uv_base AS cogip-console

RUN apt-get update && \
    apt-get install -y \
        libgl1 \
        libglib2.0-0 \
        cmake \
        swig

ADD .python-version uv.lock pyproject.toml LICENSE /src/
ADD cogip /src/cogip
RUN uv sync --frozen


CMD ["sleep", "infinity"]


FROM cogip-console AS cogip-gui

RUN apt-get install -y \
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
