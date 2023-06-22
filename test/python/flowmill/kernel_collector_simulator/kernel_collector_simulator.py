# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec

import io
import os
import sys

class kernel_collector_simulator:
    """
    Starts the kernel_collector_simulator container.

    `docker`: an instance of `flowmill.docker.docker_client`.
    `ingest_filename`: the name of the file to play back.
    """

    def __init__(
        self,
        docker,
        ingest_filename='ingest.json',
        intake_host=os.getenv('EBPF_NET_INTAKE_HOST'),
        intake_port=os.getenv('EBPF_NET_INTAKE_PORT'),
        image='kernel-collector-simulator',
        version='latest',
        registry=docker_client.DEFAULT_REGISTRY,
        detach=True,
        debug=default_debug_setting()
    ):
        self.debug = debug
        args = []
        args.append('--ingest-file=/srv/run/{}'.format(ingest_filename))

        volumes={
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}
        }

        environment={
            "EBPF_NET_INTAKE_HOST": intake_host,
            "EBPF_NET_INTAKE_PORT": intake_port,
        }

        print("starting kernel_collector_simulator...")
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



