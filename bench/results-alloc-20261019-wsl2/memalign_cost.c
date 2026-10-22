// Cost of an aligned allocation against a plain one in glibc, multi-threaded mode. Disposable.
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static void *idle(void *arg) { (void)arg; return NULL; }

static double now_ns(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec * 1e9 + t.tv_nsec;
}

int main(void) {
  pthread_t th;
  pthread_create(&th, NULL, idle, NULL);  /* leaves glibc's single-thread shortcut */
  pthread_join(th, NULL);
  const int n = 5000000;
  const size_t sizes[] = {512, 640};
  for (int s = 0; s < 2; s++) {
    size_t sz = sizes[s];
    for (int round = 0; round < 2; round++) {
      double t0 = now_ns();
      for (int i = 0; i < n; i++) { void *p = malloc(sz); __asm__ volatile("" ::"r"(p)); free(p); }
      double t1 = now_ns();
      for (int i = 0; i < n; i++) {
        void *p; posix_memalign(&p, 128, sz); __asm__ volatile("" ::"r"(p)); free(p);
      }
      double t2 = now_ns();
      if (round == 1)
        printf("%zu B: malloc+free %.1f ns, posix_memalign(128)+free %.1f ns\n", sz,
               (t1 - t0) / n, (t2 - t1) / n);
    }
  }
  return 0;
}
