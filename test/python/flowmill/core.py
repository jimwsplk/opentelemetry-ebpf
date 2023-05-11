# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

import os

def default_debug_setting():
    debug = os.getenv('EBPF_NET_TEST_DEBUG', False)
    return debug.lower() in ['true', 'yes', '1'] if type(debug) == str else debug
