# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:unstable

# Users of this image must export environment variables `HTTP_RESPONSE_CODE`, `INCOMING_PORT`
# and optionally `HEALTH_CHECK_PORT` (defaults to `INCOMING_PORT`) as well as expose all these
# ports.

ENV HTTP_HEALTH_CHECK_PATH=health/

# TODO: remove the procps line
RUN install_packages ca-certificates \
  procps dnsutils vim \
  coreutils sed gawk \
  net-tools iproute2 ncat netcat-openbsd curl \
  nginx-light

COPY srv /srv

COPY srv/data /srv/data
RUN mkdir -p /srv/logs

COPY srv/common /srv/common

WORKDIR /srv

ENTRYPOINT ["/srv/entrypoint.sh"]
CMD []
