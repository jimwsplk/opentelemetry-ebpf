#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


# downloads clang-format into ~/bin/clang-format



if [[ "$OSTYPE" == "linux-gnu" ]]; then
    # linux
    source /etc/lsb-release

    if [[ "$DISTRIB_ID" == "LinuxMint" ]]; then
	URL="http://releases.llvm.org/7.0.1/clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-16.04.tar.xz"
	ARCHIVE_PATH="clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-16.04/bin/clang-format"
    fi

    if [[ "$DISTRIB_ID" == "Ubuntu" ]] && [[ "$DISTRIB_RELEASE" == "18.04" ]]; then
	URL="http://releases.llvm.org/7.0.1/clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-18.04.tar.xz"
	ARCHIVE_PATH="clang+llvm-7.0.1-x86_64-linux-gnu-ubuntu-18.04/bin/clang-format"
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    URL="http://releases.llvm.org/7.0.0/clang+llvm-7.0.0-x86_64-apple-darwin.tar.xz"
    ARCHIVE_PATH="clang+llvm-7.0.0-x86_64-apple-darwin/bin/clang-format"
fi

mkdir -p $HOME/bin
curl -L "$URL" | tar -xvJC $HOME/bin/ "${ARCHIVE_PATH}" --strip 2
