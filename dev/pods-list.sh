#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


if [[ "$#" -eq 0 ]]; then
  echo "lists pods for a given k8s app"
  echo
  echo 'the `app.kubernetes.io/name` label is used to filter k8s apps'
  echo
  echo "usage: $0 k8s_app_name [namespace]"
  echo
  echo "e.g.:"
  echo
  echo "$0 flowtune-server"
  echo "    - lists pods for the pipeline server"
  echo
  echo "$0 flowmill-k8s-agent"
  echo "    - lists pods for the kernel collector"
  exit 1
fi

app_name="$1"; shift

declare -a kubectl_args
if [[ -n "$1" ]]; then
  namespace="$1"; shift
  kubectl_args+=(-n "$namespace")
fi

jq_query=(
  '.items[]'
  '| select(.metadata.labels."app.kubernetes.io/name"'
  "| contains(\"${app_name}\"))"
  '| .metadata.name'
)

kubectl "${kubectl_args[@]}" get pods -ojson \
  | jq -r "${jq_query[*]}"
