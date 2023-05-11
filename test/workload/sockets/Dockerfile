# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/python:3
COPY srv /srv
WORKDIR /srv
ENTRYPOINT [ "/srv/sockets.py" ]
