/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <unistd.h>

int main(void)
{
  printf("forking new process\n");
  fork();
  sleep(1);
  return 0;
}
