#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -xe

if [[ -z "${SERVICE_BIND_ADDRESS}" ]]; then
  if [[ -n "${SERVICE_BIND_INTERFACE}" ]]; then
    export SERVICE_BIND_ADDRESS="`./common/get_interface_ip.sh "${SERVICE_BIND_INTERFACE}"`"
  else
    echo 'expected environment variable `SERVICE_BIND_ADDRESS` with an address'
    echo 'or `SERVICE_BIND_INTERFACE` with an interface to bind the service to'
    exit 1
  fi
fi

sed -e "s/HTTP_RESPONSE_CODE/${HTTP_RESPONSE_CODE}/g" \
  /srv/nginx.conf.template \
  > /etc/nginx/nginx.conf

service nginx restart &

./common/register-service.sh \
  "http-${HTTP_RESPONSE_CODE}-test-server" \
  "${INCOMING_PORT}" \
  "${SERVICE_BIND_ADDRESS}" \
  "${HEALTH_CHECK_PORT}"
