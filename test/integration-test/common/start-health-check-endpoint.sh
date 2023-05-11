#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


if [[ -z "${HEALTH_CHECK_PORT}" ]] || [ "${HEALTH_CHECK_PORT}" -le 0 ] 2> /dev/null; then
  echo "expected environment variable HEALTH_CHECK_PORT with positive integer"
  exit 1
fi

nohup ncat -p "${HEALTH_CHECK_PORT}" \
  -kl -c ./common/health_check_response.sh \
  &
