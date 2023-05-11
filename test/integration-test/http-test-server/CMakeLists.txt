# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

build_custom_docker_image(
  http-200-test-server
  ARGS
    HTTP_RESPONSE_CODE=200
    INCOMING_PORT=51200
  DEPENDS
    nginx-test-server-docker
)

build_custom_docker_image(
  http-404-test-server
  ARGS
    HTTP_RESPONSE_CODE=404
    INCOMING_PORT=51404
  DEPENDS
    nginx-test-server-docker
)

build_custom_docker_image(
  http-500-test-server
  ARGS
    HTTP_RESPONSE_CODE=500
    INCOMING_PORT=51500
  DEPENDS
    nginx-test-server-docker
)
