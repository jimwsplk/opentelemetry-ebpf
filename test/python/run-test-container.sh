#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


docker pull localhost:5000/python-integration-tests

docker run --rm --tty \
  --env EBPF_NET_INTAKE_PORT="8000" \
  --env EBPF_NET_INTAKE_HOST="127.0.0.1" \
  --env EBPF_NET_AGENT_NAMESPACE="${EBPF_NET_AGENT_NAMESPACE}" \
  --env EBPF_NET_AGENT_CLUSTER="${EBPF_NET_AGENT_CLUSTER}" \
  --env EBPF_NET_AGENT_SERVICE="${EBPF_NET_AGENT_SERVICE}" \
  --env EBPF_NET_AGENT_HOST="${EBPF_NET_AGENT_HOST}" \
  --env EBPF_NET_AGENT_ZONE="${EBPF_NET_AGENT_ZONE}" \
  --env EBPF_NET_KERNEL_HEADERS_AUTO_FETCH="true" \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --network=host \
  localhost:5000/python-integration-tests \
  "$@"
