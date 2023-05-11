# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.object import dynamic_object, make_object_from_dictionary

def render_span(span_type, name = None, start_message = None, end_message = None):
    """
    Decorator that registers a class as a render span handler.

    See `flowmill.render.span.span_container` for more info.
    """
    if name is None:
        name = span_type.__name__
    if start_message is None:
        start_message = name + "_start"
    if end_message is None:
        end_message = name + "_end"

    if '__annotations__' in dir(span_type):
        for name, type in span_type.__annotations__.items():
            if not isinstance(type, aggregated_render_message): continue
            type.modify(name, span_type)

    span_type.render_span = make_object_from_dictionary({
        'name': name,
        'start_message': start_message,
        'end_message': end_message,
    })

    return span_type

def render_message(handler, name = None):
    """
    Decorator that registers a member function as a render message handler.

    See `flowmill.render.span.span_container` for more info.
    """
    handler.render_message = make_object_from_dictionary({
        'name': handler.__name__ if name is None else name
    })
    return handler

class aggregated_render_message:
    from flowmill.render import metric

    def __init__(
        self,
        fields = {},
        default = metric.rate,
        constants = ['_ref'],
        ignore = [],
        message_name = None
    ):
        self.fields = fields
        self.default = default
        self.constants = constants
        self.ignore = ignore
        self.message_name = message_name
        #print("********************* aggregated_render_message __INIT__ MESSAGE NAME", self.message_name, "CONSTANTS", self.constants, "IGNORE", self.ignore, "FIELDS", self.fields, "DEFAULT", self.default)

    class message_aggregator:
        def __init__(self, name, message_name, default, constants, ignore, fields):
            self.name = name
            self.message_name = message_name
            self.default = default
            self.constants = constants
            self.ignore = ignore
            self.fields = fields
            self.render_message = make_object_from_dictionary({
                'name': self.message_name
            })
            #print("********************* message_aggregator __INIT__ MESSAGE NAME", self.message_name, "CONSTANTS", self.constants, "IGNORE", self.ignore, "FIELDS", self.fields, "DEFAULT", self.default)

        def __call__(this, self, message):
            assert this.name in dir(self)
            aggregator = getattr(self, this.name)
            if isinstance(aggregator, aggregated_render_message.message_aggregator):
                aggregator = dynamic_object()
                aggregator.hits = 1
                setattr(self, this.name, aggregator)
            else:
                aggregator.hits += 1

            for field_name, value in message.map.items():
                if field_name in this.ignore:
                    continue
                if field_name in this.constants:
                    #print("**************** CONSTANTS NAME", field_name, "FIELDS", this.fields)
                    if field_name not in dir(aggregator):
                        setattr(aggregator, field_name, value)
                    else:
                        field = getattr(aggregator, field_name)
                        # TODO: remove - self is debug code
                        #if field != value:
                        #    print(
                        #        "current {}: '{}' got '{}' message ```{}``` object ```{}```"
                        #        .format(field_name, field, value, message, aggregator)
                        #    )
                        assert field == value
                elif field_name in dir(aggregator):
                    field = getattr(aggregator, field_name)
                    #print("**************** EXISTING NAME", field_name, "THIS", type(this), "SELF", type(self), "CONSTANTS", this.constants, "IGNORE", this.ignore, "FIELD(", type(field), ")", field, "FIELDS", this.fields, "VALUE(", type(value), ")", value)
                    field(value, aggregator.hits)
                else:
                    field = this.fields[field_name]() if field_name in this.fields else this.default()
                    #print("**************** NEW AGGREGATOR MEMBER", this.name, "MESSAGE", this.message_name, "FIELD", field_name, "SELF-TYPE", type(self), "FIELD", field, "TYPE", type(field))
                    assert aggregator.hits == 1
                    field(value, aggregator.hits)
                    setattr(aggregator, field_name, field)

    def modify(self, name, span_type):
        if name is None: name = self.message_name
        assert name is not None

        # create message handler through the `message_aggregator`

        handler = aggregated_render_message.message_aggregator(
            name=name,
            message_name=self.message_name,
            default=self.default,
            constants=self.constants,
            ignore=self.ignore,
            fields=self.fields
        )

        #print("********************* SETTING MSG HANDLER NAME", name, "MESSAGE NAME", self.message_name, "SPAN_TYPE", span_type, "HANDLER", type(handler), "CONSTANTS", self.constants, "IGNORE", self.ignore, "FIELDS", self.fields, "DEFAULT", self.default)

        setattr(span_type, name, handler)

        return span_type

def make_message_from_dictionary(dictionary):
    """
    Parses the JSON representation of a message into a message object with proper member variables.

    Below is the object's field structure for the example message (render declaration further down):
    ```
    .name: the message name
    .rpc_id: the message RPC ID
    .timestamp: the message timestamp
    .ref: for messages that act on a span reference, the reference id of the span
    .map: a dictionary representation of the message fields
    .data: the message fields (varies by message)
        .count: the value of the `count` field
        .payload: the value of the `payload` field
    ```

    Example span (message):
    ```
    74: msg some_message {
      description "example message"
      severity 0
      1: u32 count
      2: string payload
    }
    ```
    """

    METADATA_FIELD_NAMES = ['name', 'rpc_id', 'timestamp', 'ref']

    object = dynamic_object()

    for name in METADATA_FIELD_NAMES:
        if name in dictionary:
            setattr(object, name, dictionary[name])
    object.map = dictionary['data']
    object.data = dynamic_object()

    for name, value in object.map.items():
        setattr(object.data, name, value)

    return object

class basic_message_fields_filter:
    def __init__(self, filters):
        self.filters = filters

    def __call__(self, message):
        for name, expected in self.filters.items():
            if name not in message.map:
                # expected field not found in message
                return False

            actual = message.map[name]

            if isinstance(expected, list):
                if actual not in expected:
                    # value not among expected ones
                    return False
            elif actual != expected:
                # value not expected
                return False

        # all filters check
        return True

    def done(self):
        return True

class message_fields_filter(basic_message_fields_filter):
    def __init__(self, filters, min=0, max=None):
        super().__init__(filters=filters)
        self.min = min
        self.max = max
        assert self.max is None or self.min <= self.max
        self.hits = 0

    def __call__(self, message):
        self.hits += 1

        if self.max is not None and self.hits > self.max:
            return False

        return super().__call__(message)

    def done(self):
        if self.hits < self.min:
            return False

        return super().done()
