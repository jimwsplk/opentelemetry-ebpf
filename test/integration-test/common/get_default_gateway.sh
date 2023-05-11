#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -e

if which ip > /dev/null 2> /dev/null; then
  ip route show | grep default | sed -e 's/^default via \([0-9\.]*\).*$/\1/g'
else
  echo "unable to get default gateway" >&2
  exit 1
fi
