#!/bin/bash -xe
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


HTTP_CODE_LIST="200 204 300 302 401 500 501 502"

for code in $HTTP_CODE_LIST; do
  sleep 1
  curl "http://httpstat.us/$code"
done
