# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec

import io
import os
import sys

class reducer:
    """
    Starts the reducer container.

    `docker`: an instance of `flowmill.docker.docker_client`.
    """

    DEFAULT_ARGS = ['--log-console', '--debug']

    def __init__(
        self,
        docker,
        image='reducer',
        version=os.getenv('EBPF_NET_PIPELINE_SERVER_VERSION', 'latest'),
        registry=docker_client.DEFAULT_REGISTRY,
        intake_port = 8000,
        enable_prom_metrics=False,
        internal_prom_port=7000,
        prom_port=7001,
        enable_otlp_grpc_metrics=False,
        otlp_grpc_metrics_host='localhost',
        otlp_grpc_metrics_port=4317,
        args = [],
        detach=True,
        debug=default_debug_setting()
    ):
        self.debug = debug

        args = reducer.DEFAULT_ARGS + args
        args.append('--port={}'.format(intake_port))
        args.append('--internal-prom=0.0.0.0:{}'.format(internal_prom_port))
        args.append('--disable-metrics=ebpf_net.all')

        if enable_prom_metrics:
            args.append('--prom=0.0.0.0:{}'.format(prom_port))
        else:
            args.append('--disable-prometheus-metrics')

        if enable_otlp_grpc_metrics:
            args.append('--enable-otlp-grpc-metrics')
            
            args.append('--otlp-grpc-metrics-host={}'.format(otlp_grpc_metrics_host))
            args.append('--otlp-grpc-metrics-port={}'.format(otlp_grpc_metrics_port))

        volumes={
            '/sys/fs/cgroup': {'bind': '/hostfs/sys/fs/cgroup', 'mode': 'ro'},
            '/usr/src': {'bind': '/hostfs/usr/src', 'mode': 'ro'},
            '/lib/modules': {'bind': '/hostfs/lib/modules', 'mode': 'ro'},
            '/etc': {'bind': '/hostfs/etc', 'mode': 'ro'},
            '/var/cache': {'bind': '/hostfs/cache', 'mode': 'rw'},
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
        }

        environment={
        }

        print("starting reducer against {}...".format(
            intake_port
        ))

        from flowmill.docker import docker_container_spec

        spec = docker_container_spec(
            image=image,
            registry=registry,
            version=version,
            args=args,
            environment=environment,
            volumes=volumes,
            network_mode='host',
            pid_mode='host',
            privileged=True,
            detach=detach
        )

        docker.pull(spec)

        self.container = docker.run(spec=spec, pull=False, debug=self.debug)

    def stop(self):
        self.container.stop()

    def logs(self):
        return self.container.logs()
