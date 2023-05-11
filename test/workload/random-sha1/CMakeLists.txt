# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

lint_shell_script_bundle(
  workload-random-sha1
  SOURCES
    entrypoint.sh
)

build_custom_docker_image(
  workload-random-sha1
  OUT_DIR srv
  OUTPUT_OF
    workload-random-sha1
  DEPENDENCY_OF
    workload
)
