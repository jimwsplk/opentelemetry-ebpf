# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

import attr
from collections import defaultdict
from intervaltree import IntervalTree
import math
from constants import *
from our_pprint import pprint

@attr.s
class HostVerifier(object):
    '''
    Runs consistency checks on a single host's BPF trace
    '''

    parser = attr.ib()
    index = attr.ib()
    error = attr.ib(default=attr.Factory(lambda : defaultdict(int)))
    warn = attr.ib(default=attr.Factory(lambda : defaultdict(int)))

    def run(self):
        # verify that messages obey lifetime rules
        self.verify_lifetimes(self.parser.spans[TCP], self.parser.largest_timestamp['reset_tcp_counters'])
        self.verify_lifetimes(self.parser.spans[CONNTRACK], self.parser.largest_timestamp['existing_conntrack_tuple'])
        self.verify_lifetimes(self.parser.spans[PROCESS], 0)

        # verify that all TCP sockets also have had their PID reported
        self.check_every_socket_has_a_pid()

        # when a log is reported for TCP sockets, their address should be known
        self.check_every_socket_log_is_after_address_is_known()

    def print(self):
        print ("errors:")
        for (name, count) in self.error.items():
            print ("  {}\t{}".format(count, name))
        print ("warnings:")
        for (name, count) in self.warn.items():
            print ("  {}\t{}".format(count, name))


    def verify_lifetimes(self, spans, steady_state_time):
        ''' Verifies the general lifetime rules
        @param spans: the spans to verify the rules on.
        @param steady_state_time: timestamp when this span type became steady state.

        Rules are:
        * if there is a LOG message, there must be START/EXISTING prior
        * a CLOSE on a span without a START or EXISTING can only happen before steady state
        * if there is a START message, it happens before EXISTING
        
        Warnings on:
        * multiple START, EXISTING or END messages
        '''
        for span in spans:
            start, end = span.lifetime()
            
            # if there is a log message, there must be START/EXISTING prior
            for msg in span.log:
                if msg['timestamp'] < start or start < 0:
                    self.error['{}: LOG before START/EXISTING'.format(span.type)] += 1
                    print('LOG before START/EXISTING:')
                    print('lifetime:', span.lifetime())
                    pprint(span.start)
                    pprint(span.log[0])
                    pprint(span.end)

            # a CLOSE on a span without a START or EXISTING can only happen before steady state
            if start < 0 and end != math.inf:
                if end >= steady_state_time:
                    self.error['{}: CLOSE without START or EXISTING in steady state'.format(span.type)] += 1

            # if there is a START message, it happens before EXISTING
            if len(span.start) > 0 and len(span.existing) > 0:
                max_start = max([m['timestamp'] for m in span.start])
                min_existing = min([m['timestamp'] for m in span.existing])
                if min_existing < max_start:
                    self.error['{}: START after EXISTING'.format(span.type)] += 1
            
            # warn on multiple START EXISTING or END messages
            if len(span.start) > 1:
                self.warn['{}: multiple START messages'.format(span.type)] += 1
            if len(span.existing) > 1:
                self.warn['{}: multiple EXISTING messages'.format(span.type)] += 1
            if len(span.end) > 1:
                self.warn['{}: multiple END messages'.format(span.type)] += 1
    
    def check_map_lifetimes(self, map):
        ''' checks that the spans for each key in the map don't have overlapping lifetimes.
        i.e., there is at most one span associated with the key at any given time'''
        # TODO
        pass

    def check_every_socket_has_a_pid(self):
        ''' ensures we are able to associate all sockets to a pid '''
        steady_state_timestamp = self.parser.largest_timestamp['reset_tcp_counters']

        for sk in self.parser.spans['TCP']:
            start, _ = sk.lifetime()
            # verify we know the PID
            if (len([m for m in sk.start if m['name'] == 'new_sock_created']) == 0 and
                len([m for m in sk.start if m['name'] == 'set_state_ipv4']) > 0
                and start > steady_state_timestamp):
                self.error['TCP without pid after steady state'] += 1
                pprint(sk)
            
            # verify the PID actually exists
            new_sock_created = [m for m in sk.start if m['name'] == 'new_sock_created']
            overlapping = []
            for msg in new_sock_created:
                pid = msg['data']['pid']
                timestamp = msg['timestamp']
                processes = self.index.pids.get(pid, [])
                for process in processes:
                    pstart, pend = process.lifetime()
                    if timestamp > pstart and timestamp < pend:
                        overlapping.append(process)
                
            if len(overlapping) == 0 and start > steady_state_timestamp:
                self.error['TCP socket does not point to an existing PID in steady state'] += 1
                print(sk)
                print(overlapping)
            
            if len(overlapping) > 1:
                self.error['TCP socket is associated with more than one PID'] += 1
        
    def check_every_socket_log_is_after_address_is_known(self):
        ''' when there is an rtt_estimator or syn_timeout etc., we need to have already reported the 
        IP addresses and ports for the socket '''
        
        for sk in self.parser.spans['TCP']:
            if len(sk.log) == 0:
                continue
            
            first_log_timestamp = sk.log[0]['timestamp']

            set_state_messages = [m for m in sk.start if m['name'] in ['set_state_ipv4', 'set_state_ipv6']]
            if len(set_state_messages) == 0:
                self.error['TCP: LOG message without a set_state_ipv{4,6} message'] += 1
                continue
            
            first_set_state_timestamp = set_state_messages[0]['timestamp']

            if first_log_timestamp < first_set_state_timestamp:
                self.error['TCP: LOG message before set_state message'] += 1



            