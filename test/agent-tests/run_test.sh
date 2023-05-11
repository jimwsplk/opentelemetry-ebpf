#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


EBPF_NET_SRC="${EBPF_NET_SRC:-$(git rev-parse --show-toplevel)}"
BUILD_DIR="$EBPF_NET_SRC/../benv-out"
CONFIG_DIR="$EBPF_NET_SRC/test/agent-tests"

if [[ "$#" -lt 1 ]]; then
    echo "Must specify test name"
    exit 1
fi

testname="$1"
shift

while [[ "$#" -gt 0 ]]; do
    arg="$1"; shift
    case "${arg}" in
      --nospin)
        nospin=true; shift
        ;;
      *)
        echo "ERROR: unknown argument '${arg}'"
        exit 1
        ;;
    esac
done

# Terminate agent and server when this script exits
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

export SSL_CERT_DIR=/etc/ssl/certs

# Remove old data
rm -rf promdata

# Clear local DNS cache
systemd-resolve --flush-caches

echo "Starting stunnel..."
stunnel $CONFIG_DIR/dev-stunnel.conf &
sleep 1

echo "Starting server..."
$BUILD_DIR/reducer/reducer-static $DEBUG_FLAGS --authz-public-key="/etc/flowmill/authz-token-public.pem" --log-console $EXTRA_SERVER_ARGS --enable-percentile-latencies --port=8000 --prom=127.0.0.1:7010 --internal-prom=127.0.0.1:7001 --allowed-tenant-id=2 &>/tmp/server-1.log &
sleep 1

echo "Starting prometheus..."
prometheus --storage.tsdb.path="$CONFIG_DIR/promdata" --web.listen-address="127.0.0.1:9090" --config.file=$CONFIG_DIR/dev-prometheus.yml &>/tmp/prometheus-1.log &

export EBPF_NET_INTAKE_HOST="localhost"
export EBPF_NET_INTAKE_PORT="8001"
export EBPF_NET_OVERRIDE_AGENT_CLUSTER="agent-1"

echo "Starting agent..."
$BUILD_DIR/collector/kernel/kernel-collector $DEBUG_FLAGS --log-console --log-whitelist-all --debug $EXTRA_AGENT_ARGS &>/tmp/agent-1.log &
sleep 30

echo "Running ${testname}..."
"./${testname}"
sleep 1

echo "Done."
if [[ -z ${nospin} ]]; then
    echo "Press CTRL-C to exit."
    while true; do sleep 1; done
fi
