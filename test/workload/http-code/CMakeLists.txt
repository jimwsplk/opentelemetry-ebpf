# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

lint_shell_script_bundle(
  workload-http-code
  SOURCES
    entrypoint.sh
)

build_custom_docker_image(
  workload-http-code
  OUT_DIR srv
  OUTPUT_OF
    workload-http-code
  DEPENDENCY_OF
    workload
)
