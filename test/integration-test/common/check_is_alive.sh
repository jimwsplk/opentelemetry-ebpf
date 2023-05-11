#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -e

if [[ -z "${HEALTH_CHECK_ADDRESS}" ]] && [[ -n "${HEALTH_CHECK_INTERFACE}" ]]; then
  HEALTH_CHECK_ADDRESS="`./common/get_interface_ip.sh "${HEALTH_CHECK_INTERFACE}"`"
fi

if [[ -n "${HTTP_HEALTH_CHECK_PATH}" ]]; then
  curl -s "http://${HEALTH_CHECK_ADDRESS}:${HEALTH_CHECK_PORT}/${HTTP_HEALTH_CHECK_PATH}"
else
  echo -n | nc -q 0 "${HEALTH_CHECK_ADDRESS}" "${HEALTH_CHECK_PORT}"
fi
