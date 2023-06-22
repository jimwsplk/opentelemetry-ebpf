#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

docker_args=( \
  --env EBPF_NET_INTAKE_HOST="127.0.0.1"
  --env EBPF_NET_INTAKE_PORT="8000"
  --privileged
  --network=host
)

app_args=( \
  --log-console
  --debug
  --ingest-file=/srv/run/ingest.json
)

docker pull localhost:5000/kernel-collector-simulator

export container_id="$( \
  docker create -t --rm "${docker_args[@]}" \
    localhost:5000/kernel-collector-simulator "${app_args[@]}"\
)"

function cleanup_docker {
  docker kill "${container_id}" || true
  docker container prune --force || true
  docker volume prune --force || true
  docker image prune --force || true
}
trap cleanup_docker SIGINT

docker start -i "${container_id}"
cleanup_docker
