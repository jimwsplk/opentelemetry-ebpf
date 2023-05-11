# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.reducer.tester import otlp_reducer_tester

result = None
with otlp_reducer_tester() as tester:
    #DSB TODO when ingest playback is finished, call the tester twice,
    #once for prom, once for otlp
    #with a specific ingest file.  then compare the results

    result = tester.run()

def test_otlp():
    prom_lines_with_type = result.prom.splitlines()
    prom_lines = []
    for prom_line in prom_lines_with_type:
        if prom_line.startswith("#"):
            continue
        prom_lines.append(prom_line)

    otlp_lines = result.otlp.splitlines()

    assert len(prom_lines) == len(otlp_lines)

    for (prom_line, otlp_line) in zip(prom_lines, otlp_lines): 
        prom_metric_idx=prom_line.index("{")
        prom_metric_name=prom_line[:prom_metric_idx]
        prom_metric_name=prom_metric_name.replace("_", ".")
        prom_comp_line=prom_metric_name+prom_line[prom_metric_idx:]

        otlp_metric_idx=otlp_line.index("{")
        otlp_metric_name=otlp_line[:otlp_metric_idx]
        otlp_metric_name=otlp_metric_name.replace("_", ".")

        otlp_comp_line=otlp_metric_name+otlp_line[otlp_metric_idx:]

        assert prom_comp_line == otlp_comp_line

