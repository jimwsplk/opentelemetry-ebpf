#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


cmd="clang-format-11"
if ! command -v ${cmd}
then
  echo "ERROR: requires ${cmd}"
  exit 1
fi

# Apply clang-format to C, C++ and protobuf source files
for src in "$@"
do
case "${src}" in *.c | *.cc | *.h | *.proto | *.inl)
  if ! ${cmd} -style=file -verbose -i "${src}"; then
    echo "Error running clang-format"
    exit 1
  fi
  ;;
*)
  echo "Ignoring ${src}"
  ;;
esac
done
