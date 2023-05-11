# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:unstable

# TODO: remove the procps line
RUN install_packages ca-certificates \
  procps net-tools dnsutils \
  coreutils \
  curl ncat netcat-openbsd dnsmasq iproute2

# Run this container with `--dns=127.0.0.1` so that dnsmasq will be used

COPY srv /srv
RUN mkdir -p /srv/common
COPY srv/common /srv/common

ARG HEALTH_CHECK_PORT=8000
ENV HEALTH_CHECK_PORT=${HEALTH_CHECK_PORT}
EXPOSE ${HEALTH_CHECK_PORT}

WORKDIR /srv

ENTRYPOINT ["/srv/entrypoint.sh"]
CMD []

LABEL org.label-schema.name="flowtune/http-test-client" \
      org.label-schema.description="Flowtune http test client" \
      org.label-schema.usage="./README.md" \
      org.label-schema.vcs-url="https://review.prod.flowtune.io/deploy/http-test-client-docker/" \
      org.label-schema.vendor="Flowmill, Inc" \
      org.label-schema.schema-version="1.0"
