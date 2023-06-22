/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <otlp/otlp_grpc_metrics_client.h>
#include <reducer/aggregation/labels.h>
#include <reducer/publisher.h>
#include <reducer/tsdb_formatter.h>

#include <uv.h>

#include <chrono>
#include <deque>
#include <memory>

class Generator {
public:
  // Parameters:
  //   writer -- object to use for publishing generated metrics
  //   metrics_format -- in which format should metrics be generated
  //   num_flows -- number of simultaneous flows to generate
  //   interval -- time between individual writes
  Generator(
      reducer::Publisher::WriterPtr writer,
      reducer::TsdbFormat metrics_format,
      size_t num_flows,
      std::chrono::seconds interval);

  void run();
  void stop_async();

private:
  uv_loop_t loop_;
  uv_async_t stop_async_;
  uv_timer_t timer_;

  reducer::Publisher::WriterPtr writer_;
  std::unique_ptr<reducer::TsdbFormatter> formatter_;

  const size_t num_flows_;
  const std::chrono::seconds interval_;

  std::deque<reducer::aggregation::FlowLabels> flows_;

  static void on_stop_async(uv_async_t *handle);
  static void on_timer(uv_timer_t *timer);

  void generate_random_metrics();
};
