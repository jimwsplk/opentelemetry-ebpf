# Flowmill agent integration tests

### Initial setup

Assumes benv output directory with compiled executables is mounted
at `$EBPF_NET_SRC/../benv-out`.

In fresh ubuntu VM, run as root:

    apt install gcc linux-headers-generic stunnel prometheus git
    systemctl disable prometheus
    systemctl stop prometheus
    cd flowmill/test/agent-tests
    mkdir -p /etc/flowmill
    cp -v ../../misc/keys/staging/authz-token-public.pem /etc/flowmill/
    cp -v ca.crt /usr/local/share/ca-certificates/Flowmill_CA.crt
    update-ca-certificates

The last command should print:

    Updating certificates in /etc/ssl/certs...
    1 added, 0 removed; done.

### Running tests

Run as root:

    ./run_test.sh http_test.py

Extra server/agent arguments can be supplied using `EXTRA_SERVER_ARGS`
and `EXTRA_AGENT_ARGS`:

    export EXTRA_AGENT_ARGS="--enable-userland-tcp"
    ./run_test.sh http_test.py
