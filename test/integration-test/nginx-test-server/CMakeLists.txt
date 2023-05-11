# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

build_custom_docker_image(
  nginx-test-server
  OUT_DIR srv
  FILES
    entrypoint.sh
    nginx.conf.template
  DIRECTORIES
    ../common
    data
)
