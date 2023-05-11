# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.render.message import render_span, render_message, aggregated_render_message

from flowmill.render import metric

@render_span
class tracked_process(object):
    def __init__(self):
        self.tgid = None
        self.command = None
        self.cgroup = None

    @render_message
    def set_tgid(self, message):
        assert self.tgid is None or self.tgid == message.data.tgid
        self.tgid = message.data.tgid

    @render_message
    def set_command(self, message):
        self.command = message.data.command

    @render_message
    def set_cgroup(self, message):
        self.cgroup = message.data.cgroup

    cpu: aggregated_render_message(
        message_name="report_task_cpu",
        default=metric.rate,
        ignore=['pid', 'on_exit'],
        fields={
            'thread_count': metric.gauge,
        }
    )

    context_switches: aggregated_render_message(
        message_name="report_task_context_switches",
        default=metric.rate,
        ignore=['pid', 'on_exit'],
    )

    rss: aggregated_render_message(
        message_name="report_task_rss",
        default=metric.gauge,
        ignore=['pid', 'on_exit'],
    )

    page_faults: aggregated_render_message(
        message_name="report_task_page_faults",
        default=metric.rate,
        ignore=['pid', 'on_exit'],
    )

    io: aggregated_render_message(
        message_name="report_task_io",
        default=metric.rate,
        ignore=['pid', 'on_exit'],
    )

    io_wait: aggregated_render_message(
        message_name="report_task_io_wait",
        default=metric.rate,
        ignore=['pid', 'on_exit'],
    )

    def __repr__(self):
        return str({
            'tgid': self.tgid,
            'command': self.command,
            'cgroup': self.cgroup,
            'cpu': self.cpu,
            'context_switches': self.context_switches,
            'rss': self.rss,
            'page_faults': self.page_faults,
            'io': self.io,
            'io_wait': self.io_wait,
        })
