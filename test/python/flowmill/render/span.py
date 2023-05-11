# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.object import make_object_from_dictionary

class span_container:
    """
    Instantiates a span container capable of consuming streams of render
    messages for spans represented by class `span_type`.

    The method `consumers` generates a list of message consumers that can be
    fed into helpers like `flowmill.render.stream.replay_render_messages` and
    `flowmill.render.stream.message_stream_filterer`:
    ```
    processes = span_container(span_type=tracked_process)
    filter_message_stream(dump.ingest, consumers=[processes.consumers()])
    ```

    Spans are stored in an object with the following members:
   - `ref`: the numeric key of the span;
   - `start`: the timestamp of the span's start message;
   - `end`: the timestamp of the span's end message (only set for spans in the
     `history` list);
   - `instance`: an instance of `span_type`.

    Live spans can be accessed through the member variable `spans`. It is a
    dictionary where the key is the span's `_ref` and the value is the span.

    In order for specific spans to be selected out of the stream of spans,
    `select` is provided as a way to specify selection criteria. See below for
    more information.

    If `keep_history` is `True` then the member variable `history` will be a
    list of all past spans whose end messages were already collected.

    Start and end messages are handled automatically.

    Other messages can be declared as member functions in the `span_type` using
    the `render_message` decorator.

    The member function will receive the message as a parameter.

    See `flowmill.render.message.make_message_from_dictionary` for details on
    the structure of the message object.

    See package `flowmill.render.spans` for a list of known span types.

    Example span type (render declaration below):
    ```
    @render_span
    class tracked_process(object):
        @render_message
        def set_pid(self, message):
            print("timestamp: {} ref: {} pid: {}".format(
                message.timestamp, message.ref, message.data.pid
            ))

    @render_span(name="foo_bar")
    class FooBar(object):
        @render_message
        def set_foo(self, message):
            print("timestamp: {} ref: {} foo: {}".format(
                message.timestamp, message.ref, message.data.foo
            ))

        @render_message(name="set_bar")
        def setBar(self, message):
            print("timestamp: {} ref: {} bar: {}".format(
                message.timestamp, message.ref, message.data.bar
            ))
    ```

    Example span (render):
    ```
    span tracked_process {
      pool_size 600000
      conn_hash

      72: msg _start {}
      73: msg _end {}

      74: msg set_pid {
        description "set pid"
        severity 0
        1: u32 pid
      }
    }

    span foo_bar {
      pool_size 600000
      conn_hash

      82: msg _start {}
      83: msg _end {}

      84: msg set_foo {
        description "set foo"
        severity 0
        1: string foo
      }

      85: msg set_bar {
        description "set bar"
        severity 0
        1: string bar
      }
    }
    ```

    Select Criteria
    ===============
    Spans can be singled out according to a given selection criteria based on
    the fields of `span_type`.

    For this purpose, the `select` argument is offered as a dictionary, where
    the key of the dictionary is the group name (arbitrary) and the value is
    the criteria for the match.

    Say there's a span with fields `pid` and `command`. The `select` argument
    below will group spans with `pid == 1` and `command == "init"` in one group
    called `init process`, and spans with `command == "ssh"` or `command ==
    "sshd"` in another group called `secure shell`:
    ```
    container = span_container(span_type=my_span, select={
        "init process": {"pid": [1], "command": "init"},
        "secure shell": {"command": ["ssh", "sshd"]},
    })
    ```

    The different groups can be retrieved through the method `retrieve`:
    ```
    init_spans = container.retrieve("init process")
    ssh_spans = container.retrieve("secure shell")
    ```

    Spans will be selected when their lifetime ends (end message received).

    To select among live spans as well, pass the argument `live=True` to
    the `retrieve` method.
    """

    def __init__(self, span_type, select={}, keep_history=False):
        self.spans = {}
        self.span_type = span_type
        self.history = [] if keep_history else None
        self.selectors = {n: span_container.span_selector(c) for n, c in select.items()}
        self.selection = {}

    def start(self, message):
        instance = self.span_type()
        assert '_ref' not in message.map or message.data._ref == message.ref
        self.spans[message.ref] = make_object_from_dictionary({
            'ref': message.ref,
            'start': message.timestamp,
            'instance': instance,
        })

    def end(self, message):
        assert '_ref' not in message.map or message.data._ref == message.ref
        span = self.spans.pop(message.ref)

        # process `select` as we go
        for name, selector in self.selectors.items():
            if selector(span):
                if name not in self.selection:
                    self.selection[name] = [span]
                else:
                    self.selection[name].append(span)

        # update `history`
        if self.history is not None:
            span.end = message.timestamp
            self.history.append(span)

    def forward_message(self, message, method):
        span = self.spans[message.ref]
        assert span.ref == message.ref
        assert '_ref' not in message.map or message.data._ref == message.ref
        method.__call__(span.instance, message)

    def consumers(self):
        render_span = self.span_type.render_span

        consumers = {
            render_span.start_message: self.start,
            render_span.end_message: self.end,
        }

        from functools import partial

        for method_name in dir(self.span_type):
            method = getattr(self.span_type, method_name)
            if 'render_message' in dir(method):
                name = method.render_message.name
                consumers[name] = partial(self.forward_message, method=method)

        return consumers

    def retrieve(self, name, live=False):
        assert name in self.selectors

        selection = self.selection[name] if name in self.selection else []

        if live:
            selector = self.selectors[name]
            selection.extend(
                span.instance for ref, span in self.spans.items() if selector(span)
            )

        return selection

    class span_selector:
        def __init__(self, criteria, debug=default_debug_setting()):
            self.criteria = criteria

        def __call__(self, span):
            for field_name, expected in self.criteria.items():
                assert field_name in dir(span.instance)
                actual = getattr(span.instance, field_name)

                if isinstance(expected, list):
                    if actual not in expected:
                        # value not among expected ones
                        return False
                elif actual != expected:
                    # value not expected
                    return False

            return True
