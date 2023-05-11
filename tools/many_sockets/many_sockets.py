#!/usr/bin/python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

import asyncio

N_SERVERS = 1000
N_CLIENTS_PER_SERVER = 100
INITIAL_PORT = 13000

# the servers awaiting connections
servers = []

# the client connections that servers accepted
client_connections = []

# the clients themselves
clients = []

async def handle_new_client(reader, writer):
    client_connections.append([reader, writer])

async def start_client(port):
    reader, writer = await asyncio.open_connection('127.0.0.1', 
                                                   port, loop=loop)
    clients.append([reader,writer])

async def wait(n_seconds):
    await asyncio.sleep(n_seconds)

loop = asyncio.get_event_loop()
print("creating servers")
for i in range(N_SERVERS):
    coro = asyncio.start_server(handle_new_client, '127.0.0.1', 
                                  INITIAL_PORT + i, loop=loop)
    server = loop.run_until_complete(coro)
    servers.append(server)

print("creating clients")
for j in range(N_CLIENTS_PER_SERVER):
    print ("client batch ", j)
    loop.run_until_complete(asyncio.gather(*[start_client(INITIAL_PORT + i) for i in range(N_SERVERS)]))

print("sleeping 600 seconds")
loop.create_task(wait(600))
loop.run_forever()

