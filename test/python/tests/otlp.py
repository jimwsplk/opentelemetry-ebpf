# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.reducer.tester import otlp_reducer_tester

result = None
with otlp_reducer_tester() as tester:
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
        # prometheus forbids "." in their labels and metric names
        # but we use "." in our otlp names.  normalize _ to .
        prom_comp_line=prom_line.replace("_", ".")
        otlp_comp_line=otlp_line.replace("_", ".")

        assert prom_comp_line == otlp_comp_line, "{} does not match {}".format(prom_comp_line, otlp_comp_line)

