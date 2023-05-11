# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

unpack_make_autotools_project(
  lookbusy
  lookbusy-1.4.tar.gz
  BYPRODUCTS
    lookbusy
)

build_custom_docker_image(
  lookbusy
  OUT_DIR srv
  OUTPUT_OF
    lookbusy
  DEPENDENCY_OF
    workload
)
