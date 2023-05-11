#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


if [[ "$#" -eq 0 ]]; then
  echo "retrieves the ECR image tag deployed to a given pod"
  echo
  echo "usage: $0 pod_name [namespace [container]]"
  echo
  echo "e.g.:"
  echo
  echo "  $0 staging-flowtune-server-7b56bd8bc7-l2h9q"
  echo "  $0 flowmill-k8s-agent-j9rqx flowmill"
  echo "  $0 flowmill-k8s-collector-74665fb696-b5qz9 flowmill flowmill-k8s-relay"
  exit 1
fi

set -e

pod_name="$1"; shift

kubectl_args=("${pod_name}")

if [[ -n "$1" ]]; then
  namespace="$1"; shift
  kubectl_args=("-n" "${namespace}" "${kubectl_args[@]}")
fi

declare -a container_selector
jq_query=(".spec.containers[]")
if [[ -n "$1" ]]; then
  container="$1"; shift
  jq_query+=("| select(.name | contains(\"${container}\"))")
fi
jq_query+=("| .image")

kubectl get pod "${kubectl_args[@]}" -ojson \
  | jq -r "${jq_query[*]}" \
  | cut -d : -f 2
