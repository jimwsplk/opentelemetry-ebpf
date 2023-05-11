# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.collector.tester import kernel_collector_tester
from flowmill.render.app import ingest
from flowmill.render.stream import filter_message_stream

dump = None
with kernel_collector_tester() as tester:
    dump = tester.run(ingest_dump=True)

def test_auth_protocol():
    assert [] == filter_message_stream(
        dump.ingest,
        order_filter_set={
            **ingest.message_order_filters.authentication(collector_type=1),
        },
    )
