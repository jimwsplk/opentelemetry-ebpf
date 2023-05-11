// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include <channel/buffered_writer.h>
#include <channel/callbacks.h>
#include <channel/tcp_channel.h>
#include <channel/upstream_connection.h>
#include <util/json.h>
#include <util/log.h>
#include <util/uv_helpers.h>

#include <uv.h>

#include <cstring>

class Client {
public:
  Client();

  void run();
  void stop_async();

private:
  uv_loop_t loop_;
  uv_async_t stop_async_;
  uv_timer_t timer_;

  static void on_stop_async(uv_async_t *handle);
  static void send_metric(uv_timer_t *timer);

  class Callbacks : public channel::Callbacks {
  public:
    Callbacks(Client &client);
    virtual u32 received_data(const u8 *data, int data_len) override;
    virtual void on_error(int err) override;
    virtual void on_closed() override;
    virtual void on_connect() override;

  private:
    Client &client_;
  };
  Callbacks client_callbacks_;
  std::unique_ptr<channel::TCPChannel> primary_channel_;
  std::optional<channel::UpstreamConnection> upstream_connection_;
};

//========================================================================================================================
Client::Client() : client_callbacks_(*this)
{
  CHECK_UV(uv_loop_init(&loop_));

  CHECK_UV(uv_async_init(&loop_, &stop_async_, &on_stop_async));
  stop_async_.data = this;

  CHECK_UV(uv_timer_init(&loop_, &timer_));
  timer_.data = this;
}

void Client::run()
{
  //===================================================================================================================================
  LOG::info("making primary_channel");
  primary_channel_ = std::make_unique<channel::TCPChannel>(loop_, "127.0.0.1", "4318");

  upstream_connection_.emplace( // make an upstream_connection for OTLP hack
      16 * 1024,
      false /*allow_compression*/,
      *primary_channel_,
      nullptr);

  try {
    LOG::info("connecting upstream_connecion");
    upstream_connection_->connect(client_callbacks_);
  } catch (std::exception &e) {
    LOG::trace("upstream connect threw exception: {}", e.what());
    return;
  }

  uv_run(&loop_, UV_RUN_DEFAULT);
}

void Client::stop_async()
{
  uv_async_send(&stop_async_);
}

void Client::on_stop_async(uv_async_t *handle)
{
  auto instance = reinterpret_cast<Client *>(handle->data);
  uv_stop(&instance->loop_);
}

void Client::send_metric(uv_timer_t *timer)
{
  auto client = reinterpret_cast<Client *>(timer->data);
  auto writer = client->upstream_connection_->buffered_writer();

  auto send_message = [&](std::string const &payload) {
    LOG::info(
        "\n==========================================================================================================================");

    std::string header(
        "POST /v1/metrics HTTP/1.1\r\n"
        "Host: 127.0.0.1:4318\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: " +
        std::to_string(payload.size()) + "\r\n\r\n");

    LOG::info("write_otlp(): header {}", header);
    LOG::info("write_otlp(): payload {}", payload);

    writer.write_as_chunks(header);
    writer.write_as_chunks(payload);
    writer.flush();

    LOG::info("\n=========================================================\n");
  };

  using labels_t = std::map<std::string, std::string>;
  labels_t labels{
      {"daz", "ubuntu-focal"},
      {"denv", "ubuntu-focal"},
      {"dprocess", "opentelemetry-n"},
      {"drole", "nice_jennings"},
      {"dtype", "CONTAINER"},
      {"saz", "ubuntu-focal"},
      {"senv", "ubuntu-focal"},
      {"sns", "ubuntu-focal"},
      {"srole", "docker"},
      {"stype", "PROCESS"}};

  // Populate a JSON object and convert to string to send message.
  // It might be better to populate a protobuf request object and convert from protobuf to JSON string with
  // google::protobuf::util::MessageToJsonString().
  nlohmann::json attributes;
  for (auto const &[key, value] : labels) {
    nlohmann::json label;
    label["key"] = key;
    label["value"] = nlohmann::json{{"stringValue", value}};
    attributes.push_back(label);
  }

  nlohmann::json data_point;
  data_point["attributes"] = attributes;
  data_point["startTimeUnixNano"] = "1626149204629666000";
  data_point["timeUnixNano"] = "1626149211633082000";
  data_point["asInt"] = "3462";

  nlohmann::json metric;
  metric["name"] = "bytes_az_az_30";
  metric["description"] = "Describe bytes_az_az here";
  metric["sum"]["dataPoints"].push_back(data_point);
  metric["sum"]["aggregationTemporality"] = "AGGREGATION_TEMPORALITY_DELTA";
  metric["sum"]["isMonotonic"] = true;

  nlohmann::json metrics;
  metrics["metrics"].push_back(metric);

  nlohmann::json ilm;
  ilm["instrumentationLibraryMetrics"].push_back(metrics);

  nlohmann::json json_payload_object;
  json_payload_object["resourceMetrics"].push_back(ilm);

  std::string payload(json_payload_object.dump());

  send_message(payload);

  // Should clean up, but for now just exit.
  exit(0);
}

Client::Callbacks::Callbacks(Client &client) : client_(client) {}

u32 Client::Callbacks::received_data(const u8 *data, int data_len)
{
  LOG::info("Client::Callbacks::received_data() {}", std::string_view((char *)data, data_len));
  return data_len;
}

void Client::Callbacks::on_error(int err)
{
  LOG::info("Client::Callbacks::on_error() err {} {}", err, std::strerror(-err));

  /* (TODO not with this hack) close the channel, it will trigger reconnect */
  client_.upstream_connection_->close();
}

void Client::Callbacks::on_closed()
{
  LOG::info("Client::Callbacks::on_closed(): upstream connection closed");
  exit(0);
}

void Client::Callbacks::on_connect()
{
  LOG::info("Client::Callbacks::on_connect(): established upstream connection");

  CHECK_UV(uv_timer_start(&client_.timer_, send_metric, 0, 0));
}

int main(int argc, char **argv)
{
  Client client;
  client.run();

  return 0;
}
