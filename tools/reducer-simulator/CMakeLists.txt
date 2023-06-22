# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_tool_executable(
  sim-reducer
  SRCS
    reducer.cc
    generator.cc
    random.cc
  DEPS
    render_ebpf_net_aggregation
    metrics_output
    signal_handling
    libuv-static
    args_parser
    logging
)

build_custom_docker_image(
  sim-reducer
  OUT_DIR srv
  ARTIFACTS_OF
    sim-reducer
  FILES
    example-dimensions.yaml
)
