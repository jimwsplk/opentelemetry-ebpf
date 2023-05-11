#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


set -e

# Using echo here right now out of paranoia... script is to show you what you should run,
# not to actually do it.  Kinda want deployments managed from a CI server (or something)
# rather than my laptop anyway...
namespace="integration-test"
echo "Run this, and if you like the output, remove diff from the command:" >&2
echo helm diff upgrade "$namespace" ./ -f values.yaml --namespace "$namespace"
