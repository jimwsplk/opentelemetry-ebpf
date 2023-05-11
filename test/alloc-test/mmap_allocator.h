/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <sys/mman.h>
#include <sys/types.h>

#include <cassert>
#include <stdexcept>

template <typename T> class MmapAllocator {
public:
  using value_type = T;

  template <typename U> struct rebind {
    typedef MmapAllocator<U> other;
  };

  value_type *allocate(std::size_t n)
  {
    constexpr auto prot = PROT_READ | PROT_WRITE;
    constexpr auto flags = MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE;

    const size_t length = n * sizeof(value_type);

    void *m = mmap(NULL, length, prot, flags, -1, 0);

    if (m == MAP_FAILED) {
      throw std::bad_alloc();
    }

    return static_cast<value_type *>(m);
  }

  void deallocate(value_type *p, std::size_t n)
  {
    const size_t length = n * sizeof(value_type);

    int r = munmap(p, length);

    (void)r;
    assert(r == 0);
  }
};
