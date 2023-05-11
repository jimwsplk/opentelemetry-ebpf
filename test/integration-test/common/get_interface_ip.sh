#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -e

if which ip > /dev/null 2> /dev/null; then
  for interface in "$@"; do
    ip addr show "${interface}" \
      | grep inet \
      | cut -d / -f 1 \
      | awk '{print $2}' \
      | head -n 1
  done
elif which ifconfig > /dev/null 2> /dev/null; then
  for interface in "$@"; do
    ifconfig "${interface}" \
      | grep inet \
      | awk '{print $2}' \
      | head -n 1
  done
else
  echo "unable to list network interfaces" >&2
  exit 1
fi
