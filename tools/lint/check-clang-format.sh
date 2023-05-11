#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


CLANG_FORMAT_VERSION="clang-format-11"
if ! command -v ${CLANG_FORMAT_VERSION}
then
  echo "ERROR: requires ${CLANG_FORMAT_VERSION}"
  exit 1
fi

RC=0
CMD="${CLANG_FORMAT_VERSION} -Werror --dry-run -style=file"
function check_file
{
  if ! ${CMD} $1
  then
    RC=1
  fi
}

# Check that C and C++ source files are properly clang-formatted
FILES=$(find ./geoip ./server ./test ./tools \
	-type f                              \
	\( -name "*.c"                       \
	-o -name "*.cc"                      \
	-o -name "*.h"                       \
	-o -name "*.inl" \)                  \
	-print)

for FILE in ${FILES}
do
  check_file ${FILE}
done

exit ${RC}
