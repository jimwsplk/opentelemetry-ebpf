#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


if [[ -z "${HEALTH_CHECK_PORT}" ]] || [ "${HEALTH_CHECK_PORT}" -le 0 ] 2> /dev/null; then
  echo "expected environment variable HEALTH_CHECK_PORT with positive integer"
  exit 1
fi

if [[ "${USE_ECS_HTTP_TEST_CLIENT}" == "true" ]]; then
  ./common/setup-dns-proxy.sh
fi

./common/start-health-check-endpoint.sh

# start client
./make_test_http_request.sh "$@"
