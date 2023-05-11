#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


# we're using attr to easily create objects rather than work with dicts for everything
# can install with `pip3 install attrs` -- note the extra `s` at the end!
import attr

from collections import defaultdict
import socket
import ipaddress
import itertools
import math
import copy
from our_pprint import pprint
from constants import *

@attr.s
class Span(object):
    type = attr.ib()
    start = attr.ib(factory=list)
    existing = attr.ib(factory=list)
    end = attr.ib(factory=list)
    log = attr.ib(factory=list)

    def lifetime(self):
        '''returns the span (start_time, end_time) the object was alive.
        start_time is computed as the first start/existing message
        end_time is the last end message.
        no START/EXISTING messages or no END messages result in -inf, +inf respectively
        '''
        start_time = min(map(msg_timestamp, self.start + self.existing), default=-math.inf)
        end_time = min(map(msg_timestamp, self.end), default=math.inf)
        return (start_time, end_time)


# helpers
def set_state_to_five_tuple(msg):
    data = msg['data']
    return ('TCP', data['src'], data['sport'], data['dest'], data['dport'])

def conntrack_to_five_tuple(msg):
    proto = {6: 'TCP'}
    if msg['name'] == 'nf_conntrack_alter_reply':
        data = msg['data']
        return (proto.get(data['proto'],'unsupported'), data['src_ip'], data['src_port'], data['dst_ip'], data['dst_port'])
    # unsupported message
    raise RuntimeError('unsupported message')

def msg_ntohs(msg, field_names):
    for k in field_names:
        msg['data'][k] = socket.ntohs(msg['data'][k])

def msg_to_ipaddress(msg, field_names):
    for k in field_names:
        msg['data'][k] = str(ipaddress.ip_address(socket.ntohl(msg['data'][k])))

def process_conntrack_message(msg):
    '''fixes port endianity in conntrack messages'''
    if msg['name'] in ['nf_conntrack_alter_reply']:
        for k in ['src_port', 'dst_port', 'nat_src_port', 'nat_dst_port']:
            msg['data'][k] = socket.ntohs(msg['data'][k])
    elif msg['name'] in ['existing_conntrack_tuple']:
        for k in ['src_port', 'dst_port']:
            msg['data'][k] = socket.ntohs(msg['data'][k])

def msg_timestamp(msg):
    return msg['timestamp']

def lifetime_span(obj):
    '''returns the span (start_time, end_time) the object was alive.
    start_time is computed as the first start/existing message
    end_time is the last end message.
    no START/EXISTING messages or no END messages result in -inf, +inf respectively
    '''
    start_time = min(map(msg_timestamp, obj.start + obj.existing), default=-math.inf)
    end_time = min(map(msg_timestamp, obj.end), default=math.inf)
    return (start_time, end_time)


class Parser (object):
    def __init__(self):
        # will count how many messages we didn't have handlers for
        self.unprocessed_message_counts = dict()

        # the spans alive as we're processing a trace
        # this is a dictionary (type, ID) -> Span()
        self.live_spans = dict()

        # the ended spans
        # this is a dictionary (type) -> list of Span()
        self.ended_spans = defaultdict(list)


        # for each message type, what was the largest timestamp it had in the trace.
        # this is used to find if we're in steady-state for different entities
        self.largest_timestamp = dict()

        # keep a count of problems. we'll need to go back and fix those
        self.problems = defaultdict(int)

        # the currently live entries
        self.live_conntrack = dict()
        self.live_tcp = dict()

        # closed entries
        self.closed_conntrack = defaultdict(list)
        self.closed_tcp = defaultdict(list)

        # a dictionary from (protocol, src_ip, src_port, dst_ip, dst_port) to the TCP/... object
        # for live sockets
        self.socket_five_tuples = defaultdict(list)

        # a dictionary from five tuple to Conntrack object
        self.conntrack_five_tuples = defaultdict(list)

    def by_key(self, span_type, span_id):
        ''' returns a span of given ID, creating a new one if it doesn't exist '''
        return self.live_spans.setdefault((span_type, span_id), Span(type=span_type))

    def start(self, span_type, span_id, msg):
        ''' adds a start message '''
        self.by_key(span_type, span_id).start.append(msg)
    
    def existing(self, span_type, span_id, msg):
        ''' adds an existing message '''
        self.by_key(span_type, span_id).existing.append(msg)

    def log(self, span_type, span_id, msg):
        ''' adds a log message '''
        self.by_key(span_type, span_id).log.append(msg)

    def end(self, span_type, span_id, msg):
        ''' processes an end message '''
        span = self.by_key(span_type, span_id)
        span.end.append(msg)
        self.ended_spans[span_type].append(span)
        del self.live_spans[(span_type, span_id)]



    def read(self, filename):
        import json

        with open(filename) as f:
            l = json.load(f)

            # we use message number as timestamp for now
            timestamp = 0
            for msg in l:
                msg['timestamp'] = timestamp
                timestamp += 1

            # FIRST PASS: find the largest timestamp for each message type
            for msg in l:
                self.largest_timestamp[msg['name']] = msg['timestamp']

            # SECOND PASS: process messages
            for msg in l:
                self.process_message(msg['timestamp'], msg)

        self.spans = copy.copy(self.ended_spans)
        for (span_type, _), span in self.live_spans.items():
            self.spans.setdefault(span_type, []).append(span)

        print ("unprocessed messages:")
        for (name, count) in self.unprocessed_message_counts.items():
            print ("  {}\t{}".format(count, name))

    def process_message(self, timestamp, msg):
        handler_func = getattr(self, msg['name'], None)
        if handler_func is not None:
            handler_func(timestamp, msg)
        else:
            # we don't have a method for the message, count it
            self.unprocessed_message_counts[msg['name']] = self.unprocessed_message_counts.get(msg['name'],0) + 1

    ## STEADY STATE
    def is_conntrack_steady_state(self, timestamp):
        return (timestamp > self.largest_timestamp['existing_conntrack_tuple'])

    def is_tcp_steady_state(self, timestamp):
        return (timestamp > self.largest_timestamp['reset_tcp_counters'])

    ## HANDLERS - NAT
    def existing_conntrack_tuple(self, timestamp, msg):
        msg_ntohs(msg, ['src_port', 'dst_port'])
        msg_to_ipaddress(msg, ['src_ip', 'dst_ip'])
        self.existing(CONNTRACK, msg['data']['ct'], msg)

    def nf_conntrack_alter_reply(self, timestamp, msg):
        msg_ntohs(msg, ['src_port', 'dst_port', 'nat_src_port', 'nat_dst_port'])
        msg_to_ipaddress(msg, ['src_ip', 'dst_ip', 'nat_src_ip', 'nat_dst_ip'])
        self.start(CONNTRACK, msg['data']['ct'], msg)

    def nf_nat_cleanup_conntrack(self, timestamp, msg):
        msg_ntohs(msg, ['src_port', 'dst_port'])
        msg_to_ipaddress(msg, ['src_ip', 'dst_ip'])
        self.end(CONNTRACK, msg['data']['ct'], msg)

    # HANDLERS - TCP
    def new_sock_created(self, timestamp, msg):
        self.start(TCP, msg['data']['sk'], msg)

    def set_state_ipv6(self, timestamp, msg):
        # msg_to_ipaddress(msg, ['src', 'dest'])
        self.start(TCP, msg['data']['sk'], msg)

    def set_state_ipv4(self, timestamp, msg):
        msg_to_ipaddress(msg, ['src', 'dest'])
        self.start(TCP, msg['data']['sk'], msg)
        

    def close_sock_info(self, timestamp, msg):
        self.end(TCP, msg['data']['sk'], msg)
    
    def reset_tcp_counters(self, timestamp, msg):
        self.start(TCP, msg['data']['sk'], msg)

    def rtt_estimator(self, timestamp, msg):
        self.log(TCP, msg['data']['sk'], msg)

    
    # PROCESS    

    def pid_info(self, timestamp, msg):
        self.start(PROCESS, msg['data']['pid'], msg)

    def pid_set_comm(self, timestamp, msg):
        self.log(PROCESS, msg['data']['pid'], msg)

    def pid_close(self, timestamp, msg):
        self.end(PROCESS, msg['data']['pid'], msg)
    
    # BPF LOG
    def bpf_log(self, timestamp, msg):
        print(msg)


import os.path
import glob
# files = ['/Users/yonch/Downloads/bpf.dump/flowmill-kernel-collector.bpf.messages.flowmill-k8s-agent-mxpj9.json']
#files = glob.glob(os.path.expanduser('~/Downloads/bpf.dump/*.json'))
files = ['/tmp/messages.json']
for filename in files:
    print(filename)
    p = Parser()
    p.read(filename)

    from index import Index
    index = Index(p)

    for tup, conntracks in index.conntrack_five_tuples.items():
        if tup[1] == '100.96.7.222' and tup[3] == '100.65.32.140':
            matches = [ct for ct in conntracks if len([m for m in ct.start if m['name'] == 'nf_conntrack_alter_reply' and m['data']['nat_dst_ip'] == '100.96.7.98']) > 0]
            if len(matches) > 0:
                # print(tup, conntracks)

                # now check that we see the inverse socket
                for ct in matches:
                    msgs = [m for m in ct.start if m['name'] == 'nf_conntrack_alter_reply' and m['data']['nat_dst_ip'] == '100.96.7.98']
                    data = msgs[-1]['data']
                    tuple = (6, data['nat_dst_ip'], data['nat_dst_port'], data['nat_src_ip'], data['nat_src_port'])
                    sks = index.socket_five_tuples.get(tuple, [])
                    if (len(sks) != 1):
                        pprint(tuple)
                        pprint(ct)
                        pprint ([sk.start for sk in sks])
                        print('forward tuples:')
                        pprint ([(sk.start, (sk.log), sk.end)  for sk in index.socket_five_tuples.get(tup, [])])

    from host_verifier import HostVerifier
    v = HostVerifier(p,index)
    v.run()
    v.print()

# ip_addrs = {638083172: 'pipeline-pod', 503865444: 'prometheus-pod', 2651865188: 'pipeline-svc'}

# five_tuple = ('TCP', 503865444, 43086, 2651865188, 7020) # prom-external -> flowtune-server.svc.cluster.local
# other_five_tuples = [('TCP', 503865444, 43086, 638083172, 7010), # prom-external -> pipeline ("old" conntrack)
#                         ('TCP', 503865444, 10134, 638083172, 7010)] # prom-external -> pipeline ("correct" conntrack)
# def reverse_five_tuple(tup):
#     return (tup[0], tup[3], tup[4], tup[1], tup[2])

# ports = [five_tuple[2], five_tuple[4]]
# import socket
# import pprint
# hports = [socket.ntohs(x) for x in ports]

# for i, tup in enumerate([five_tuple] + other_five_tuples):
#     print('tuple {} - {}:'.format(i, tup))
#     print('\tsockets:', p.socket_five_tuples.get(tup,[]))
#     pprint.pprint([sk.start for sk in p.socket_five_tuples.get(tup,[])])
#     pprint.pprint([sk.set_state for sk in p.socket_five_tuples.get(tup,[])])
#     pprint.pprint([sk.end for sk in p.socket_five_tuples.get(tup,[])])
#     print('\tsockets with reverse five_tuple:', p.socket_five_tuples.get(reverse_five_tuple(tup), []))
#     pprint.pprint([sk.start for sk in p.socket_five_tuples.get(reverse_five_tuple(tup),[])])
#     pprint.pprint([sk.set_state for sk in p.socket_five_tuples.get(reverse_five_tuple(tup),[])])
#     pprint.pprint([sk.end for sk in p.socket_five_tuples.get(reverse_five_tuple(tup),[])])
#     print('\tconntrack with five_tuple:')
#     pprint.pprint(p.conntrack_five_tuples.get(tup,[]))
#     pprint.pprint([ct.start for ct in p.conntrack_five_tuples.get(tup,[])])

# for tup, sks in p.socket_five_tuples.items():
#     if tup[2] in ports and tup[4] in ports:
#         pprint.pprint(sks)
# print('sockets with five_tuple:', p.socket_five_tuples[five_tuple])
# print('sockets with reverse five_tuple:', p.socket_five_tuples[reverse_five_tuple(five_tuple)])
# print('conntrack with five_tuple:')
# pprint.pprint(p.conntrack_five_tuples[five_tuple])