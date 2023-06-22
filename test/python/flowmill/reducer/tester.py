# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from flowmill.reducer.reducer import reducer
from flowmill.otlp_to_prom.otlp_to_prom import otlp_to_prom
from flowmill.core import default_debug_setting
from flowmill.docker import docker_client, docker_container_spec
from flowmill.object import make_object_from_dictionary
from flowmill.kernel_collector_simulator.kernel_collector_simulator import kernel_collector_simulator

import time
import requests

class otlp_reducer_tester:
    """
    Runs a reducer,a kernel collector, and the otlp-to-prom converter containers.
    DSB TODO when ingest playback is finished, return here and load a specified ingest file
    in ingest playback, then return the result from the reducer

    """
    def __init__(self, debug=default_debug_setting()):
        self.docker = docker_client()
        self.debug = debug
        self.scheduled = []
        self.otlp_to_prom = None
        self.reducer = None
        self.kernel_collector_simulator = None

    def run(self, reducer_args=[], collector_args=[]):
        """
        Runs a reducer and kernel collector and a converter.  It then takes the output
        of the prom formatted metrics and the output of the otlp formatted metrics, and returns
        them.
        """
        print("starting otlp-to-prom...")
        otlp_listen_port = 4317
        self.otlp_to_prom = otlp_to_prom(
                docker=self.docker,
                listen_port=otlp_listen_port)

        print("starting reducer...")
        # assign some ports not likely to be in use
        intake_port = 8100
        internal_prom_port = 9100
        prom_port = 9110
        otlp_grpc_metrics_port = otlp_listen_port 
        self.reducer = reducer(
            docker=self.docker,
            debug=self.debug,
            intake_port=intake_port,
            enable_prom_metrics=True,
            internal_prom_port=internal_prom_port,
            enable_otlp_grpc_metrics=True,
            otlp_grpc_metrics_host='localhost',
            otlp_grpc_metrics_port=otlp_grpc_metrics_port,
            prom_port=prom_port,
            args=reducer_args
        )

        print("starting kernel_collector_simulator...")
        self.kernel_collector_simulator = kernel_collector_simulator(
            docker=self.docker,
            debug=self.debug,
            intake_host = 'localhost',
            intake_port = intake_port
        )

        time.sleep(120)
        r = requests.get('http://localhost:{}'.format(prom_port))
        prom_text = r.text
        with open("prom.txt", "w") as prom_file:
            prom_file.write(prom_text)

        metrics_bytes = self.otlp_to_prom.download_metrics_file()
        with open('otlp.txt', 'wb') as otlp_file:
            otlp_file.write(metrics_bytes)

        result = {
            'prom': prom_text,
            'otlp': str(metrics_bytes, 'UTF-8') 
        }

        self.reducer.stop()
        self.kernel_collector_simulator.stop()
        self.otlp_to_prom.stop()
    
        self.reducer = None
        self.kernel_collector_simulator = None
        self.otlp_to_prom = None

        return make_object_from_dictionary(result)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.reducer is not None:
            self.reducer.stop()
        if self.kernel_collector_simulator is not None:
            self.kernel_collector_simulator.stop()
        if self.otlp_to_prom is not None:
            self.otlp_to_prom.stop()
