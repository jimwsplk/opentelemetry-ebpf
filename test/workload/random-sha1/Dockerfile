# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:unstable

ARG PKG_CORE="coreutils pv bc"
RUN apt-get update && apt-get install -y --no-install-recommends $PKG_CORE

COPY srv /srv
WORKDIR /srv
ENTRYPOINT [ "/srv/entrypoint.sh" ]
