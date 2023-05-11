# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

build_custom_docker_image(
  http-test-client
  OUT_DIR srv
  FILES
    entrypoint.sh
    make_test_http_request.sh
  DIRECTORIES
    ../common
)
