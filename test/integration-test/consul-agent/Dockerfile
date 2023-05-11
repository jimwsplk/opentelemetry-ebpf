# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:unstable

RUN install_packages ca-certificates \
  coreutils gawk \
  net-tools netcat-openbsd curl \
  consul

COPY srv /srv
RUN mkdir -p /srv/common
COPY srv/common /srv/common
RUN mkdir -p /srv/consul.d
COPY srv/consul.d /srv/consul.d

ARG CONSUL_DATACENTER_NAME
ENV CONSUL_DATACENTER_NAME=${CONSUL_DATACENTER_NAME}
ARG CONSUL_BIND_ADDRESS
ENV CONSUL_BIND_ADDRESS=${CONSUL_BIND_ADDRESS}
ARG CONSUL_BIND_INTERFACE
ENV CONSUL_BIND_INTERFACE=${CONSUL_BIND_INTERFACE}
ARG CONSUL_BOOTSTRAP_NODE
ENV CONSUL_BOOTSTRAP_NODE=${CONSUL_BOOTSTRAP_NODE}

EXPOSE 53 53/udp 8300 8301 8301/udp 8302 8302/udp 8400 8500

WORKDIR /srv

ENTRYPOINT ["/srv/entrypoint.sh"]
CMD []

LABEL org.label-schema.name="flowtune/consul-agent" \
      org.label-schema.description="Flowtune consul agent" \
      org.label-schema.usage="./README.md" \
      org.label-schema.vcs-url="https://review.prod.flowtune.io/deploy/consul-agent-docker/" \
      org.label-schema.vendor="Flowmill, Inc" \
      org.label-schema.schema-version="1.0"
