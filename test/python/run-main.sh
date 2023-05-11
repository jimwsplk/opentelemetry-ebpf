#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


if [ $# -eq 0 ]; then
    echo "No arguments provided"
    printf "Available arguments are the following:\nsandbox,\nhttp-code,\nkernel-headers\notlp\n"
    exit 1
fi

if [[ $1 == "sandbox" ||  $1 == "kernel-headers"  ||  $1 == "http-code" ]]; then
     nohup bash run-mocked-pipeline-server.sh > mock.output 2>&1&
     nohup bash run-test-container.sh $1 > test.output  2>&1 &
elif [[ $1 == "otlp" ]]; then
     echo " Starting otlp test "
     nohup bash run-test-container.sh $1 > test.output  2>&1 &
else
     echo " No valid arguments provided! "
     printf "Available arguments are the following:\nsandbox,\nhttp-code,\nkernel-headers\notlp\n"
     exit 1
fi
