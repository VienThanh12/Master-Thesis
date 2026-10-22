// LD_PRELOAD allocation tracker for the handoff diagnosis. Disposable.
// Counts, per 16-byte size bucket, how many blocks were allocated and whether
// the thread that freed each block was the thread that allocated it.
// Output: one JSON line appended to $ALLOCPROBE_OUT at exit.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

#define NBUCKET 513           /* 16-byte steps up to 8 KiB, last bucket is larger */
#define TABLE_BITS 22
#define TABLE_SIZE (1u << TABLE_BITS)

typedef struct { uintptr_t ptr; uint32_t tid; uint32_t size; } entry_t;

static void *(*real_malloc)(size_t);
static void (*real_free)(void *);
static void *(*real_calloc)(size_t, size_t);
static void *(*real_realloc)(void *, size_t);
static int (*real_posix_memalign)(void **, size_t, size_t);
static void *(*real_aligned_alloc)(size_t, size_t);
static void *(*real_memalign)(size_t, size_t);

static entry_t *table;
static volatile int lock_word;
static int ready;
static uint64_t n_alloc[NBUCKET], n_free_same[NBUCKET], n_free_cross[NBUCKET], n_free_untracked;

static char boot_buf[1 << 16];
static size_t boot_used;

static __thread uint32_t tls_tid __attribute__((tls_model("initial-exec")));
static __thread int tls_busy __attribute__((tls_model("initial-exec")));

static uint32_t my_tid(void) {
  if (!tls_tid) tls_tid = (uint32_t)syscall(SYS_gettid);
  return tls_tid;
}
static void lock(void) { while (__atomic_exchange_n(&lock_word, 1, __ATOMIC_ACQUIRE)) { } }
static void unlock(void) { __atomic_store_n(&lock_word, 0, __ATOMIC_RELEASE); }
static unsigned bucket(size_t n) { size_t b = (n + 15) / 16; return b >= NBUCKET ? NBUCKET - 1 : (unsigned)b; }
static size_t slot_of(uintptr_t p) { return (size_t)((p >> 4) * 0x9E3779B97F4A7C15ull >> (64 - TABLE_BITS)); }

static int initializing;

static void init(void) {
  if (ready || initializing) return;
  initializing = 1;
  real_malloc = dlsym(RTLD_NEXT, "malloc");
  real_free = dlsym(RTLD_NEXT, "free");
  real_calloc = dlsym(RTLD_NEXT, "calloc");
  real_realloc = dlsym(RTLD_NEXT, "realloc");
  real_posix_memalign = dlsym(RTLD_NEXT, "posix_memalign");
  real_aligned_alloc = dlsym(RTLD_NEXT, "aligned_alloc");
  real_memalign = dlsym(RTLD_NEXT, "memalign");
  table = mmap(NULL, sizeof(entry_t) * TABLE_SIZE, PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
  ready = 1;
  initializing = 0;
}

static void *boot_alloc(size_t n) {
  size_t off = (boot_used + 15) & ~(size_t)15;
  if (off + n > sizeof boot_buf) return NULL;
  boot_used = off + n;
  return boot_buf + off;
}

static void track_alloc(void *p, size_t n) {
  if (!p || !ready || tls_busy) return;
  uint32_t tid = my_tid();
  lock();
  size_t i = slot_of((uintptr_t)p);
  while (table[i].ptr && table[i].ptr != (uintptr_t)p) i = (i + 1) & (TABLE_SIZE - 1);
  table[i].ptr = (uintptr_t)p; table[i].tid = tid; table[i].size = (uint32_t)n;
  n_alloc[bucket(n)]++;
  unlock();
}

static void track_free(void *p) {
  if (!p || !ready || tls_busy) return;
  uint32_t tid = my_tid();
  lock();
  size_t i = slot_of((uintptr_t)p);
  while (table[i].ptr && table[i].ptr != (uintptr_t)p) i = (i + 1) & (TABLE_SIZE - 1);
  if (!table[i].ptr) { n_free_untracked++; unlock(); return; }
  unsigned b = bucket(table[i].size);
  if (table[i].tid == tid) n_free_same[b]++; else n_free_cross[b]++;
  /* Backward-shift deletion keeps linear probing correct without tombstones. */
  size_t j = i;
  for (;;) {
    j = (j + 1) & (TABLE_SIZE - 1);
    if (!table[j].ptr) break;
    size_t k = slot_of(table[j].ptr);
    if ((j > i && (k <= i || k > j)) || (j < i && (k <= i && k > j))) { table[i] = table[j]; i = j; }
  }
  table[i].ptr = 0;
  unlock();
}

static int in_boot(void *p) { return (char *)p >= boot_buf && (char *)p < boot_buf + sizeof boot_buf; }

void *malloc(size_t n) {
  if (!real_malloc) {
    if (initializing) return boot_alloc(n);
    init();
    if (!real_malloc) return boot_alloc(n);
  }
  void *p = real_malloc(n); track_alloc(p, n); return p;
}
void *calloc(size_t a, size_t b) {
  if (!real_calloc) {
    if (initializing) { void *p = boot_alloc(a * b); if (p) memset(p, 0, a * b); return p; }
    init();
    if (!real_calloc) { void *p = boot_alloc(a * b); if (p) memset(p, 0, a * b); return p; }
  }
  void *p = real_calloc(a, b); track_alloc(p, a * b); return p;
}
void free(void *p) {
  if (!p || in_boot(p)) return;
  if (!real_free) init();
  track_free(p); real_free(p);
}
void *realloc(void *p, size_t n) {
  if (!real_realloc) init();
  if (p && in_boot(p)) { void *q = real_malloc(n); memcpy(q, p, n); track_alloc(q, n); return q; }
  if (p) track_free(p);
  void *q = real_realloc(p, n); track_alloc(q, n); return q;
}
int posix_memalign(void **out, size_t al, size_t n) {
  if (!real_posix_memalign) init();
  int r = real_posix_memalign(out, al, n); if (!r) track_alloc(*out, n); return r;
}
void *aligned_alloc(size_t al, size_t n) {
  if (!real_aligned_alloc) init();
  void *p = real_aligned_alloc(al, n); track_alloc(p, n); return p;
}
void *memalign(size_t al, size_t n) {
  if (!real_memalign) init();
  void *p = real_memalign(al, n); track_alloc(p, n); return p;
}

__attribute__((constructor)) static void on_load(void) { init(); }

__attribute__((destructor)) static void on_exit_report(void) {
  const char *path = getenv("ALLOCPROBE_OUT");
  const char *label = getenv("ALLOCPROBE_LABEL");
  if (!path) return;
  tls_busy = 1;
  FILE *f = fopen(path, "a");
  if (!f) return;
  fprintf(f, "{\"label\":\"%s\",\"untracked_frees\":%llu,\"buckets\":[", label ? label : "",
          (unsigned long long)n_free_untracked);
  int first = 1;
  for (unsigned b = 0; b < NBUCKET; b++) {
    if (!n_alloc[b] && !n_free_same[b] && !n_free_cross[b]) continue;
    fprintf(f, "%s[%u,%llu,%llu,%llu]", first ? "" : ",", b * 16,
            (unsigned long long)n_alloc[b], (unsigned long long)n_free_same[b],
            (unsigned long long)n_free_cross[b]);
    first = 0;
  }
  fprintf(f, "]}\n");
  fclose(f);
}
