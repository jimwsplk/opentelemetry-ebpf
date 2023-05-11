# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from constants import *


# helpers
def set_state_to_five_tuple(msg):
    data = msg['data']
    return (6, data['src'], data['sport'], data['dest'], data['dport'])

def conntrack_to_five_tuple(msg):
    data = msg['data']
    return (data['proto'], data['src_ip'], data['src_port'], data['dst_ip'], data['dst_port'])


class Index (object):
    '''
    Indexes the different spans so they can be accessed by the entities they refer to,
    for example that a socket be reachable by its five-tuple.
    '''
    
    def __init__(self, parser):
        # index sockets by their five-tuples
        self.socket_five_tuples = defaultdict(list)
        for sk in parser.spans[TCP]:
            for msg in [msg for msg in sk.start if msg['name'] == 'set_state_ipv4']:
                five_tuple = set_state_to_five_tuple(msg)
                self.socket_five_tuples[five_tuple].append(sk)

        
        # index conntrack by their five-tuples
        self.conntrack_five_tuples = defaultdict(list)
        for ct in parser.spans[CONNTRACK]:
            if len(ct.start) > 0:
                five_tuple = conntrack_to_five_tuple(ct.start[-1])
            else:
                # on existing, direction 0 holds the five-tuple of this conntrack
                dir0 = [m for m in ct.existing if m['data']['dir'] == 0]
                if len(dir0) > 0:
                    five_tuple = conntrack_to_five_tuple(dir0[-1])
                else:
                    continue
            
            self.conntrack_five_tuples[five_tuple].append(ct)
        
        # index processes by their PIDs
        self.pids = defaultdict(list)
        for process in parser.spans[PROCESS]:
            for msg in [msg for msg in process.start if msg['name'] == 'pid_info']:
                self.pids[msg['data']['pid']].append(process)
