#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


import time
import requests
from collections import defaultdict

SLEEP_TIMEOUT_SEC = 8

def query_prometheus(q):
    print(q)
    r = requests.get('http://127.0.0.1:9090/api/v1/query?query={}'.format(q))
    if r.status_code != 200:
        raise Exception('prometheus status_code != 200')
    return int(r.json()['data']['result'][0]['value'][1])

def check_http_agg(metric, agg, n):
    r = query_prometheus('sum(sum_over_time({}_{}[1h]))'.format(metric, agg))
    print('number of {}_{} in tsdb = {}'.format(metric, agg, r))
    print('SUCCESS' if r == n else 'FAILURE')

def check_http(metric, n):
    for agg in ['id_az', 'az_id', 'az_az', 'az_role', 'role_az', 'role_role']:
        check_http_agg(metric, agg, n)

def classify_code(http_code):
    if http_code >= 200 and http_code <= 299:
        return 'http_code_200'
    if http_code >= 400 and http_code <= 499:
        return 'http_code_400'
    if http_code >= 500 and http_code <= 599:
        return 'http_code_500'
    return 'http_code_other'

def main():
    http_code_list = [200, 204, 300, 302, 401, 500, 501, 502]
    http_code_count = defaultdict(int)

    for http_code in http_code_list:
        time.sleep(1)
        print(requests.get('http://httpstat.us/{}'.format(http_code), allow_redirects=False))
        http_code_count[classify_code(http_code)] += 1

    print('Waiting for data...')
    time.sleep(SLEEP_TIMEOUT_SEC)

    for code_class, count in http_code_count.items():
        check_http(code_class, count)

if __name__ == '__main__':
    main()
