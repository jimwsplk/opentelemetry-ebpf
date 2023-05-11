// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include "random.h"

#include <reducer/constants.h>

#include <yaml-cpp/yaml.h>

#include <cstdlib>
#include <stdexcept>
#include <vector>

////////////////////////////////////////////////////////////////////////////////

using string_values_t = std::vector<std::string>;

static string_values_t az_values{
    "us-east-1",
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "eu-north-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
};

static string_values_t role_values{
    "backflow-generator",
    "quince-receiver",
    "sideline-initiator",
    "throughfare-counter",
    "turbo-encabulator",
    "flux-capacitor",
    "relation-farcaster",
    "bob",
};

static string_values_t version_values{
    "v1.0",
    "1.2.3",
    "latest",
    "beta",
    "rc0",
    "rc1",
};

static string_values_t env_values{
    "production",
    "staging",
    "testing",
    "lab",
};

static string_values_t ns_values{
    "o11y-npm",
    "flowmill",
    "staging",
};

static string_values_t process_values{
    "python",
    "ruby",
    "java",
    "node",
    "curl",
    "nc",
    "nginx",
};

static string_values_t container_values{
    "lucky-badger",
    "curious-sparrow",
    "determined-sheep",
    "sidelined-squirrel",
    "zesty-octopus",
    "tetchy-meerkat",
    "drab-shark",
};

////////////////////////////////////////////////////////////////////////////////

void random_init()
{
  srand(time(NULL));
}

static void load_values(YAML::Node &yaml, std::string const &dimension, string_values_t &container)
{
  auto values = yaml[dimension];

  if (!values.IsDefined()) {
    // No values are defined for this dimension, and that's OK.
    return;
  }

  if (!values.IsSequence()) {
    // Must be a list of values.
    throw std::runtime_error("wrong type for node '" + dimension + "'; expecting a sequence");
  }

  // Discard prior values.
  container.clear();

  for (auto const &i : values) {
    auto value = i.as<std::string>();
    container.push_back(value);
  }
}

void random_load_dimensions(std::string_view path)
{
  YAML::Node yaml = YAML::LoadFile(std::string(path));

  load_values(yaml, "az", az_values);
  load_values(yaml, "role", role_values);
  load_values(yaml, "version", version_values);
  load_values(yaml, "env", env_values);
  load_values(yaml, "ns", ns_values);
  load_values(yaml, "process", process_values);
  load_values(yaml, "container", container_values);
}

inline std::string_view random_choice(string_values_t const &values)
{
  if (values.empty()) {
    return "";
  } else {
    return values[rand() % values.size()];
  }
}

inline std::string_view random_az_name()
{
  return random_choice(az_values);
}

inline std::string_view random_role()
{
  return random_choice(role_values);
}

inline std::string_view random_version()
{
  return random_choice(version_values);
}

inline std::string_view random_env()
{
  return random_choice(env_values);
}

inline std::string_view random_ns()
{
  return random_choice(ns_values);
}

inline std::string_view random_type()
{
  auto r = rand() % enum_traits<NodeResolutionType>::count;
  return to_string(static_cast<NodeResolutionType>(r), "");
}

inline std::string_view random_process()
{
  return random_choice(process_values);
}

inline std::string_view random_container()
{
  return random_choice(container_values);
}

inline unsigned random_number(unsigned min, unsigned max)
{
  assert(max > min);
  return (rand() % (max - min)) + min;
}

reducer::aggregation::NodeLabels random_az()
{
  reducer::aggregation::NodeLabels n;

  n.az = random_az_name();
  n.role = random_role();
  n.version = random_version();
  n.env = random_env();
  n.ns = random_ns();
  n.type = random_type();
  n.process = random_process();
  n.container = random_container();

  return n;
}

reducer::aggregation::FlowLabels random_az_az()
{
  return {random_az(), random_az()};
}

ebpf_net::metrics::tcp_metrics random_tcp_metrics()
{
  return ebpf_net::metrics::tcp_metrics{
      .active_sockets = random_number(1, 10),
      .sum_retrans = random_number(1, 10),
      .sum_bytes = random_number(100, 10'000),
      .sum_srtt = random_number(10'000'000, 100'000'000),
      .sum_delivered = random_number(1, 10),
      .active_rtts = random_number(1, 10),
      .syn_timeouts = random_number(1, 10),
      .new_sockets = 1,
      .tcp_resets = random_number(1, 10),
  };
}

ebpf_net::metrics::udp_metrics random_udp_metrics()
{
  return ebpf_net::metrics::udp_metrics{
      .active_sockets = random_number(1, 10),
      .addr_changes = 0,
      .packets = random_number(1, 1000),
      .bytes = random_number(100, 10'000),
      .drops = random_number(1, 10),
  };
}

ebpf_net::metrics::dns_metrics random_dns_metrics()
{
  auto requests_a = random_number(1, 10);
  auto requests_aaaa = random_number(1, 10);
  auto responses = random_number(0, requests_a + requests_aaaa);
  auto timeouts = random_number(0, requests_a + requests_aaaa - responses);
  auto sum_processing_time_ns = random_number(1'000'00, 100'000'000);
  auto sum_total_time_ns = random_number(sum_processing_time_ns, 100'000'000);

  return ebpf_net::metrics::dns_metrics{
      .active_sockets = 1,
      .requests_a = requests_a,
      .requests_aaaa = requests_aaaa,
      .responses = responses,
      .timeouts = timeouts,
      .sum_total_time_ns = sum_total_time_ns,
      .sum_processing_time_ns = sum_processing_time_ns,
  };
}

ebpf_net::metrics::http_metrics random_http_metrics()
{
  auto sum_processing_time_ns = random_number(1'000'00, 100'000'000);
  auto sum_total_time_ns = random_number(sum_processing_time_ns, 100'000'000);

  return ebpf_net::metrics::http_metrics{
      .active_sockets = 1,
      .sum_code_200 = random_number(1, 10),
      .sum_code_400 = random_number(1, 10),
      .sum_code_500 = random_number(1, 10),
      .sum_code_other = random_number(1, 10),
      .sum_total_time_ns = sum_total_time_ns,
      .sum_processing_time_ns = sum_processing_time_ns,
  };
}
