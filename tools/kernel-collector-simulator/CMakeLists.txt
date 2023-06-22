# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_tool_executable(
  kernel-collector-simulator
  SRCS
    main.cc
    kernel_collector_simulator.cc
    ingest_connection.cc
    ingest_json_reader.cc
  DEPS
    render_ebpf_net_cloud_collector
    render_ebpf_net_ingest_writer
    signal_handler
    aws-sdk-cpp
    reconnecting_channel
    connection_caretaker
    resource_usage_reporter
    config_file
    ip_address
    scheduling
    libuv-static
    args_parser
    system_ops
    aws_instance_metadata
    spdlog
    cgroup_parser
)

build_custom_docker_image(
  kernel-collector-simulator 
  OUT_DIR srv
  ARTIFACTS_OF
    kernel-collector-simulator
  DIRECTORIES
    run
)
