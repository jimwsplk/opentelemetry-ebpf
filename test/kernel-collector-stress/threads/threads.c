/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#define MAXTHR 64

static int choice(double p)
{
  return p > drand48();
}

static void *thread_func(void *arg)
{
  int t = *(int *)arg;

  printf("thread start\n");
  sleep((unsigned int)t);
  printf("thread done\n");

  return NULL;
}

int main(void)
{
  int i, error;
  pthread_t thr[MAXTHR];

  srand48((long)time(NULL));

  for (i = 0; i < MAXTHR; i++) {
    int *arg = malloc(sizeof(*arg));
    *arg = (i + 1) / 3;
    error = pthread_create(&thr[i], NULL, thread_func, arg);
    if (error != 0) {
      printf("pthread_create: errno %d\n", error);
    }
  }
  sleep(10);
  for (i = 0; i < MAXTHR; i++) {
    if (choice(0.5)) {
      pthread_join(thr[i], NULL);
    }
  }
  return 0;
}
