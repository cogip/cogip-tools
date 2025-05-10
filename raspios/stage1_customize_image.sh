#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
source ${SCRIPT_DIR}/common.sh

DOCKER_BUILDKIT=1 docker build --progress plain .. -f Dockerfile.customize --target beacon -t cogip/raspios:beacon
DOCKER_BUILDKIT=1 docker build --progress plain .. -f Dockerfile.customize --target robot -t cogip/raspios:robot
