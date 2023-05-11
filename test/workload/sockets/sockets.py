#!/usr/bin/env python3
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


import argparse
import asyncio
import random
import string


SERVER_ADDR = "127.0.0.1"
SERVER_PORT_BASE = 13000


def random_str(length=16):
    return "".join([random.choice(string.ascii_letters) for _ in range(length)])


async def handle_client(reader, writer):
    msg = await reader.read(1024)

    writer.write(msg)
    await writer.drain()

    writer.close()
    await writer.wait_closed()


async def do_client(port):
    reader, writer = await asyncio.open_connection(SERVER_ADDR, port)

    msg_send = random_str().encode()

    writer.write(msg_send)
    await writer.drain()

    msg_recv = await reader.read(1024)

    writer.close()
    await writer.wait_closed()

    assert msg_send == msg_recv


def main():
    parser = argparse.ArgumentParser(description="Establish TCP connections.")
    parser.add_argument("servers", type=int, nargs="?", default=10,
                        help="number of listeners to establish")
    parser.add_argument("batches", type=int, nargs="?", default=10,
                        help="number of client batches to run")
    args = parser.parse_args()

    n_servers = args.servers
    n_batches = args.batches

    loop = asyncio.get_event_loop()

    print("creating servers")
    for server_num in range(n_servers):
        server = asyncio.start_server(handle_client, SERVER_ADDR,
                                      SERVER_PORT_BASE + server_num)
        loop.run_until_complete(server)

    print("creating clients")
    for batch_num in range(n_batches):
        print("client batch", batch_num)
        clients = [do_client(SERVER_PORT_BASE + server_num) for server_num in range(n_servers)]
        loop.run_until_complete(asyncio.gather(*clients))

    print("sleeping")
    loop.run_until_complete(asyncio.sleep(5))


if __name__ == "__main__":
    main()
