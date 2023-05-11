# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_executable(
  otlp-http-metrics-client
    otlp-http-metrics-client.cc
)
target_link_libraries(
  otlp-http-metrics-client
    libuv-static
    logging
    tcp_channel
    upstream_connection
)
