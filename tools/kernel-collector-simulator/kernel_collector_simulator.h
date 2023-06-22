/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <channel/callbacks.h>
#include <scheduling/interval_scheduler.h>
#include <scheduling/job.h>
#include <util/curl_engine.h>
#include <util/logger.h>

#include <chrono>
#include <string>

#include "ingest_connection.h"
#include "ingest_json_reader.h"

class KernelCollectorSimulator : channel::Callbacks {
public:
  explicit KernelCollectorSimulator(
      ::uv_loop_t &loop,
      std::string_view hostname,
      std::chrono::milliseconds aws_metadata_timeout,
      std::chrono::milliseconds heartbeat_interval,
      std::size_t buffer_size,
      config::IntakeConfig intake_config,
      const std::filesystem::path &json_file);
  ~KernelCollectorSimulator();

  void run_loop();

  ::uv_loop_t &get_loop() { return loop_; }

private:
  scheduling::JobFollowUp callback();

  void on_error(int err);
  void on_connected();

  ::uv_loop_t &loop_;
  IngestConnection connection_;
  logging::Logger log_;
  scheduling::IntervalScheduler scheduler_;
  std::unique_ptr<IngestJsonReader> ingest_json_reader_;
  bool stopped_;
};