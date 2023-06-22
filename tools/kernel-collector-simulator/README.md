This tool allows one to simulate a kernel collector by playing back a json file that contains a collection of messages.
This file can either be composed manually or by dumping the ingest messages sent from a kernel collector in raw/binary format.
This raw file needs to be then passed through the "intake_wire_to_json" tool to convert it to json.  

If one wishes to compose a file manually, the file should be an array of messages.  Each message object needs a name, timestamp, and beneath this, the message specific payload in a sub-objected called "data". This conforms to the file format used by intake_wire_to_json.

For example:
```
[
...
{
  "name": "new_sock_info",
  "timestamp": 1660599615026736400,
  "data": {
    "pid": 1072,
    "sk": 18446636213026701000
   }
},
...
]
```

The idea is to precisely control the input to the reducer to observe how it behaves.  This could be useful for troubleshooting customer issues; load testing; or testing the reducer in isolation.

Like the kernel collector, the environment variables `EBPF_NET_INTAKE_HOST` and `EBPF_NET_INTAKE_PORT` must be defined.

A command-line argument `ingest-file` must be supplied if you are running the tool directly.  This is the path to the file that will be played back by the simulator.

If running your are running within the context of a container, mount a directory containing a file called "ingest.json" to /var/run/kernel-collector-simulator.
