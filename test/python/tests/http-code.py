# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.collector.tester import kernel_collector_tester
from flowmill.render.stream import filter_message_stream

dump = None
with kernel_collector_tester() as tester:
    dump = tester.run(ingest_dump=True)

# see workload/http-code
def test_http_code():
    assert [] == filter_message_stream(
        dump.ingest,
        fixed_filter_set={
            "http response 200": [
                {"http_response": {"code": 200}},
            ],
            "http response 204": [
                {"http_response": {"code": 204}},
            ],
            "http response 300": [
                {"http_response": {"code": 300}},
            ],
            "http response 302": [
                {"http_response": {"code": 302}},
            ],
            "http response 401": [
                {"http_response": {"code": 401}},
            ],
            "http response 500": [
                {"http_response": {"code": 500}},
            ],
            "http response 501": [
                {"http_response": {"code": 501}},
            ],
            "http response 502": [
                {"http_response": {"code": 502}},
            ],
        },
    )
