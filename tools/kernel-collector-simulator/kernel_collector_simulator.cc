// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include "kernel_collector_simulator.h"

#include <scheduling/interval_scheduler.h>
#include <util/jitter.h>
#include <util/log.h>
#include <util/log_formatters.h>

#include <functional>
#include <stdexcept>
#include <thread>

namespace {

constexpr auto RECONNECT_DELAY = 5s;
constexpr std::chrono::milliseconds RECONNECT_JITTER = 1s;

} // namespace

KernelCollectorSimulator::KernelCollectorSimulator(
    ::uv_loop_t &loop,
    std::string_view hostname,
    std::chrono::milliseconds aws_metadata_timeout,
    std::chrono::milliseconds heartbeat_interval,
    std::size_t buffer_size,
    config::IntakeConfig intake_config,
    const std::filesystem::path &ingest_json_path)
    : loop_(loop),
      connection_(
          hostname,
          loop_,
          aws_metadata_timeout,
          heartbeat_interval,
          std::move(intake_config),
          buffer_size,
          *this,
          std::bind(&KernelCollectorSimulator::on_connected, this)),
      log_(connection_.writer()),
      scheduler_(loop_, std::bind(&KernelCollectorSimulator::callback, this)),
      stopped_{true}
{
  ingest_json_reader_ = std::make_unique<IngestJsonReader>(ingest_json_path, connection_.writer());
}

KernelCollectorSimulator::~KernelCollectorSimulator()
{
  ::uv_loop_close(&loop_);
}

void KernelCollectorSimulator::run_loop()
{
  connection_.connect();

  while (::uv_run(&loop_, UV_RUN_DEFAULT))
    ;

  scheduler_.stop();
  stopped_ = true;
}

scheduling::JobFollowUp KernelCollectorSimulator::callback()
{
  if (stopped_) {
    return scheduling::JobFollowUp::stop;
  }
  // loss of precision here is ok - its just a simulator after all.
  auto next_message_ms = std::chrono::duration_cast<std::chrono::milliseconds>(ingest_json_reader_->next());
  connection_.flush();
  scheduler_.defer(next_message_ms);
  return scheduling::JobFollowUp::ok;
}

void KernelCollectorSimulator::on_error(int err)
{
  scheduler_.stop();
  stopped_ = true;
  // TBD should we restart the playback from the beginning?  if the reducer is down
  // and then restarted, it will miss all the process, etc. messages from the beginning.
  ingest_json_reader_->reset(); // I think this is right.
  LOG::error("connection error encountered {}.  stopping playback until reconnection.", err);
  std::this_thread::sleep_for(add_jitter(RECONNECT_DELAY, -RECONNECT_JITTER, RECONNECT_JITTER));
}

void KernelCollectorSimulator::on_connected()
{
  stopped_ = false;
  LOG::debug("connected, starting playback.");
  scheduler_.defer(std::chrono::duration_cast<std::chrono::milliseconds>(ingest_json_reader_->next()));
}
