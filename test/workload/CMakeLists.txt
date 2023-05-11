# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

add_custom_target(workload-docker)
add_custom_target(workload-docker-registry)

add_dependencies(python-integration-tests-docker workload-docker)
add_dependencies(python-integration-tests-docker-registry workload-docker-registry)
add_subdirectory(lookbusy)

add_subdirectory(http-code)
add_subdirectory(sockets)

