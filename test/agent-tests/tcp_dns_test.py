#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


import time
import requests

SLEEP_TIMEOUT_SEC = 8

def query_prometheus(q):
    print(q)
    r = requests.get('http://127.0.0.1:9090/api/v1/query?query={}'.format(q))
    if r.status_code != 200:
        raise Exception('prometheus status_code != 200')
    return int(r.json()['data']['result'][0]['value'][1])

def check_dns_agg(agg, drole, n):
    r = query_prometheus('sum(sum_over_time(bytes_{}{{drole="{}"}}[1h]))'.format(agg, drole))
    print('number of bytes_{} in tsdb = {}'.format(agg, r))
    print('SUCCESS' if r == n else 'FAILURE')

def check_dns(drole, n):
    for agg in ['id_az', 'az_id', 'az_az', 'az_role', 'role_az', 'role_role']:
        check_dns_agg(agg, drole, n)

def main():
    print(requests.get('http://nyt.com', allow_redirects=False))
    print(requests.get('http://google.com', allow_redirects=False))

    time.sleep(SLEEP_TIMEOUT_SEC)

    check_dns('nyt.com', 140) # num bytes in 301 response
    check_dns('google.com', 142) # num bytes in 301 response

if __name__ == '__main__':
    main()
