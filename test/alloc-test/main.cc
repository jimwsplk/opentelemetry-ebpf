// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

#include "mmap_allocator.h"

#include <platform/types.h>
#include <util/metric_store.h>
#include <util/pool.h>

#include <sys/types.h>
#include <unistd.h>

#include <cstdio>
#include <memory>

constexpr size_t PAGE_SIZE = 4096;

constexpr size_t POOL_SIZE = 1000000;

static size_t num_constructed = 0;
static size_t num_destructed = 0;

struct PoolElement {
  char dummy[1024];

  PoolElement() { num_constructed++; }

  ~PoolElement() { num_destructed++; }
};

using allocator_t = MmapAllocator<PoolElement>;

using pool_t = Pool<PoolElement, POOL_SIZE, allocator_t>;

void print_mem_usage()
{
  char file_name[256] = {};
  snprintf(file_name, sizeof(file_name), "/proc/%d/statm", getpid());

  FILE *file = fopen(file_name, "r");
  assert(file);

  u64 size{0}, resident{0};
  fscanf(file, "%lu %lu", &size, &resident);

  fclose(file);

  printf("size=%lu resident=%lu\n", size * PAGE_SIZE, resident * PAGE_SIZE);
}

int main()
{
  printf("-- starting\n");
  print_mem_usage();

  // allocate the pool
  auto pool = std::make_unique<pool_t>();

  printf("\n-- after allocation\n");
  print_mem_usage();

  // construct all pool elements
  //
  while (!pool->full()) {
    pool->emplace();
  }
  assert(pool->size() == pool->capacity());
  assert(num_constructed == pool->capacity());

  printf("\n-- after instatiation\n");
  print_mem_usage();

  // destruct all pool elements
  //
  for (size_t i = 0; i < pool->capacity(); ++i) {
    pool->remove(i);
  }
  assert(pool->empty());
  assert(num_destructed == pool->capacity());

  printf("\n-- after cleanup\n");
  print_mem_usage();

  // deallocate the pool
  pool.reset();

  printf("\n-- after deallocation\n");
  print_mem_usage();
}
