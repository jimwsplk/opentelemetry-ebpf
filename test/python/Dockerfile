# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM docker-hub.repo.splunkdev.net/bitnami/minideb:buster

VOLUME /var/run/flowmill/data

ENTRYPOINT [ "/srv/entrypoint.sh" ]

ARG PKG_CORE="docker.io python3"
RUN apt-get update && apt-get install -y --no-install-recommends $PKG_CORE

ARG PKG_PYTHON="python3-pip python3-bcrypt python3-pytest python3-setuptools"
RUN apt-get update && apt-get install -y --no-install-recommends $PKG_PYTHON

ARG PYTHON_LIBS="ijson docker"
RUN pip3 install ${PYTHON_LIBS}

WORKDIR /srv
COPY srv /srv
