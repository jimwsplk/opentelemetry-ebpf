# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec

import io
import os
import sys

class otlp_to_prom:
    """
    Starts the otlp_to_prom container.

    `docker`: an instance of `flowmill.docker.docker_client`.
    """

    def __init__(
        self,
        docker,
        image='otlp-to-prom',
        version='latest',
        registry=docker_client.DEFAULT_REGISTRY,
        listen_port=4317,
        detach=True,
        debug=default_debug_setting()
    ):
        self.debug = debug
        args = []
        args.append('--listen-port={}'.format(listen_port))

        volumes={
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}
        }

        environment={
        }

        print("starting otlp-to-prom on {}...".format(listen_port))
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

    def download_metrics_file(self):
        metrics_bytes = self.container.download_file('metrics.txt')
        print(str(metrics_bytes, 'UTF-8'))
        return metrics_bytes


