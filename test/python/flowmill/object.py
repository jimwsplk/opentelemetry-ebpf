# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

class dynamic_object(object):
    def __repr__(self):
        result = {}
        for name in dir(self):
            if name[0:2] != '__':
                result[name] = getattr(self, name)
        return str(result)

def make_object_from_dictionary(dictionary):
    object = dynamic_object()
    for name, value in dictionary.items():
        setattr(object, name, value)
    return object
