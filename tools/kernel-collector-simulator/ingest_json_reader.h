/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <generated/ebpf_net/ingest/writer.h>

#include <chrono>
#include <filesystem>
#include <map>

#include <nlohmann/json.hpp>

// Reads a JSON file formatted according to the "intake_wire_to_json" helper tool.
// it is an array of objects, with a field called "name" determining the message.
// the field "timestamp" is the time in nanoseconds.  we use this to diff the
// time between messages to determine an appropriate delay.
//
// we are ignoring the rpc_id and ref fields.
//
// a nested object, called data, contains the message-specific data members.
//
// Example:
// [
//{
//  "name": "new_sock_info",
//  "rpc_id": 302,
//  "timestamp": 1660599615026736400,
//  "ref": 18446636213026701000,
//  "data": {
//    "pid": 1072,
//    "sk": 18446636213026701000
//   }
// },
// ...
// ]
class IngestJsonReader {
public:
  explicit IngestJsonReader(const std::filesystem::path &ingest_file_path, ebpf_net::ingest::Writer &writer);

  std::chrono::nanoseconds next();
  void reset();

private:
  bool write_message(const std::string &message_name, const nlohmann::json &data);

  std::uint32_t make_unique_ip(std::uint32_t ip);

  const std::filesystem::path &ingest_file_path_;

  nlohmann::json ingest_json_;
  nlohmann::json::const_iterator current_;
  ebpf_net::ingest::Writer &writer_;

  std::map<std::uint32_t, std::uint32_t> ip_ip_map_;
  std::string unique_prefix_;
};
