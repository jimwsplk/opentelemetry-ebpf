# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

lint_python_bundle(
  workload-sockets-python
  SOURCES
    sockets.py
)

build_custom_docker_image(
  workload-sockets
  OUT_DIR srv
  OUTPUT_OF
    workload-sockets-python
  DEPENDENCY_OF
    workload
)
