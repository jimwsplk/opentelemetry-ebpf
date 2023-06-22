// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0
#include "ingest_connection.h"

#include <util/boot_time.h>

IngestConnection::IngestConnection(
    std::string_view hostname,
    ::uv_loop_t &loop,
    std::chrono::milliseconds aws_metadata_timeout,
    std::chrono::milliseconds heartbeat_interval,
    config::IntakeConfig intake_config,
    std::size_t buffer_size,
    channel::Callbacks &connection_callback,
    std::function<void()> on_connected_cb)
    : curl_(CurlEngine::create(&loop)),
      channel_(std::move(intake_config), loop, buffer_size),
      connection_callback_(connection_callback),
      encoder_(channel_.intake_config().make_encoder()),
      writer_(channel_.buffered_writer(), monotonic, get_boot_time(), encoder_.get()),
      caretaker_(
          hostname,
          ClientType::kernel,
          {},
          &loop,
          writer_,
          aws_metadata_timeout,
          heartbeat_interval,
          std::bind(&channel::ReconnectingChannel::flush, &channel_),
          std::bind(&channel::ReconnectingChannel::set_compression, &channel_, std::placeholders::_1),
          std::move(on_connected_cb))
{
  channel_.register_pipeline_observer(this);
}

void IngestConnection::connect()
{
  channel_.start_connect();
}

void IngestConnection::flush()
{
  channel_.flush();
}

u32 IngestConnection::received_data(const u8 *data, int data_len)
{
  return connection_callback_.received_data(data, data_len);
}

void IngestConnection::on_error(int err)
{
  caretaker_.set_disconnected();

  connection_callback_.on_error(err);
}

void IngestConnection::on_closed()
{
  connection_callback_.on_closed();
}

void IngestConnection::on_connect()
{
  caretaker_.set_connected();

  connection_callback_.on_connect();
}
