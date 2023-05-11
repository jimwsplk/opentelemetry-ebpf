# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_executable(
  alloc-test
  main.cc
)
target_link_libraries(
  alloc-test
  fastpass_util
)
