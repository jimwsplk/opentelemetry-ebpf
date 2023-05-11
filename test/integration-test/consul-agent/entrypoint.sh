#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -xe

if [[ -z "${CONSUL_DATACENTER_NAME}" ]]; then
  CONSUL_DATACENTER_NAME="flowmill_test_datacenter"
fi

if [[ -z "${CONSUL_NODE_NAME}" ]]; then
  CONSUL_NODE_NAME="`uname -n`"
fi

if [[ -z "${CONSUL_ROOT_DIR}" ]]; then
  CONSUL_ROOT_DIR="`pwd`"
fi

if [[ -z "${CONSUL_RETRY_INTERVAL}" ]]; then
  CONSUL_RETRY_INTERVAL="5s"
fi

if [[ -z "${CONSUL_BIND_ADDRESS}"  ]] && [[ -n "${CONSUL_BIND_INTERFACE}" ]]; then
  CONSUL_BIND_ADDRESS="`./common/get_interface_ip.sh "${CONSUL_BIND_INTERFACE}"`"
fi

if [[ -z "${CONSUL_API_ADDRESS}"  ]] && [[ -n "${CONSUL_API_INTERFACE}" ]]; then
  CONSUL_API_ADDRESS="`./common/get_interface_ip.sh "${CONSUL_API_INTERFACE}"`"
fi

if [[ -z "${CONSUL_BIND_ADDRESS}" ]]; then
  echo "need environment variables CONSUL_BIND_ADDRESS with the ip address, or" \
    " CONSUL_BIND_INTERFACE with the interface name, to bind to for cluster communication"
  exit 1
fi

if [[ -z "${CONSUL_API_ADDRESS}"  ]]; then
  CONSUL_API_ADDRESS="${CONSUL_BIND_ADDRESS}"
fi

consul_args=( \
  -data-dir="${CONSUL_ROOT_DIR}/data"
  -config-dir="${CONSUL_ROOT_DIR}/consul.d"
  -datacenter="${CONSUL_DATACENTER_NAME}"
  -node="${CONSUL_NODE_NAME}"
  -bind="${CONSUL_BIND_ADDRESS}"
  -client="${CONSUL_API_ADDRESS}"
  -server
  -rejoin
  -retry-interval="${CONSUL_RETRY_INTERVAL}"
  -dns-port=53
)

#bootstrapped="false"
expected_node_count=1
if [[ -n "${CONSUL_BOOTSTRAP_NODES}" ]]; then
  for node in ${CONSUL_BOOTSTRAP_NODES}; do
    if [[ "${node}" != "${CONSUL_BIND_ADDRESS}" ]] && echo -n | nc -w 1 "${node}" 22; then
      consul_args+=(-retry-join="${node}")
#      bootstrapped="true"
      expected_node_count=$((expected_node_count + 1))
    fi
  done
fi

#if [[ "${bootstrapped}" == "false" ]]; then
#  consul_args+=(-bootstrap)
#fi
consul_args+=(-bootstrap-expect "${expected_node_count}")

if [[ "${CONSUL_USE_SYSLOG}" == "true" ]]; then
  consul_args+=(-syslog)
fi

exec consul agent "${consul_args[@]}" "$@"
