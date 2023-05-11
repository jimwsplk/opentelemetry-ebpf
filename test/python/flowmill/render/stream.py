# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.render.message import basic_message_fields_filter

class message_streamer:
    """
    Decodes a JSON stream and returns an iterable of messages as created by
    `flowmill.render.message.make_message_from_dictionary`.
    """

    def __init__(self, stream, buffer_size = 4096):
        """
        `stream` is the JSON stream. It has to support the `read(size)` call as
        per `io.BytesIO` and is often `sys.stdin.buffer`.
        See https://docs.python.org/3/library/io.html#io.BytesIO.

        `buffer_size` is the size of the buffer used to read from the stream.
        """

        self.stream = stream
        self.buffer_size = 4096

        import ijson
        self.events = ijson.sendable_list()
        self.coro = ijson.items_coro(self.events, 'item')

    def next(self):
        """
        Decodes and returns the next message from the JSON stream.

        Returns `None` when EOF is reached.
        """

        while len(self.events) < 1:
            chunk = self.stream.read(self.buffer_size)

            if len(chunk) < 1:
                self.coro.close()
                return None

            self.coro.send(chunk)

        from flowmill.render.message import make_message_from_dictionary

        element = self.events.pop(0)
        return make_message_from_dictionary(element)

def stream_render_messages(stream, buffer_size = 4096):
    """
    Decodes a JSON stream and returns an iterable of messages as created by
    `flowmill.render.message.make_message_from_dictionary`.

    `stream` has to support the `read(size)` call as per `io.BytesIO` and is
    often `sys.stdin.buffer`.
    See https://docs.python.org/3/library/io.html#io.BytesIO.

    `buffer_size` is the size of the buffer used to read from the stream.

    This function returns an iterable of messages as created by
    `flowmill.render.message.make_message_from_dictionary`.
    """

    streamer = message_streamer(stream, buffer_size)
    while True:
        message = streamer.next()

        if message is None:
            break

        yield message

def replay_render_messages(stream, consumers = [], buffer_size = 4096):
    """
    Decodes a JSON stream and returns an iterable of messages as created by
    `flowmill.render.message.make_message_from_dictionary`.

    `consumers` defines a list of dictionaries that map message names to
    message consumers. Messages will automatically be dispatched to the
    appropriate consumers. Consumers are a callable object that takes a message
    object as its single argument.

    See `span_container` for a handy message consumer capable of re-creating
    spans.

    `stream` has to support the `read(size)` call as per `io.BytesIO` and is
    often `sys.stdin.buffer`.
    See https://docs.python.org/3/library/io.html#io.BytesIO.

    `buffer_size` is the size of the buffer used to read from the stream.
    """

    handler_map = {}

    for consumer_map in consumers:
        for name, consumer in consumer_map.items():
            if not name in handler_map:
                handler_map[name] = []
            handler_map[name].append(consumer)

    for message in stream_render_messages(stream, buffer_size):
        if message.name in handler_map:
            for consumer in handler_map[message.name]:
                consumer(message)

        yield message

class message_stream_filterer:
    """
    A message consumer that asserts that messages match the specified filter
    set.
    """

    class message_fixed_filter_set:
        def __init__(self, message_filters, debug=default_debug_setting()):
            self.debug = debug
            self.filters = {
                name: filters
                    if isinstance(filters, basic_message_fields_filter)
                    else basic_message_fields_filter(filters)
                    for name, filters in message_filters.items()
            }

        def __call__(self, message):
            if message.name not in self.filters:
                # not a message we're looking for
                return True

            return self.filters[message.name](message)

        def pending(self):
            return True

        def done(self):
            for name, filter in self.filters.items():
                if not filter.done():
                    return False
            return True

    class message_order_filter_set:
        class message_filter:
            def __init__(self, message_filters, debug=default_debug_setting()):
                self.debug = debug
                self.filters = {
                    name: basic_message_fields_filter(filters)
                        for name, filters in message_filters.items()
                }

            def __call__(self, message):
                if message.name not in self.filters:
                    # not a message we're looking for
                    return None

                return self.filters[message.name](message)

        def __init__(self, filters, debug=default_debug_setting()):
            self.debug = debug
            self.filters = [self.message_filter(f, self.debug) for f in filters]
            self.filters.reverse()

        def __call__(self, message):
            assert len(self.filters) > 0

            result = self.filters[-1](message)

            if result is None:
                return True

            if not result:
                self.filters = []
                return False

            del self.filters[-1]
            return True

        def pending(self):
            return not self.done()

        def done(self):
            return len(self.filters) == 0

    def __init__(self, fixed_filter_set = {}, order_filter_set = {}, debug=default_debug_setting()):
        """
        `order_filter_set` is a dictionary comprised of several independent filter sets,
        applied to the same stream of messages.

        Fixed Filter Set
        ----------------

        The key of the dictionary is the filter's name, for documenting
        purposes only. The associated value is a dictionary where the key
        corresponds to the expected message name. The associated value is a
        dictionary with the message fields to be matched, also known as payload
        filters.

        Each payload filter is represented by a dictionary entry where the key is
        the message field name. The associated value can be either a string or a
        number, representing the expected value of the field, or an array of
        expected values where at least one has to match.

        Order Filter Set
        ----------------

        The key of the dictionary is the filter's name, for documenting purposes
        only. The associated value is an array of message filters to be asserted
        sequentially but not necessarily adjacent to each other.

        Each message filter is a dictionary with a single entry, where the key
        corresponds to the expected message name. The associated value is a
        dictionary with the message fields to be matched, also known as payload
        filters.

        Each payload filter is represented by a dictionary entry where the key is
        the message field name. The associated value can be either a string or a
        number, representing the expected value of the field, or an array of
        expected values where at least one has to match.

        Here's an example that should make the semantics more clear:

        ```
        order_filter_set = {
            "authentication messages order": [
                {"version_info": {}},
                {"authz_authenticate": {"collector_type": 1}},
                {"metadata_complete": {}},
            ],
            "kernel header fetching": [
                {"kernel_headers_source": { "source": [2, 4]}},
            ],
        }
        ```

        In the above example two independent filters are specified: one to assert
        that authentication messages are received in the correct order, and another
        one to assert that the kernel headers were source through the correct
        method.

        The `authentication messages order` message filter specifies three ordered
        messages. First, the `version_info` needs to be found in the stream - its
        payload doesn't matter. After this message is matched, another message
        called `authz_authenticate` has to be found where the `collector_type`
        member has to have the value `1`. Other members don't matter. Lastly, the
        `metadata_complete` message needs to be found - its payload also doesn't
        matter. Note that these messages don't need to appear immediately following
        the previous one, as long as the relative order is maintained.

        The `kernel header fetching` message filter is matched independently of
        other filters and all it expects is for a message
        named `kernel_headers_source` to be found, and its member `source` has to
        have a value of either `2` or `4`.

        Let's look at one example message streams (some fields omitted):
        ```
        {"name":"version_info","data":{"major":0,"minor":8,"build":2928}},
        {"name":"authz_authenticate","data":{"token":"omitted","collector_type":1,"hostname":"myhost"}},
        {"name":"os_info","data":{"os":1,"flavor":1,"kernel_version":"5.7.0-2-amd64"}},
        {"name":"kernel_headers_source","data":{"source":1}},
        {"name":"set_config_label","data":{"key":"environment","value":"myenv"}},
        {"name":"set_config_label","data":{"key":"host","value":"myhost"}},
        {"name":"set_config_label","data":{"key":"service","value":"mysvc"}},
        {"name":"set_config_label","data":{"key":"zone","value":"myzone"}},
        {"name":"set_config_label","data":{"key":"__kernel_version","value":"5.7.0-2-amd64"}},
        {"name":"cloud_platform","data":{"cloud_platform":0}},
        {"name":"set_node_info","data":{"az":"","role":"","instance_id":"myhost","instance_type":""}},
        {"name":"metadata_complete","data":{"time":0}}
        ```

        The message filter `authentication messages order` will match successfully.
        It contains the expected messages in the expected relative order, and the
        only specified member (from the `authz_authenticate` message) has the
        expected value of `1`.

        The message filter `kernel header fetching` will fail. Even though the
        expected message is present, the value of the specified member `source`
        differs from the expected values.

        In this next example (some fields omitted):
        ```
        {"name":"authz_authenticate","data":{"token":"omitted","collector_type":1,"hostname":"myhost"}},
        {"name":"version_info","data":{"major":0,"minor":8,"build":2928}},
        {"name":"os_info","data":{"os":1,"flavor":1,"kernel_version":"5.7.0-2-amd64"}},
        {"name":"kernel_headers_source","data":{"source":2}},
        {"name":"set_config_label","data":{"key":"environment","value":"myenv"}},
        {"name":"set_config_label","data":{"key":"host","value":"myhost"}},
        {"name":"set_config_label","data":{"key":"service","value":"mysvc"}},
        {"name":"set_config_label","data":{"key":"zone","value":"myzone"}},
        {"name":"set_config_label","data":{"key":"__kernel_version","value":"5.7.0-2-amd64"}},
        {"name":"cloud_platform","data":{"cloud_platform":0}},
        {"name":"set_node_info","data":{"az":"","role":"","instance_id":"myhost","instance_type":""}},
        {"name":"metadata_complete","data":{"time":0}}
        ```

        The message filter `kernel header fetching` now succeeds, but the message
        filter `authentication messages order` fails because the relative order
        between the messages `version_info` and `authz_authenticate` are not
        maintained.
        """

        self.debug = debug
        self.success_set = []
        self.failure_set = []
        self.filter_set = {
            name: self.message_fixed_filter_set(filter, debug=self.debug)
                for name, filter in fixed_filter_set.items() if len(filter) > 0
        }
        self.filter_set.update({
            name: self.message_order_filter_set(filter, debug=self.debug)
                for name, filter in order_filter_set.items() if len(filter) > 0
        })

    def __call__(self, message):
        """
        Forward the `message` to each pending filter.

        If `message` is `None`, it is ignored.

        Returns `message`.
        """

        if message is None:
            return None

        remove_queue = []

        for name, filter in self.filter_set.items():
            if not filter(message):
                if self.debug:
                    print("filter failed '{}'".format(name))
                remove_queue.append(name)
                self.failure_set.append(name)
            elif not filter.pending():
                if self.debug:
                    print("filter succeeded '{}'".format(name))
                remove_queue.append(name)
                self.success_set.append(name)

        for name in remove_queue:
            self.filter_set.pop(name)

        return message

    def replay(self, stream, consumers = [], buffer_size = 4096, debug=default_debug_setting()):
        """
        Asserts that messages read from the given JSON stream match the specified
        filter set.

        `consumers` is a list of custom message consumers. See
        `flowmill.render.stream.replay_render_messages` for more info.

        `stream` has to support the `read(size)` call as per `io.BytesIO` and is
        often `sys.stdin.buffer`.
        See https://docs.python.org/3/library/io.html#io.BytesIO.

        `buffer_size` is the size of the buffer used to read from the stream.

        This function returns a sorted list with the names of failed message filters.
        """

        if debug:
            print("replaying render messages...")

        for message in replay_render_messages(stream, consumers=consumers, buffer_size=buffer_size):
            self(message)

        self.finish(debug=debug)

        if debug:
            print("finished replaying render messages")

        return sorted(self.failures())

    def finish(self, debug=default_debug_setting()):
        """
        Signals that no further messages will be filtered.

        Any pending filters are moved to the failure set.
        """

        for name, filter in self.filter_set.items():
            if filter.done():
                self.success_set.append(name)
            else:
                self.failure_set.append(name)

        self.filter_set.clear()

        if debug or self.debug:
            print("SUCCESSES:", self.successes())
            print("FAILURES:", self.failures())

    def succeeded(self):
        return len(self.failure_set) == 0 and self.done()

    def done(self):
        return len(self.filter_set) == 0

    def pending(self):
        """
        Returns the list of pending filters.

        This list will always be empty after `finish` is called.
        """

        return self.filter_set.keys()

    def successes(self):
        """
        Returns the list of successful filters.
        """

        return self.success_set

    def failures(self):
        """
        Returns the list of failed filters.
        """

        return self.failure_set

def filter_message_stream(
    stream,
    fixed_filter_set = {},
    order_filter_set = {},
    consumers = [],
    buffer_size = 4096,
    debug = False,
):
    """
    Asserts that messages read from the given JSON stream match the specified
    filter set.

    `order_filter_set` is the list of filters to apply to the message stream. See
    `message_stream_filterer` for further details.

    `consumers` is a list of custom message consumers. See
    `flowmill.render.stream.replay_render_messages` for more info.

    `stream` has to support the `read(size)` call as per `io.BytesIO` and is
    often `sys.stdin.buffer`.
    See https://docs.python.org/3/library/io.html#io.BytesIO.

    `buffer_size` is the size of the buffer used to read from the stream.

    This function returns a sorted list with the names of failed message filters.
    """

    filters = message_stream_filterer(
        fixed_filter_set=fixed_filter_set,
        order_filter_set=order_filter_set,
        debug=debug,
    )

    return filters.replay(stream, consumers=consumers, buffer_size=buffer_size)
