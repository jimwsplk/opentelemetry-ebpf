// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include <otlp/otlp_grpc_logs_client.h>

#include <util/log.h>

int main(int argc, char **argv)
{
  otlp_client::OtlpGrpcLogsClient client(grpc::CreateChannel("localhost:4317", grpc::InsecureChannelCredentials()));

  ExportLogsServiceRequest request;

  auto resource_logs = request.add_resource_logs();

  auto scope_logs = resource_logs->add_scope_logs();

  opentelemetry::proto::logs::v1::LogRecord log_record;
  log_record.set_time_unix_nano(12345678);

  log_record.set_severity_text("INFO");
  log_record.set_severity_number(opentelemetry::proto::logs::v1::SeverityNumber::SEVERITY_NUMBER_INFO);

  std::string_view message("-------------Test log body--------------");
  log_record.mutable_body()->set_string_value(message.data(), message.size());

  auto attribute1 = log_record.add_attributes();
  std::string_view key1("test-log-attribute-key1");
  std::string_view value1("test-log-attribute-value1");
  attribute1->set_key(key1.data(), key1.size());
  attribute1->mutable_value()->set_string_value(value1.data(), value1.size());

  auto attribute2 = log_record.add_attributes();
  std::string_view key2("test-log-attribute-key2");
  std::string_view value2("test-log-attribute-value2");
  attribute2->set_key(key2.data(), key2.size());
  attribute2->mutable_value()->set_string_value(value2.data(), value2.size());

  *scope_logs->add_log_records() = std::move(log_record);

  auto status = client.Export(request);

  if (status.ok()) {
    LOG::debug("RPC succeeded.");
  } else {
    LOG::error("RPC failed: {}: {}", status.error_code(), log_waive(status.error_message()));
  }

  return 0;
}
