/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

/* return nonzero with probability p */
static int choice(double p)
{
  return p > drand48();
}

static void child(void)
{
  /* reseed */
  srand48((long)time(NULL));

  for (;;) {
    sleep(1);

    if (choice(0.2)) {
      printf("child: calling exit(1)\n");
      exit(1);
    }
    if (choice(0.2)) {
      printf("child: calling abort()\n");
      abort();
    }
    if (choice(0.2)) {
      break;
    }
  }
}

int main(void)
{
  srand48((long)time(NULL));

  for (;;) {
    pid_t pid;
    pid = fork();
    if (pid) { /* parent */
      printf("forked pid %d\n", pid);
    } else {
      child();
      return 0;
    }

    if (choice(0.01)) {
      printf("parent: exit(0)\n");
      exit(0);
    }

    sleep(1);
  }
}
