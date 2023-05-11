/*
 * Copyright The OpenTelemetry Authors
 * SPDX-License-Identifier: Apache-2.0
 */

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define NTHR 4

void *thread_func(void *);
void make_threads(void);

void *thread_func(void *arg)
{
  int t = *(int *)arg;

  printf("child: thread start\n");
  sleep((unsigned int)t);
  printf("child: thread done\n");

  return NULL;
}

void make_threads(void)
{
  int i, error;
  pthread_t thr[NTHR];

  for (i = 0; i < NTHR; i++) {
    int *arg = malloc(sizeof(*arg));
    *arg = i + 1;
    error = pthread_create(&thr[i], NULL, thread_func, arg);
    if (error != 0) {
      printf("pthread_create: errno %d\n", error);
    }
  }
}

int main(void)
{
  pid_t pid;

  printf("parent: forking...\n");
  pid = fork();
  if (pid) { /* parent */
    printf("parent: child pid %d created, sleeping\n", pid);
    sleep(10);
    printf("parent: exiting\n");
  } else {
    printf("child: creating %d threads...\n", NTHR);
    make_threads();
    sleep(3);
    printf("child: exiting\n");
    exit(0); /* will become zombie process */
  }
  return 0;
}
