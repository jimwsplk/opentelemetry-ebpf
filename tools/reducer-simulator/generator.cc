// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include <config.h>

#include "generator.h"
#include "random.h"

#include <reducer/disabled_metrics.h>
#include <reducer/util/thread_ops.h>
#include <reducer/write_metrics.h>

#include <platform/userspace-time.h>

#include <util/time.h>
#include <util/uv_helpers.h>

Generator::Generator(
    reducer::Publisher::WriterPtr writer, reducer::TsdbFormat metrics_format, size_t num_flows, std::chrono::seconds interval)
    : writer_(std::move(writer)),
      formatter_(reducer::TsdbFormatter::make(metrics_format, writer_)),
      num_flows_(num_flows),
      interval_(interval)
{
  CHECK_UV(uv_loop_init(&loop_));

  CHECK_UV(uv_async_init(&loop_, &stop_async_, &on_stop_async));
  stop_async_.data = this;

  CHECK_UV(uv_timer_init(&loop_, &timer_));
  timer_.data = this;

  formatter_->set_rollup(30);
  formatter_->set_aggregation("az_az");
}

void Generator::run()
{
  set_self_thread_name("generator");

  auto interval_ms = integer_time<std::chrono::milliseconds>(interval_);
  CHECK_UV(uv_timer_start(&timer_, on_timer, interval_ms, interval_ms));

  uv_run(&loop_, UV_RUN_DEFAULT);
}

void Generator::stop_async()
{
  uv_async_send(&stop_async_);
}

void Generator::on_stop_async(uv_async_t *handle)
{
  auto instance = reinterpret_cast<Generator *>(handle->data);
  uv_stop(&instance->loop_);
}

void Generator::on_timer(uv_timer_t *timer)
{
  auto instance = reinterpret_cast<Generator *>(timer->data);
  instance->generate_random_metrics();
}

void Generator::generate_random_metrics()
{
  reducer::DisabledMetrics disabled_metrics("");

  formatter_->set_timestamp(std::chrono::nanoseconds(fp_get_time_ns()));

  // Generate a predetermined number of random flows.
  //
  while (flows_.size() < num_flows_) {
    flows_.push_back(random_az_az());
  }

  for (const auto &flow : flows_) {
    formatter_->set_labels(flow);

    reducer::write_metrics(random_tcp_metrics(), writer_, *formatter_, disabled_metrics);
    reducer::write_metrics(random_udp_metrics(), writer_, *formatter_, disabled_metrics);
    reducer::write_metrics(random_dns_metrics(), writer_, *formatter_, disabled_metrics);
    reducer::write_metrics(random_http_metrics(), writer_, *formatter_, disabled_metrics);
  }

  formatter_->flush();
  writer_->flush();

  // Pop-off a random number of flows. What is left will be reused in the next
  // iteration, simulating flows that persist through more than one interval.
  //
  if (flows_.size() > 0) {
    size_t pop_num = rand() % flows_.size();
    flows_.erase(flows_.begin(), flows_.begin() + pop_num);
  }
}
