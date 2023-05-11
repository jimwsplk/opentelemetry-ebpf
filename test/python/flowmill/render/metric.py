# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

class metric:
    pass

class value(metric):
    def __init__(self):
        self.value = None

    def __call__(self, value, hits):
        self.value = value

    def __repr__(self):
        import json

        return json.dumps({
            'value': self.value,
        })

class counter(metric):
    def __init__(self):
        self.value = 0

    def __call__(self, value, hits):
        self.value = value

    def __repr__(self):
        import json

        return json.dumps({
            'value': self.value,
        })

class monotonic_counter(metric):
    def __init__(self):
        self.value = None

    def __call__(self, value, hits):
        assert self.value is None or value >= self.value
        self.value = value

    def __repr__(self):
        import json

        return json.dumps({
            'value': self.value,
        })

class gauge(metric):
    def __init__(self):
        self.min = None
        self.max = None
        self.value = 0
        self.sum = 0
        self.average = 0

    def __call__(self, value, hits):
        if self.min is None or value < self.min: self.min = value
        if self.max is None or value > self.max: self.max = value
        self.value = value
        self.sum += value
        self.average = self.sum / hits

    def __repr__(self):
        import json

        return json.dumps({
            'min': self.min,
            'max': self.max,
            'value': self.value,
            'sum': self.sum,
            'average': self.average,
        })

class rate(metric):
    def __init__(self):
        self.rate = 0
        self.sum = 0

    def __call__(self, value, hits):
        self.rate = value
        self.sum += value

    def __repr__(self):
        import json

        return json.dumps({
            'rate': self.rate,
            'sum': self.sum,
        })

class value_set(metric):
    def __init__(self):
        self.values = set()

    def __call__(self, value, hits):
        self.values.add(value)

    def __repr__(self):
        import json

        return json.dumps([x for x in self.values])
