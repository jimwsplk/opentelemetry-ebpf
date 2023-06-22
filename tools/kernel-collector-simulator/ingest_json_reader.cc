// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0
#include "ingest_json_reader.h"

#include <fstream>
#include <iostream>
#include <stdexcept>

#include <spdlog/fmt/fmt.h>
#include <util/cgroup_parser.h>
#include <util/log.h>

IngestJsonReader::IngestJsonReader(const std::filesystem::path &ingest_file_path, ebpf_net::ingest::Writer &writer)
    : ingest_file_path_{ingest_file_path}, writer_{writer}
{
  std::ifstream ingest_file{ingest_file_path};
  if (!ingest_file) {
    throw std::invalid_argument(fmt::format("could not open {} for reading", ingest_file_path.string()));
  }

  ingest_json_ = nlohmann::json::parse(ingest_file);
  if (ingest_json_.size() < 2) {
    // simplifying assumption
    throw std::invalid_argument("json file must have at least 2 messages to playback");
  }
  current_ = ingest_json_.begin();

  srand(time(NULL));

  // make a unique pod id, container id, and process
  for (int ii = 0; ii < 6; ++ii) {
    int replacement = rand() % 16;
    if (replacement < 10) {
      unique_prefix_ += '0' + replacement;
    } else {
      replacement -= 10;
      unique_prefix_ += 'a' + replacement;
    }
  }
}

std::uint32_t IngestJsonReader::make_unique_ip(std::uint32_t ip)
{
  auto find_itr = ip_ip_map_.find(ip);
  if (find_itr == ip_ip_map_.end()) {
    std::uint32_t ret = rand();
    ip_ip_map_[ip] = ret;
    return ret;
  }

  return find_itr->second;
}

void IngestJsonReader::reset()
{
  current_ = ingest_json_.begin();
}

std::chrono::nanoseconds IngestJsonReader::next()
{
  const std::string &message_name = (*current_)["name"];
  const auto &data = (*current_)["data"];

  try {
    write_message(message_name, data);
  } catch (const nlohmann::detail::type_error &e) {
    // we'll let everything else percolate up, but it would be good to log the
    // typos or whatever here so they can be fixed, but not interrupt playback
    LOG::error("type error from json {} for message {}", e.what(), message_name);
  }

  // find the defer period
  nlohmann::json::const_iterator next = current_ + 1;
  if (next == ingest_json_.end()) {
    // wrap around and immediately emit
    // TODO maybe a flag to control restart vs. terminating?
    LOG::debug("EOF reached, restarting");
    current_ = ingest_json_.begin();
    return 0ns;
  }

  const std::string &next_message = (*next)["name"];
  std::uint64_t cur_message_time = (*current_)["timestamp"];
  std::uint64_t next_message_time = (*next)["timestamp"];
  std::chrono::nanoseconds defer = 0ns;

  if (next_message_time > cur_message_time) {
    defer = std::chrono::nanoseconds(next_message_time - cur_message_time);
  } else {
    // out of order messages or threading?
    defer = std::chrono::nanoseconds(cur_message_time - next_message_time);
  }

  LOG::debug("next message {} in {}ms ({}ns) ", next_message, defer / 1.0ms, defer.count());

  current_++;
  return std::chrono::nanoseconds(defer);
}

bool IngestJsonReader::write_message(const std::string &message_name, const nlohmann::json &data)
{
  // FUTURE this is probably OK for this little simulator but it would be nice
  // to have this sort of mapping handled by renderc / meta-programming
  // this is brittle and prone to needing upkeep of the sort that is often
  // forgotten.

  if (message_name == "pid_info") {
    std::uint32_t pid = data["pid"];
    std::string comm_str = unique_prefix_;
    comm_str += data["comm"];
    std::uint8_t comm[16];
    memcpy(comm, comm_str.data(), std::min(comm_str.size(), sizeof(comm)));

    LOG::debug("write pid_info: pid {} comm {}", pid, comm);
    writer_.pid_info(pid, comm);
    return true;
  }

  if (message_name == "pid_close_info") {
    std::uint32_t pid = data["pid"];
    std::string comm_str = unique_prefix_;
    comm_str += data["comm"];
    std::uint8_t comm[16];
    memcpy(comm, comm_str.data(), std::min(comm_str.size(), sizeof(comm)));

    LOG::debug("write pid_close_info: pid {} comm {}", pid, comm);
    writer_.pid_close_info(pid, comm);
    return true;
  }

  if (message_name == "pid_info_create") {
    std::uint32_t pid = data["pid"];
    std::string comm_str = unique_prefix_;
    comm_str += data["comm"];
    std::uint8_t comm[16];
    memcpy(comm, comm_str.data(), std::min(comm_str.size(), sizeof(comm)));
    std::uint64_t cgroup = data["cgroup"];
    std::int32_t parent_pid = data["parent_pid"];
    std::string cmdline = data["cmdline"];
    LOG::debug(
        "write pid_info_create: pid {} comm {} cgroup {} parent_pid {} cmdline {}", pid, comm, cgroup, parent_pid, cmdline);
    writer_.pid_info_create(pid, comm, cgroup, parent_pid, jb_blob(cmdline));
    return true;
  }

  if (message_name == "pid_cgroup_move") {
    std::uint32_t pid = data["pid"];
    std::uint64_t cgroup = data["cgroup"];

    LOG::debug("write pid_cgroup_move: pid {} cgroup {}", pid, cgroup);
    writer_.pid_cgroup_move(pid, cgroup);
    return true;
  }

  if (message_name == "pid_set_comm") {
    std::uint32_t pid = data["pid"];
    std::string comm_str = unique_prefix_;
    comm_str += data["comm"];

    std::uint8_t comm[16];
    memcpy(comm, comm_str.data(), std::min(comm_str.size(), sizeof(comm)));

    LOG::debug("write pid_set_comm: pid {} comm {}", pid, comm);
    writer_.pid_set_comm(pid, comm);
    return true;
  }

  if (message_name == "pid_set_cmdline") {
    std::uint32_t pid = data["pid"];
    std::string cmdline = data["cmdline"];

    LOG::debug("write pid_set_cmdline: pid {} cmdline {}", pid, cmdline);
    writer_.pid_set_cmdline(pid, jb_blob(cmdline));
    return true;
  }

  if (message_name == "tracked_process_start") {
    std::uint64_t _ref = data["_ref"];

    LOG::debug("write tracked_process_start: _ref {}");
    writer_.tracked_process_start(_ref);
    return true;
  }

  if (message_name == "tracked_process_end") {
    std::uint64_t _ref = data["_ref"];

    LOG::debug("write tracked_process_end: _ref {}");
    writer_.tracked_process_end(_ref);
    return true;
  }

  if (message_name == "set_tgid") {
    std::uint64_t _ref = data["_ref"];
    std::uint32_t tgid = data["tgid"];

    LOG::debug("write set_tgid: _ref {} tgid {}", _ref, tgid);
    writer_.set_tgid(_ref, tgid);
    return true;
  }

  if (message_name == "set_cgroup") {
    std::uint64_t _ref = data["_ref"];
    std::uint64_t cgroup = data["cgroup"];

    LOG::debug("write set_cgroup: _ref {} cggroup {}", _ref, cgroup);
    writer_.set_cgroup(_ref, cgroup);
    return true;
  }

  if (message_name == "set_command") {
    std::uint64_t _ref = data["_ref"];
    std::string command = data["command"];

    LOG::debug("write set_command: _ref {} command {}", _ref, command);
    writer_.set_command(_ref, jb_blob(command));
    return true;
  }

  if (message_name == "pid_exit") {
    std::uint64_t _ref = data["_ref"];
    std::uint32_t tgid = data["tgid"];
    std::uint32_t pid = data["pid"];
    std::int32_t exit_code = data["exit_code"];

    LOG::debug("write pid_exit: _ref {} tgid {} pid {} exit_code {}", _ref, tgid, pid, exit_code);
    writer_.pid_exit(_ref, tgid, pid, exit_code);
    return true;
  }

  if (message_name == "cgroup_create") {
    std::uint64_t cgroup = data["cgroup"];
    std::uint64_t cgroup_parent = data["cgroup_parent"];
    std::string cgroup_name = data["name"];
    std::uint8_t name[256];

    CGroupParser parser{cgroup_name};
    auto cgroup_info = parser.get();
    if (cgroup_info.valid) {
      if (!cgroup_info.pod_id.empty()) {
        auto idx = cgroup_name.find(cgroup_info.pod_id.substr(0, 6));
        if (idx != std::string::npos) {
          cgroup_name.replace(idx, unique_prefix_.size(), unique_prefix_);
        }
      }

      if (!cgroup_info.container_id.empty()) {
        auto idx = cgroup_name.find(cgroup_info.container_id.substr(0, 6));
        if (idx != std::string::npos) {
          cgroup_name.replace(idx, unique_prefix_.size(), unique_prefix_);
        }
      }
    }

    memcpy(name, cgroup_name.data(), std::min(cgroup_name.size(), sizeof(name)));
    LOG::debug("write cgroup_create: cgroup {} cgroup_parent {} name {}", cgroup, cgroup_parent, name);

    writer_.cgroup_create(cgroup, cgroup_parent, name);
    return true;
  }

  if (message_name == "cgroup_close") {
    std::uint64_t cgroup = data["cgroup"];

    LOG::debug("write cgroup_close: cgroup {}", cgroup);

    writer_.cgroup_close(cgroup);
    return true;
  }

  if (message_name == "container_metadata") {
    std::uint64_t cgroup = data["cgroup"];
    std::string id = data["id"];
    std::string name = data["name"];
    std::string image = data["image"];
    std::string ip_addr = data["ip_addr"];
    std::string cluster = data["cluster"];
    std::string container_name = data["container_name"];
    std::string task_family = data["task_family"];
    std::string task_version = data["task_version"];
    std::string ns = data["ns"];

    LOG::debug(
        "write container_metadata: cgroup {}",
        cgroup,
        id,
        name,
        image,
        ip_addr,
        cluster,
        container_name,
        task_family,
        task_version,
        ns);
    writer_.container_metadata(
        cgroup,
        jb_blob(id),
        jb_blob(name),
        jb_blob(image),
        jb_blob(ip_addr),
        jb_blob(cluster),
        jb_blob(container_name),
        jb_blob(task_family),
        jb_blob(task_version),
        jb_blob(ns));
    return true;
  }

  if (message_name == "new_sock_info") {
    std::uint32_t pid = data["pid"];
    std::uint64_t sk = data["sk"];

    LOG::debug("write new_sock_info: pid {} sk {}", pid, sk);

    writer_.new_sock_info(pid, sk);
    return true;
  }

  if (message_name == "set_state_ipv4") {
    std::uint32_t dest = make_unique_ip(data["dest"]);
    std::uint32_t src = make_unique_ip(data["src"]);
    std::uint16_t dport = data["dport"];
    std::uint16_t sport = data["sport"];
    std::uint64_t sk = data["sk"];
    std::uint32_t tx_rx = data["tx_rx"];

    LOG::debug("write set_state_ipv4: dest {} src {} dport {} sport {} sk {} tx_rx {}", dest, src, dport, sport, sk, tx_rx);

    writer_.set_state_ipv4(dest, src, dport, sport, sk, tx_rx);
    return true;
  }

  if (message_name == "set_state_ipv6") {
    std::string dest_str = data["dest"];
    std::uint8_t dest[16];
    memcpy(dest, dest_str.data(), std::min(dest_str.size(), sizeof(dest)));
    std::string src_str = data["src"];
    std::uint8_t src[16];
    memcpy(src, src_str.data(), std::min(src_str.size(), sizeof(src)));
    std::uint16_t dport = data["dport"];
    std::uint16_t sport = data["sport"];
    std::uint64_t sk = data["sk"];
    std::uint32_t tx_rx = data["tx_rx"];

    LOG::debug(
        "write set_state_ipv6: dest {} src {} dport {} sport {} sk {} tx_rx {}", dest_str, src_str, dport, sport, sk, tx_rx);

    writer_.set_state_ipv6(dest, src, dport, sport, sk, tx_rx);
    return true;
  }

  if (message_name == "socket_stats") {
    std::uint64_t sk = data["sk"];
    std::uint64_t diff_bytes = data["diff_bytes"];
    std::uint32_t diff_delivered = data["diff_delivered"];
    std::uint32_t diff_retrans = data["diff_retrans"];
    std::uint32_t max_srtt = data["max_srtt"];
    std::uint8_t is_rx = data["is_rx"];

    LOG::debug(
        "write socket_stats: sk {} diff_bytes {} diff_delivered {} diff_retrans {} max_srtt {} is_rx {}",
        sk,
        diff_bytes,
        diff_delivered,
        diff_retrans,
        max_srtt,
        is_rx);

    writer_.socket_stats(sk, diff_bytes, diff_delivered, diff_retrans, max_srtt, is_rx);
    return true;
  }

  if (message_name == "nat_remapping") {
    std::uint64_t sk = data["sk"];
    std::uint32_t src = make_unique_ip(data["src"]);
    std::uint32_t dst = make_unique_ip(data["dst"]);
    std::uint16_t sport = data["sport"];
    std::uint16_t dport = data["dport"];

    LOG::debug("write nat_remapping: sk {} src {} dst {} sport {} dport {}", sk, src, dst, sport, dport);

    writer_.nat_remapping(sk, src, dst, sport, dport);
    return true;
  }

  if (message_name == "close_sock_info") {
    std::uint64_t sk = data["sk"];
    LOG::debug("write close_sock_info: sk {}", sk);

    writer_.close_sock_info(sk);
    return true;
  }

  if (message_name == "http_response") {
    std::uint64_t sk = data["sk"];
    std::uint32_t pid = data["pid"];
    std::uint16_t code = data["code"];
    std::uint64_t latency_ns = data["latency_ns"];
    std::uint8_t client_server = data["client_server"];

    LOG::debug(
        "write http_response: sk {} pid {} code {} latency_ns {} client_server {}", sk, pid, code, latency_ns, client_server);

    writer_.http_response(sk, pid, code, latency_ns, client_server);
    return true;
  }

  if (message_name == "tcp_reset") {
    std::uint64_t sk = data["sk"];
    std::uint8_t is_rx = data["is_rx"];

    LOG::debug("write tcp_reset: sk {} is_rx {}", sk, is_rx);
    writer_.tcp_reset(sk, is_rx);
    return true;
  }

  if (message_name == "private_ipv4_addr") {
    std::uint32_t addr = data["addr"];
    std::string vpc_id_str = data["vpc_id"];
    std::uint8_t vpc_id[22];
    memcpy(vpc_id, vpc_id_str.data(), std::min(vpc_id_str.size(), sizeof(vpc_id)));

    LOG::debug("write private_ipv4_addr: addr {} vpc_id {}", addr, vpc_id);
    writer_.private_ipv4_addr(addr, vpc_id);
    return true;
  }

  if (message_name == "udp_new_socket") {
    std::uint32_t pid = data["pid"];
    std::uint32_t sk_id = data["sk_id"];
    std::string laddr_str = data["laddr"];
    std::uint8_t laddr[16];
    memcpy(laddr, laddr_str.data(), std::min(laddr_str.size(), sizeof(laddr)));
    std::uint16_t lport = data["lport"];
    LOG::debug("write udp_new_socket: pid {} sk_id {} laddr {} lport {}", pid, sk_id, laddr, lport);

    writer_.udp_new_socket(pid, sk_id, laddr, lport);
    return true;
  }

  if (message_name == "udp_stats_addr_changed_v4") {
    std::uint32_t sk_id = data["sk_id"];
    std::uint8_t is_rx = data["is_rx"];
    std::uint32_t packets = data["packets"];
    std::uint32_t bytes = data["bytes"];
    std::uint32_t raddr = data["raddr"];
    std::uint16_t rport = data["rport"];

    LOG::debug(
        "write udp_stats_addr_changed_v4: sk_id {} is_rx {} packets {}, bytes {}, raddr {}, rport {}",
        sk_id,
        is_rx,
        packets,
        bytes,
        raddr,
        rport);

    writer_.udp_stats_addr_changed_v4(sk_id, is_rx, packets, bytes, raddr, rport);
    return true;
  }

  if (message_name == "udp_stats_addr_unchanged") {
    std::uint32_t sk_id = data["sk_id"];
    std::uint8_t is_rx = data["is_rx"];
    std::uint32_t packets = data["packets"];
    std::uint32_t bytes = data["bytes"];

    LOG::debug("write udp_stats_addr_unchanged: sk_id {} is_rx {} packets {}, bytes {}", sk_id, is_rx, packets, bytes);

    writer_.udp_stats_addr_unchanged(sk_id, is_rx, packets, bytes);
    return true;
  }

  LOG::debug("no handler for message {}, skipping.", message_name);
  return false;
}
