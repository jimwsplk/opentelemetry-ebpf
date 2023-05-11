/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <reducer/aggregation/labels.h>

#include <generated/ebpf_net/metrics.h>

#include <string_view>

// Initializes this module.
void random_init();

// Loads values for each dimension (az, role, etc.) from a YAML file.
// Throws an exception on error.
void random_load_dimensions(std::string_view path);

reducer::aggregation::FlowLabels random_az_az();

ebpf_net::metrics::tcp_metrics random_tcp_metrics();

ebpf_net::metrics::udp_metrics random_udp_metrics();

ebpf_net::metrics::dns_metrics random_dns_metrics();

ebpf_net::metrics::http_metrics random_http_metrics();
