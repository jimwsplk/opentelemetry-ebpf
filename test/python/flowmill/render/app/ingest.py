# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.render.message import message_fields_filter

import os

class message_fixed_filters:
    @staticmethod
    def kernel_headers():
        """
        Ensures that kernel headers have been properly fetched.
        """

        return {
            "kernel header fetching": {
                "kernel_headers_source": message_fields_filter(
                    {"source": [1, 2, 4]},
                    min=1,
                    max=1,
                ),
            }
        }

class message_order_filters:
    """
    A list of reusable message filters to be used  with `order_filter_set` from
    `flowmill.render.stream.message_stream_filterer`.
    """

    @staticmethod
    def authentication(collector_type):
        """
        Ensures that the authentication protocol proceeds in the correct order.
        """

        return {
            "authentication messages order": [
                {"version_info": {}},
                {"authz_authenticate": {"collector_type": collector_type}},
                {"os_info": {"os": 1, "kernel_version": os.uname().release}},
                {"report_cpu_cores": {}},
                {"cloud_platform": {}},
                {"metadata_complete": {}},
                {"bpf_compiled": {}},
            ],
        }

