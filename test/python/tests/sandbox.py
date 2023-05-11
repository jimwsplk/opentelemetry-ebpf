# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.collector.tester import kernel_collector_tester
from flowmill.render.app import ingest
from flowmill.render.span import span_container
from flowmill.render.spans.tracked_process import tracked_process
from flowmill.render.stream import message_stream_filterer
from flowmill.render.message import message_fields_filter

dump = None
with kernel_collector_tester(debug=True) as tester:
    lookbusy = tester.add_workload(
        image='lookbusy',
        args=['--cpu-mode=fixed', '--ncpus=2', '--cpu-util=70'],
        duration=5, delay=5, debug=True
    )
    dump = tester.run(args=['--enable-cpu-mem-io'], ingest_dump=True)

def test_sandbox():
    filters = message_stream_filterer(
        fixed_filter_set={
            "default cpu period": {
                "container_resource_limits": message_fields_filter({"cpu_period": 100000}, min=1),
            },
            **ingest.message_fixed_filters.kernel_headers(),
        },
    )

    tracked_processes = span_container(span_type=tracked_process, select={
        "cpu": {"command": "lookbusy"},
    })

    filters.replay(dump.ingest, consumers=[tracked_processes.consumers()], debug=True)

    print("LIVE SPANS:", len(tracked_processes.spans))

    lookbusy_spans = tracked_processes.retrieve("cpu", live=True)
    print("LOOKBUSY SPANS(", len(lookbusy_spans), "):", lookbusy_spans)

    assert filters.succeeded()
