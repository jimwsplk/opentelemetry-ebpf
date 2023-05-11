#!/bin/bash -xe
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


export EBPF_NET_SRC="${EBPF_NET_SRC:-$(git rev-parse --show-toplevel)}"

IMAGE_TAG="$(cd ${EBPF_NET_SRC}/build-env && ./get_tag.sh final)"
IMAGE_NAME="${IMAGE_TAG%%:*}"
IMAGE_VERSION="${IMAGE_TAG##*:}"
EBPF_NET_DOCKER_REGISTRY="966881513036.dkr.ecr.us-east-1.amazonaws.com/bld"

if [[ "$#" -gt 0 ]]; then
  IMAGE_VERSION="$1"; shift
fi

"${EBPF_NET_SRC}/dev/docker-registry-login.sh" ecr

for version in "${IMAGE_VERSION}" latest; do
  remote_image_tag="${EBPF_NET_DOCKER_REGISTRY}/${IMAGE_NAME}:${version}"
  docker tag "${IMAGE_NAME}:${IMAGE_VERSION}" "${remote_image_tag}"
  docker push "${remote_image_tag}"
done
