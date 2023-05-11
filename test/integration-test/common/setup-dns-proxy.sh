#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

set -e

if [[ -z "${CONSUL_DNS_ADDRESS}"  ]]; then
  CONSUL_DNS_ADDRESS="`./common/get_default_gateway.sh`"
fi

cat > /etc/dnsmasq.conf <<EOF
no-resolv
server=${CONSUL_DNS_ADDRESS}
EOF

service dnsmasq restart
systemctl enable dnsmasq
