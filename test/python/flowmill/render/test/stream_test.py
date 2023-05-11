#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


from flowmill.render.stream import filter_message_stream

import io
import os

def test_filter_message_stream():
    assert [] == filter_message_stream(
            io.BytesIO(b'[\
    {"name":"version_info","data":{"major":0,"minor":8,"build":2928}},\
    {"name":"authz_authenticate","data":{"token":"omitted","collector_type":1,"hostname":"myhost"}},\
    {"name":"os_info","data":{"os":1,"flavor":1,"kernel_version":"5.7.0-2-amd64"}},\
    {"name":"kernel_headers_source","data":{"source":2}},\
    {"name":"set_config_label","data":{"key":"environment","value":"myenv"}},\
    {"name":"set_config_label","data":{"key":"host","value":"myhost"}},\
    {"name":"set_config_label","data":{"key":"service","value":"mysvc"}},\
    {"name":"set_config_label","data":{"key":"zone","value":"myzone"}},\
    {"name":"set_config_label","data":{"key":"__kernel_version","value":"5.7.0-2-amd64"}},\
    {"name":"cloud_platform","data":{"cloud_platform":0}},\
    {"name":"set_node_info","data":{"az":"","role":"","instance_id":"myhost","instance_type":""}},\
    {"name":"metadata_complete","data":{"time":0}},\
    {"name":"bpf_compiled","data":{}}\
        ]'),
        order_filter_set={
            "kernel header fetching": [
                {"kernel_headers_source": {"source": [2, 4]}},
            ]
        }
    )

    assert [] == filter_message_stream(
        io.BytesIO(b'[\
    {"name":"version_info","data":{"major":0,"minor":8,"build":2928}},\
    {"name":"authz_authenticate","data":{"token":"omitted","collector_type":1,"hostname":"myhost"}},\
    {"name":"os_info","data":{"os":1,"flavor":1,"kernel_version":"5.7.0-2-amd64"}},\
    {"name":"kernel_headers_source","data":{"source":4}},\
    {"name":"set_config_label","data":{"key":"environment","value":"myenv"}},\
    {"name":"set_config_label","data":{"key":"host","value":"myhost"}},\
    {"name":"set_config_label","data":{"key":"service","value":"mysvc"}},\
    {"name":"set_config_label","data":{"key":"zone","value":"myzone"}},\
    {"name":"set_config_label","data":{"key":"__kernel_version","value":"5.7.0-2-amd64"}},\
    {"name":"cloud_platform","data":{"cloud_platform":0}},\
    {"name":"set_node_info","data":{"az":"","role":"","instance_id":"myhost","instance_type":""}},\
    {"name":"metadata_complete","data":{"time":0}},\
    {"name":"bpf_compiled","data":{}}\
        ]'),
        order_filter_set={
            "kernel header fetching": [
                {"kernel_headers_source": {"source": [2, 4]}},
            ]
        }
    )

    assert ["kernel header fetching"] == filter_message_stream(
        io.BytesIO(b'[\
    {"name":"version_info","data":{"major":0,"minor":8,"build":2928}},\
    {"name":"authz_authenticate","data":{"token":"omitted","collector_type":1,"hostname":"myhost"}},\
    {"name":"os_info","data":{"os":1,"flavor":1,"kernel_version":"5.7.0-2-amd64"}},\
    {"name":"kernel_headers_source","data":{"source":1}},\
    {"name":"set_config_label","data":{"key":"environment","value":"myenv"}},\
    {"name":"set_config_label","data":{"key":"host","value":"myhost"}},\
    {"name":"set_config_label","data":{"key":"service","value":"mysvc"}},\
    {"name":"set_config_label","data":{"key":"zone","value":"myzone"}},\
    {"name":"set_config_label","data":{"key":"__kernel_version","value":"5.7.0-2-amd64"}},\
    {"name":"cloud_platform","data":{"cloud_platform":0}},\
    {"name":"set_node_info","data":{"az":"","role":"","instance_id":"myhost","instance_type":""}},\
    {"name":"metadata_complete","data":{"time":0}},\
    {"name":"bpf_compiled","data":{}}\
        ]'),
        order_filter_set={
            "kernel header fetching": [
                {"kernel_headers_source": {"source": [2, 4]}},
            ]
        }
    )

