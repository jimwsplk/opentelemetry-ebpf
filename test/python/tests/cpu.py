# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.collector.tester import kernel_collector_tester
from flowmill.render.stream import filter_message_stream
from flowmill.render.message import message_fields_filter

dump = None
with kernel_collector_tester() as tester:
    dump = tester.run(args=['--enable-cpu-mem-io'], ingest_dump=True)

def test_default_cpu_period():
    assert [] == filter_message_stream(
        dump.ingest,
        fixed_filter_set={
            "default cpu period": {
                "container_resource_limits": message_fields_filter({"cpu_period": 100000}, min=1),
            },
        },
    )
