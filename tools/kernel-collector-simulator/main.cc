// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include <channel/component.h>
#include <channel/reconnecting_channel.h>
#include <collector/k8s/resync_processor.h>
#include <collector/k8s/resync_queue.h>
#include <common/cloud_platform.h>
#include <config/config_file.h>
#include <util/agent_id.h>
#include <util/args_parser.h>
#include <util/log.h>
#include <util/log_whitelist.h>
#include <util/signal_handler.h>
#include <util/system_ops.h>
#include <util/utility.h>

#include <yaml-cpp/yaml.h>

#include <csignal>
#include <cstdlib>
#include <thread>

#include "ingest_json_reader.h"
#include "kernel_collector_simulator.h"

int main(int argc, char *argv[])
{
  constexpr int WRITE_BUFFER_SIZE = 16 * 1024;
  constexpr auto HEARTBEAT = 2s;
  constexpr auto AWS_TIMEOUT = 0ms;

  ::uv_loop_t loop;
  if (auto const error = ::uv_loop_init(&loop)) {
    throw std::runtime_error(::uv_strerror(error));
  }

  cli::ArgsParser parser("Kernel Collector Simulator");
  args::HelpFlag help(*parser, "help", "Display this help menu", {'h', "help"});

  args::ValueFlag<std::string> ingest_json_file(
      *parser,
      "ingest_file",
      "The location of a json file containing kernel to reducer (ingest) messages",
      {"ingest-file"},
      "");

  parser.new_handler<LogWhitelistHandler<channel::Component>>("channel");

  auto &intake_config_handler = parser.new_handler<config::IntakeConfig::ArgsHandler>();

  SignalManager &signal_manager = parser.new_handler<SignalManager>(loop, "kernel-collector-simulator");

  if (auto result = parser.process(argc, argv); !result.has_value()) {
    return result.error();
  }

  std::string const hostname = get_host_name(MAX_HOSTNAME_LENGTH).recover([](auto &error) {
    LOG::error("Unable to retrieve host information from uname: {}", error);
    return "(unknown)";
  });

  auto curl_engine = CurlEngine::create(&loop);

  auto agent_id = gen_agent_id();

  auto intake_config = intake_config_handler.read_config();

  LOG::info("kernel collector simulator started on host {}", hostname);
  LOG::info("agent ID: {}", agent_id);

  KernelCollectorSimulator sim{
      loop, hostname, AWS_TIMEOUT, HEARTBEAT, WRITE_BUFFER_SIZE, std::move(intake_config), ingest_json_file.Get()};
  signal_manager.handle_signals({SIGINT, SIGTERM});

  sim.run_loop();

  return EXIT_SUCCESS;
}
