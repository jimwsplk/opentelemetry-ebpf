# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_subdirectory(flowmill)

lint_shell_script_bundle(
  python-integration-tests-scripts
  SOURCES
    entrypoint.sh
)

build_custom_docker_image(
  python-integration-tests
  OUT_DIR srv
  OUTPUT_OF
    python-integration-tests-scripts
  ARTIFACTS_OF
    bpf_wire_to_json
    intake_wire_to_json
  DIRECTORIES
    flowmill
    tests
)
