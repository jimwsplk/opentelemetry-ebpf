# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:buster

VOLUME /srv/run/

COPY srv /srv
WORKDIR /srv

CMD ["--ingest-file", "/srv/run/ingest.json"]

ENTRYPOINT ["/srv/kernel-collector-simulator"]
