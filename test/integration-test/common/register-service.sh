#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -x

if [[ -z "${CONSUL_PUBLISH_ADDRESS}"  ]]; then
  CONSUL_PUBLISH_ADDRESS="`./common/get_default_gateway.sh`"
fi

if [[ -z "${CONSUL_PUBLISH_PORT}" ]]; then
  CONSUL_PUBLISH_PORT="8500"
fi

max_retries="10"
retry_interval="10"
re_register_interval="60"

service_name="$1"; shift
service_port="$1"; shift
health_check_address="$1"; shift
health_check_port="${service_port}"
if [[ -n "$1" ]]; then health_check_port="$1"; shift; fi
health_check_interval="30s"
if [[ -n "$1" ]]; then health_check_interval="$1"; shift; fi
health_check_timeout="1s"
if [[ -n "$1" ]]; then health_check_timeout="$1"; shift; fi

declare -A health_check_info=( \
  ["Interval"]="${health_check_interval}"
  ["Timeout"]="${health_check_timeout}"
)

if [[ -n "${HTTP_HEALTH_CHECK_PATH}" ]]; then
  health_check_info["HTTP"]="http://${health_check_address}:${health_check_port}/${HTTP_HEALTH_CHECK_PATH}"
else
  health_check_info["TCP"]="${health_check_address}:${health_check_port}"
fi

health_check_payload=""
for key in "${!health_check_info[@]}"; do
  if [[ -n "${health_check_payload}" ]]; then
    health_check_payload+=","
  fi
  value="${health_check_info[${key}]}"
  health_check_payload+="\"${key}\":\"${value}\""
done
health_check_payload="{${health_check_payload}}"

declare -A service_info=( \
  ["Name"]="${service_name}"
  ["Port"]="${service_port}"
  ["Check"]="${health_check_payload}"
)

curl_payload=""
for key in "${!service_info[@]}"; do
  if [[ -n "${curl_payload}" ]]; then
    curl_payload+=","
  fi
  value="${service_info[${key}]}"
  curl_payload+="\"${key}\":\"${value}\""
done
curl_payload="{${curl_payload}}"

while true; do
  for (( attempt=0; attempt++ < ${max_retries}; )); do
    curl_output="`curl -w "%{http_code}" -XPUT "http://${CONSUL_PUBLISH_ADDRESS}:${CONSUL_PUBLISH_PORT}/v1/agent/service/register?replace-existing-checks=1" -d "${curl_payload}" 2>&1`"
    curl_status="$?"
    if [[ "${curl_status}" -eq 0 ]]; then
      echo "successfully registered service '${service_name}' at `date -R`"
      break
    else
      echo "service '${service_name}' registration failed (status=${curl_status}), retrying in ${retry_interval}s:"
      echo "  payload: ${curl_payload}"
      echo "  output: ${curl_output}"
      if [[ "${attempt}" == "${max_retries}" ]]; then
        echo "failed to register service '${service_name}' after maximum number of attempts..."
      else
        sleep "${retry_interval}"
      fi
    fi
  done

  echo "re-registering service '${service_name}' in ${re_register_interval}s"
  sleep "${re_register_interval}"
done
