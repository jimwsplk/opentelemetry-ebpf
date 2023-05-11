# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5.1)

project(GRPC_OTLP_POC C CXX)

set(CMAKE_CXX_STANDARD 20)

include_directories(${CMAKE_INSTALL_PREFIX})

include(openssl)

foreach(_target
  logs)
  add_executable(otlp-grpc-${_target}-client-test "otlp-grpc-${_target}-client-test.cc")
  target_link_libraries(otlp-grpc-${_target}-client-test
    OpenSSL::Crypto
    OpenSSL::SSL
    logging
    otlp_grpc_${_target}_client)
endforeach()

