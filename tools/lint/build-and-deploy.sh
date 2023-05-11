#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

set -e

NAME=clang-format
TAG=7.0.1

# the path to extract from the archive
ARCHIVE_PATH="clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-18.04/bin/clang-format"

if [ ! -r "${ARCHIVE_PATH}" ]; then
    curl -L "http://releases.llvm.org/7.0.1/clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-18.04.tar.xz" | tar xvJ "${ARCHIVE_PATH}"
fi

ln -sf ${ARCHIVE_PATH} clang-format

docker build -t "${NAME}:${TAG}" -t "966881513036.dkr.ecr.us-east-1.amazonaws.com/prd/${NAME}:${TAG}" .
# shellcheck disable=SC2091
$(aws-vault exec flowmill-prod -- aws ecr get-login --no-include-email)
docker push "966881513036.dkr.ecr.us-east-1.amazonaws.com/prd/${NAME}:${TAG}"
