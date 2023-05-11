running the test container
==========================
The test container takes care of starting the collectors and the workload. For that it needs access to the host's docker engine.

There's a sample script to be used as a starting point for how to run the container: `run-test-container.sh`.

Build the container using build target `python-integration-tests-docker`. Push it to the docker registry with build target `python-integration-tests-docker-registry`.

Below are the minimum settings required for the container to work:

privileges
----------
The test container doesn't need any special privileges, but is must be able to spin up the kernel collector's container with docker options `--privileged`, `--net host` and `--pid host`.

volumes
-------
- `/var/run/docker.sock`: the host's Docker engine UNIX socket.

environment variables
---------------------
These are the environment variables used directly by the test container:
- `EBPF_NET_DOCKER_REGISTRY`: the registry to pull workloads and the components being tested from. Defaults to `localhost:5000`.

Additionally, there are the environment variables to be forwarded to the collector which should be set into the test container. Development environments like `benv` and `devbox` already take care of the environment setup.

Additional environments should, at the bare minimum, provide these variables: `EBPF_NET_INTAKE_HOST`, `EBPF_NET_INTAKE_PORT`.
