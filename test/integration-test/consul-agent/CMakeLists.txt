# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

build_custom_docker_image(
  consul-agent
  OUT_DIR srv
  FILES
    entrypoint.sh
    check_is_alive.sh
  DIRECTORIES
    ../common
    consul.d
)
