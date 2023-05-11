#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


import socket
import time
import requests

SLEEP_TIMEOUT_SEC = 8

def query_prometheus(q):
    print(q)
    r = requests.get('http://127.0.0.1:9090/api/v1/query?query={}'.format(q))
    if r.status_code != 200:
        raise Exception('prometheus status_code != 200')
    return int(r.json()['data']['result'][0]['value'][1])

def check_udp(host):
    res = query_prometheus('sum(sum_over_time(udp_bytes_az_id{{dip="{}"}}[1h]))'.format(host))
    print('Number of udp bytes in prometheus is {}'.format(res))
    print('SUCCESS' if res > 0 else 'FAILURE')

def send_udp_data(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        n = sock.sendto(bytes('hello', 'utf-8'), (host, port))
        print('sent {} udp bytes to {}:{}'.format(n, host, port))

def main():
    send_udp_data('1.1.1.1', 12345)
    send_udp_data('8.8.8.8', 54321)

    print('Waiting for data...')
    time.sleep(SLEEP_TIMEOUT_SEC)

    check_udp('1.1.1.1')
    check_udp('8.8.8.8')

if __name__ == '__main__':
    main()
