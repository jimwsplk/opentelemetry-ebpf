# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec

from tempfile import NamedTemporaryFile

import io
import os
import sys

class kernel_collector:
    """
    Starts the kernel collector container.

    `docker`: an instance of `flowmill.docker.docker_client`.
    """

    DEFAULT_ARGS = ['--log-console', '--debug']

    TOOLS_PATH = os.getenv('EBPF_NET_TOOLS_DIR', '.')

    BPF_DUMP_FILE = 'bpf.render.raw'
    BPF_CONVERTER_BINARY = 'bpf_wire_to_json'
    BPF_CONVERTER_PATH = os.path.join(TOOLS_PATH, BPF_CONVERTER_BINARY)

    INGEST_DUMP_FILE = 'ingest.render.raw'
    INGEST_CONVERTER_BINARY = 'intake_wire_to_json'
    INGEST_CONVERTER_PATH = os.path.join(TOOLS_PATH, INGEST_CONVERTER_BINARY)

    def __init__(
        self,
        docker,
        image='kernel-collector',
        version=os.getenv('EBPF_NET_KERNEL_COLLECTOR_VERSION', 'latest'),
        registry=docker_client.DEFAULT_REGISTRY,
        bpf_dump=False,
        ingest_dump=False,
        args = [],
        intake_host = os.getenv('EBPF_NET_INTAKE_HOST'),
        intake_port = os.getenv('EBPF_NET_INTAKE_PORT'),
        labels_namespace = os.getenv('EBPF_NET_AGENT_NAMESPACE'),
        labels_environment = os.getenv('EBPF_NET_AGENT_CLUSTER'),
        labels_service = os.getenv('EBPF_NET_AGENT_SERVICE'),
        labels_host = os.getenv('EBPF_NET_AGENT_HOST'),
        labels_zone = os.getenv('EBPF_NET_AGENT_ZONE'),
        fetch_kernel_headers = os.getenv('EBPF_NET_KERNEL_HEADERS_AUTO_FETCH', 'true'),
        data_dir = os.getenv('EBPF_NET_DATA_DIR', '/var/run/ebpf_net'),
        detach=True,
        debug=default_debug_setting()
    ):
        self.debug = debug

        args = kernel_collector.DEFAULT_ARGS + args

        volumes={
            '/sys/fs/cgroup': {'bind': '/hostfs/sys/fs/cgroup', 'mode': 'ro'},
            '/usr/src': {'bind': '/hostfs/usr/src', 'mode': 'ro'},
            '/lib/modules': {'bind': '/hostfs/lib/modules', 'mode': 'ro'},
            '/etc': {'bind': '/hostfs/etc', 'mode': 'ro'},
            '/var/cache': {'bind': '/hostfs/cache', 'mode': 'rw'},
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
        }

        environment={
            "EBPF_NET_INTAKE_HOST": intake_host,
            "EBPF_NET_INTAKE_PORT": intake_port,
            "EBPF_NET_AGENT_NAMESPACE": labels_namespace,
            "EBPF_NET_AGENT_CLUSTER": labels_environment,
            "EBPF_NET_AGENT_SERVICE": labels_service,
            "EBPF_NET_AGENT_HOST": labels_host,
            "EBPF_NET_AGENT_ZONE": labels_zone,
            "EBPF_NET_KERNEL_HEADERS_AUTO_FETCH": fetch_kernel_headers,
            "EBPF_NET_DATA_DIR": data_dir,
        }

        if ingest_dump:
            self.ingest_dump_path = os.path.join(data_dir, 'dump', kernel_collector.INGEST_DUMP_FILE)
            environment['EBPF_NET_RECORD_INTAKE_OUTPUT_PATH'] = self.ingest_dump_path

        if bpf_dump:
            self.bpf_dump_path = os.path.join(data_dir, 'dump', kernel_collector.BPF_DUMP_FILE)
            args.extend(['--bpf-dump-file', self.bpf_dump_path])

        print("starting kernel collector against {}:{}...".format(
            intake_host, intake_port,
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

    def dump_json_bpf(self):
        return self.download_json_dump(
            self.bpf_dump_path,
            kernel_collector.BPF_CONVERTER_PATH
        )

    def dump_json_ingest(self):
        return self.download_json_dump(
            self.ingest_dump_path,
            kernel_collector.INGEST_CONVERTER_PATH
        )

    def download_raw_dump(self, container_path):
        assert container_path is not None

        raw = self.container.download_file(container_path)

        if self.debug:
            with NamedTemporaryFile(mode='wb', delete=False) as temp:
                temp.write(raw)
                print(
                    "raw version of kernel collector's '{}' saved as '{}'".format(
                        container_path,
                        temp.name
                    ),
                    file = sys.stderr
                )

        return raw

    def download_json_dump(self, container_path, converter_path):
        """
        Returns a JSON representation of the given dump as `bytes`.

        If debug mode is enabled, the file is saved in a temporary location and
        its path is output to `stderr`.
        """
        from subprocess import Popen, PIPE, STDOUT

        raw = self.download_raw_dump(container_path)

        process = Popen(converter_path, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout, stderr = process.communicate(input=raw)

        if self.debug:
            with NamedTemporaryFile(mode='wb', delete=False) as temp:
                #import json
                #temp.write(json.dumps(json.loads(stdout), indent=2, sort_keys=True))
                temp.write(stdout)
                print(
                    "JSON version of kernel collector's '{}' saved as '{}'".format(
                        container_path,
                        temp.name
                    ),
                    file=sys.stderr
                )

        return io.BytesIO(stdout)
