# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.collector.kernel import kernel_collector
from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec
from flowmill.object import make_object_from_dictionary

import heapq
import time

class kernel_collector_tester:
    """
    Runs the kernel collector and manages the scheduling of workload
    containers.

    Collects render message dumps from the kernel collector after all workloads
    are done.

    The output of `run` can be used as the input for the render messages
    streamers from the package `flowmill.render.stream`.

    Below is a quick example of how to run workloads using this class:

    # instantiate the kernel collector tester (debug mode)
    tester = kernel_collector_tester(debug=True)

    # add the lookbusy workload to be run immediately for 5 seconds (debug mode)
    lookbusy = tester.add_workload(image='workload-lookbusy', duration=5, debug=True)

    # run all workloads and collect the ingest dump
    dump = tester.run(ingest_dump=True)

    # declare some message filters to be applied on top of the ingest dump
    filters = message_stream_filterer(
        fixed_filter_set={
            "default cpu period": {
                "container_resource_limits": message_fields_filter({"cpu_period": 100000}, min=1),
            },
        },
        order_filter_set={
            "kernel header fetching": [
                {"kernel_headers_source": {"source": [1, 2, 4]}},
            ],
        }
    )

    # creates a span container for `tracked_processes`
    tracked_processes = span_container(span_type=tracked_process, keep_history=True)

    # replay messages from the `dump.ingest` stream and apply pre-specified filters
    # at the same time, collect spans into the `tracked_processes` container
    filters.replay(dump.ingest, consumers=[tracked_processes.consumers()])

    # download files out of the lookbusy workload container
    with open('/tmp/lookbusy', 'wb') as out:
        out.write(lookbusy.container.download_file('/srv/lookbusy'))

    # assert that all the filters succeeded
    assert filters.succeeded()
    """
    def __init__(self, collector_startup_delay=30, debug=default_debug_setting()):
        self.docker = docker_client()
        self.scheduled = []
        self.debug = debug
        self.collector_startup_delay = collector_startup_delay
        self.kernel_collector = None

    def run(self, ingest_dump=False, bpf_dump=False, args=[]):
        """
        Runs the kernel collector and all scheduled workflows.

        After everything is done running, returns an object with members:
        - `bpf`: an instance of `io.BytesIO` containing the JSON dump of BPF
          messages for the kernel collector, if `bpf_dump` is true;
        - `ingest`: an instance of `io.BytesIO` containing the JSON dump of
          ingest messages for the kernel collector, if `ingest_dump` is true;
        """

        # TODO: dump logs

        if self.debug:
            print("pulling workload images...")
        # pre-pull dockr images
        for workload in self.scheduled:
            self.docker.pull(workload.spec)

        heapq.heapify(self.scheduled)

        if self.debug:
            print("starting kernel collector...")
        self.kernel_collector = kernel_collector(
            args=args,
            docker=self.docker,
            ingest_dump=ingest_dump,
            bpf_dump=bpf_dump,
            debug=self.debug
        )
        # TODO: when proper ingest streaming is in place, get rid of the sleep
        #       and wait for the appropriate message
        time.sleep(self.collector_startup_delay + (0 if len(self.scheduled) > 0 else 10))

        if self.debug:
            print("running workloads...")
        timestamp = 0
        while len(self.scheduled) > 0:
            job = heapq.heappop(self.scheduled)

            job_time = job.time()
            assert job_time >= timestamp
            if job_time > timestamp:
                delay = job_time - timestamp
                if self.debug:
                    print("sleeping for {} seconds".format(delay))
                time.sleep(delay)
                timestamp = job_time

            if job(self.docker):
                heapq.heappush(self.scheduled, job)

        if self.debug:
            print("stopping kernel collector...")
        self.kernel_collector.stop()

        if self.debug:
            print("collecting render messages...")
        result = {}
        if bpf_dump:
            result["bpf"] = self.kernel_collector.dump_json_bpf()
        if ingest_dump:
            result["ingest"] = self.kernel_collector.dump_json_ingest()

        self.kernel_collector = None
        
        return make_object_from_dictionary(result)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for job in self.scheduled:
            job.stop()
        if self.kernel_collector is not None:
            self.kernel_collector.stop()

    def add_workload(self, duration, delay=0, debug=default_debug_setting(), *args, **kwargs):
        """
        Schedules execution of the given docker image as a workload.

        Extra positional and named arguments will be forwarded to
        `flowmill.docker.docker_container_spec`.

        The workload will be started `delay` seconds after `run` is called and
        will run for `duration` seconds before being stopped.

        Returns an instance of `kernel_collector_tester.workload` as a proxy of
        the workload. This proxy allows things like downloading files from the
        workload container.
        """
        workload = kernel_collector_tester.workload(
            spec=docker_container_spec(*args, **kwargs),
            duration=duration,
            delay=delay,
            debug=debug,
        )

        self.scheduled.append(workload)

        return workload

    class workload:
        """
        Represents a workload container.

        The member variable `container` is an instance of the workload
        container. The instance is `None` if the workload is still in `pending`
        state, otherwise if is a valid `flowmill.docker.docker_container`
        instance, even after stopped.

        The member variable `spec` contains the specs of the container images,
        as an instance of `flowmill.docker.docker_container_spec`.
        """

        def __init__(self, spec, duration, delay=0, debug=default_debug_setting()):
            self.spec = spec
            self.spec.detach = True
            self.container = None
            self.ended = False

            assert duration > 0
            self.duration = duration

            assert delay >= 0
            self.delay = delay

            self.debug = debug

        def pending(self):
            """
            Returns `True` if this workload hasn't started execution yet,
            regardless of whether it already stopped. Returns `False`
            otherwise.
            """
            return self.container is None

        def running(self):
            """
            Returns `True` if this workload is currently running. Returns
            `False` if it's still pending execution or if it already stopped..
            """
            return not self.pending() and not self.finished

        def finished(self):
            """
            Returns `True` if this workload has already finished executing.
            Returns `False` if it's pending or running.
            """
            return self.ended

        def stop(self):
            if self.running():
                self.container.stop()
                self.ended = True

        def __call__(self, docker):
            """
            private framework method, do not use
            """

            if self.container is None:
                if self.debug:
                    print("starting workload '{}'...".format(self.spec.image))
                self.container = docker.run(self.spec, pull=False, debug=self.debug)
                return True
            else:
                if self.debug:
                    print("stopping workload '{}'...".format(self.spec.image))
                self.stop()
                return False

        def time(self):
            """
            private framework method, do not use
            """

            if self.container is None:
                # event not started, return time of start event
                return self.delay
            else:
                # event started, return time of stop event
                return self.delay + self.duration

        def __lt__(self, rhs):
            return self.time() < rhs.time()

        def __le__(self, rhs):
            return self.time() <= rhs.time()

        def __gt__(self, rhs):
            return self.time() > rhs.time()

        def __ge__(self, rhs):
            return self.time() >= rhs.time()
