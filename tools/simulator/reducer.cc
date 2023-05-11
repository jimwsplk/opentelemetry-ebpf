// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include <config.h>

#include "generator.h"
#include "random.h"

#include <reducer/otlp_grpc_formatter.h>
#include <reducer/otlp_grpc_publisher.h>
#include <reducer/prometheus_publisher.h>
#include <reducer/publisher.h>
#include <reducer/tsdb_format.h>
#include <reducer/util/signal_handler.h>

#include <util/args_parser.h>
#include <util/log.h>

#include <csignal>
#include <functional>
#include <memory>
#include <thread>
#include <vector>

int main(int argc, char **argv)
{
  cli::ArgsParser parser("sim-reducer");

  args::HelpFlag help(*parser, "help", "Display this help menu.", {'h', "help"});
  args::ValueFlag<std::string> metrics_format_flag(
      *parser, "format", "Format of metrics output", {"metrics-format"}, "prometheus");
  args::ValueFlag<uint32_t> num_shards_flag(*parser, "count", "How many output shards to run.", {"num-shards"}, 1);
  args::ValueFlag<std::string> prom_bind(*parser, "addr:port", "Bind address for scraping.", {"prom"}, "0.0.0.0:7010");
  args::ValueFlag<uint32_t> num_flows(*parser, "count", "How many random flows to generate.", {"num-flows"}, 10);
  args::ValueFlag<uint32_t> interval_flag(
      *parser, "interval", "Generate metrics every 'interval' seconds.", {'i', "interval"}, 30);
  args::ValueFlag<std::string> dimensions_path(
      *parser, "path", "Path to YAML file containing values for each dimension.", {"dimensions"});

  args::Flag enable_otlp_grpc_metrics(
      *parser, "enable_otlp_grpc_metrics", "Enables sending metrics via OTLP gRPC", {"enable-otlp-grpc-metrics"});
  args::ValueFlag<std::string> otlp_grpc_metrics_address(
      *parser,
      "otlp_grpc_metrics_address",
      "Network address to send OTLP gRPC metrics",
      {"otlp-grpc-metrics-host"},
      "localhost");
  args::ValueFlag<u32> otlp_grpc_metrics_port(
      *parser, "otlp_grpc_metrics_port", "TCP port to send OTLP gRPC metrics", {"otlp-grpc-metrics-port"}, 4317);
  args::ValueFlag<int> otlp_grpc_batch_size_flag(*parser, "otlp_grpc_batch_size", "", {"otlp-grpc-batch-size"}, 1000);

  if (auto result = parser.process(argc, argv); !result) {
    return result.error();
  }

  global_otlp_grpc_batch_size = otlp_grpc_batch_size_flag.Get();

  reducer::TsdbFormat metrics_format;
  if (!enum_from_string(metrics_format_flag.Get(), metrics_format)) {
    LOG::critical("Unknown TSDB format: {}", metrics_format_flag.Get());
    return 1;
  }

  const std::chrono::seconds interval(interval_flag.Get());
  const size_t num_shards = num_shards_flag.Get();

  random_init();

  if (dimensions_path) {
    try {
      random_load_dimensions(dimensions_path.Get());
    } catch (std::exception const &e) {
      LOG::critical("Unable to load file '{}': {}.", dimensions_path.Get(), e.what());
      return 1;
    }
  }

  std::unique_ptr<reducer::Publisher> metrics_publisher;
  if (enable_otlp_grpc_metrics.Get()) {
    metrics_publisher = std::make_unique<reducer::OtlpGrpcPublisher>(
        num_shards, std::string(otlp_grpc_metrics_address.Get() + ":" + std::to_string(otlp_grpc_metrics_port.Get())));
    metrics_format = reducer::TsdbFormat::otlp_grpc;
  } else {
    metrics_publisher =
        std::make_unique<reducer::PrometheusPublisher>(reducer::PrometheusPublisher::PORT_RANGE, num_shards, prom_bind.Get());
  }

  // A generator for each "shard".
  //
  std::vector<std::unique_ptr<Generator>> generators;
  for (size_t i = 0; i < num_shards; ++i) {
    generators.emplace_back(
        std::make_unique<Generator>(metrics_publisher->make_writer(i), metrics_format, num_flows.Get(), interval));
  }

  auto signal_handler = std::make_unique<reducer::SignalHandler>();

  // Terminate on INT and TERM signals.
  //
  auto on_terminate = [&](int signum) {
    LOG::debug("received signal {}", signum);
    for (auto &generator : generators) {
      generator->stop_async();
    }
    signal_handler->stop_async();
  };
  signal_handler->handle(SIGINT, on_terminate);
  signal_handler->handle(SIGTERM, on_terminate);

  // A thread to run each generator.
  //
  std::vector<std::thread> threads;
  for (auto &generator : generators) {
    threads.emplace_back(&Generator::run, generator.get());
  }

  // We'll handle signals in its own thread.
  threads.emplace_back(&reducer::SignalHandler::run, signal_handler.get());

  LOG::info("running");

  // Wait until all threads terminate.
  //
  for (auto &thread : threads) {
    thread.join();
  }

  LOG::info("shutting down");

  metrics_publisher->shutdown();

  LOG::info("exiting");

  return 0;
}
