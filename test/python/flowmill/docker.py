# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.core import default_debug_setting

from tempfile import NamedTemporaryFile

import io
import os
import sys

class docker_container:
    def __init__(self, container, debug=default_debug_setting()):
        self.container = container
        self.debug = debug

    def stop(self):
        result = self.container.stop()

        if self.debug:
            print(
                "stopped container '{}', status: `{}`".format(
                    self.container.image, self.container.status
            ))
            with NamedTemporaryFile(mode='wb', delete=False) as temp:
                temp.write(self.container.logs())
                print(
                    "saved logs for stopped container '{}' into '{}'".format(
                        self.container.image,
                        temp.name
                    ),
                    file=sys.stderr
                )

        return result

    def logs(self, stdout=True, stderr=True, stream=False, follow=False):
        result = self.container.logs(stream=stream, stdout=stdout, stderr=stderr, follow=stream)
        if stream:
            return result
        return result.decode('utf-8')

    def download_file(self, container_path):
        from tarfile import TarFile
        archive, status = self.container.get_archive(container_path)
        tar = TarFile(fileobj=io.BytesIO(bytes().join(archive)))
        file_name = os.path.basename(container_path)
        return tar.extractfile(file_name).read()

    def __exit__(self):
        # TODO: avoid double stops by checking self.container.status (returns a string)
        self.stop()

class docker_client:
    DEFAULT_REGISTRY = os.getenv('EBPF_NET_DOCKER_REGISTRY', 'localhost:5000')

    def __init__(self, unix_socket='/var/run/docker.sock', debug=default_debug_setting()):
        import docker
        url = 'unix:/{}'.format(unix_socket)
        self.docker = docker.DockerClient(base_url=url)
        self.debug = debug

    def pull(self, spec):
        self.docker.images.pull(spec.image_url)

        return spec

    def run(self, spec, pull=True, debug=default_debug_setting()):
        if pull:
            self.pull(spec)

        container = self.docker.containers.run(
            image=spec.image_url,
            command=spec.args,
            environment=spec.environment,
            volumes=spec.volumes,
            network_mode=spec.network_mode,
            pid_mode=spec.pid_mode,
            privileged=spec.privileged,
            detach=spec.detach
        )

        return docker_container(
            container=container,
            debug=debug or self.debug
        )

class docker_container_spec:
    def __init__(
        self,
        image,
        version='latest',
        registry=docker_client.DEFAULT_REGISTRY,
        args=[],
        environment={},
        volumes={},
        network_mode='',
        pid_mode='',
        privileged=False,
        detach=False
    ):
        self.image = image
        self.version = version
        self.registry = registry
        self.args = args
        self.environment = {k:v for k, v in environment.items() if v is not None}
        self.volumes = {k:v for k, v in volumes.items() if v is not None}
        self.network_mode = network_mode
        self.pid_mode = pid_mode
        self.privileged = privileged
        self.detach = detach

        self.image_url = "{}/{}:{}".format(self.registry, self.image, self.version)
