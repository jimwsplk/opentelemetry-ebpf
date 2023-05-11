#!/bin/bash -xe
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


[[ -n "${MEGABYTE_COUNT}" ]] || MEGABYTE_COUNT=4096
[[ -n "${COOLDOWN_MILLISECONDS}" ]] || COOLDOWN_MILLISECONDS=1000

BYTE_COUNT="$(echo "${MEGABYTE_COUNT} * 1024 * 1024" | bc -q)"
COOLDOWN_SECONDS="$(echo "${COOLDOWN_MILLISECONDS} / 1000" | bc -lq)"

echo "BYTE_COUNT=${BYTE_COUNT}"
echo "COOLDOWN_SECONDS=${COOLDOWN_SECONDS}"

while true; do
  yes | head --bytes="${BYTE_COUNT}" /dev/urandom | pv | sha1sum
  sleep "${COOLDOWN_SECONDS}"
done
