#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


function print_help {
  echo "usage: $0 response_code_1 [reponse_code_2 [... [response_code_N]]]"
}

function build_k8s_url {
  if [[ -z "$2" ]]; then
    echo "host required for http-$1-test-server" >&2
    exit 1
  fi

  if [[ -z "$3" ]] || [ "$3" -ne "$3" ] 2> /dev/null; then
    echo "integer port required http-$1-test-server" >&2
    exit 1
  fi

  echo "http://$2:$3/${HTTP_TEST_REQUEST_PATH}"
}

if [[ "$#" -eq 0 ]]; then
  print_help
  exit 1
fi

if [[ -z "${HTTP_CLIENT_BATCH_DELAY}" ]]; then HTTP_CLIENT_BATCH_DELAY="1"; fi
if [[ -z "${HTTP_CLIENT_QUERY_REPS}" ]]; then HTTP_CLIENT_QUERY_REPS="10"; fi

batch_count_checkpoint="10" # TODO: MAKE IT 1000
declare -a urls

while [[ "$#" -gt 0 ]]; do
  arg="$1"; shift

  case "${arg}" in
    [0-9][0-9]*)
      if [[ "${USE_ECS_HTTP_TEST_CLIENT}" == "true" ]]; then
        urls+=("http://http-${arg}-test-server.service.consul:51${arg}/${HTTP_TEST_REQUEST_PATH}")
      else
        host_var_name="INTEGRATION_TEST_HTTP_${arg}_TEST_SERVER_SERVICE_HOST"
        port_var_name="INTEGRATION_TEST_HTTP_${arg}_TEST_SERVER_SERVICE_PORT"
        urls+=("$(build_k8s_url "${arg}" "${!host_var_name}" "${!port_var_name}")")
      fi
      ;;

    *)
      echo "unsupported http server response code: '${arg}'"
      exit 1
      ;;
  esac
done

if [[ "${#urls[@]}" -lt 1 ]]; then
  echo "ERROR: at least one response code must be specified"
  exit 1
fi

echo "batch reps: ${HTTP_CLIENT_QUERY_REPS}, batch delay: ${HTTP_CLIENT_BATCH_DELAY}s, urls to query:"
for url in "${urls[@]}"; do
  echo "- ${url}"
done
echo

batch_count=0
while true; do
  for url in "${urls[@]}"; do
    for ((i=0; i < ${HTTP_CLIENT_QUERY_REPS}; ++i)); do
      (curl --silent --output /dev/null "${url}" \
        || echo "failed to fetch ${url} on iteration ${i} batch ${batch_count}"
      ) &
    done
  done
  wait

  sleep "${HTTP_CLIENT_BATCH_DELAY}"

  if [[ $((batch_count % batch_count_checkpoint)) -eq 0 ]]; then
    echo "checkpoint: batch ${batch_count}"
  fi

  batch_count=$((batch_count + 1))
done
