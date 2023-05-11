#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -e

if [[ -z "${CONSUL_API_ADDRESS}"  ]] && [[ -n "${CONSUL_API_INTERFACE}" ]]; then
  CONSUL_API_ADDRESS="`./common/get_interface_ip.sh "${CONSUL_API_INTERFACE}"`"
fi

curl "${CONSUL_API_ADDRESS}:8500"
