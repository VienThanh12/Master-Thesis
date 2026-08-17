#pragma once
// jemalloc's own accounting, read through mallctl (RQ3).
//
// Why this exists. Peak RSS from getrusage is a single number for the whole
// process, so it can establish that the Rust build holds more memory than the
// C++ build without saying what the extra is. Section 7.5.4 records exactly that
// gap: the split between arena pre-reservation, per-thread caches, and static
// footprint is left unresolved. jemalloc already tracks that split internally.
//
// This is not the heap profile that bench/alloc_profile.sh collects. That needs a
// prof-enabled build and jeprof to symbolise, and attributes bytes to allocation
// sites; this needs neither and attributes bytes to allocator structures. They
// answer different halves of the same question, and this half runs anywhere.
//
// Both languages read the same six counters from the same allocator -- the C++
// side through mallctl here, the Rust side through tikv-jemalloc-ctl -- so the
// numbers can be differenced. Using two allocator-specific tools instead would
// reproduce the mismatched-instrument problem that alloc_profile.sh was written
// to avoid.
//
// mallctl is declared weak rather than included from <jemalloc/jemalloc.h>: the
// runtime ships in libjemalloc.so.2 while the header is a separate dev package,
// and the system-allocator arms deliberately do not link jemalloc at all. When
// the symbol is absent every field reports null, never zero -- a zero here would
// be read as "no arena metadata" rather than "not measured".
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string>

extern "C" int mallctl(const char* name, void* oldp, std::size_t* oldlenp, void* newp,
                       std::size_t newlen) __attribute__((weak));

namespace bench {

struct JeStats {
  bool available = false;
  // All in bytes. See the jemalloc(3) STATS section for the exact definitions.
  std::uint64_t allocated = 0;  // requested by the application and not yet freed
  std::uint64_t active = 0;     // in pages handed to the application
  std::uint64_t metadata = 0;   // arena and tcache bookkeeping -- the fixed cost
  std::uint64_t resident = 0;   // physically backed, the allocator's own view of RSS
  std::uint64_t mapped = 0;     // address space in active extents
  std::uint64_t retained = 0;   // unmapped but not returned to the OS
};

inline bool je_read_u64(const char* name, std::uint64_t* out) {
  std::size_t sz = sizeof(*out);
  return mallctl(name, out, &sz, nullptr, 0) == 0;
}

// jemalloc's statistics are cached and only refreshed when `epoch` is written,
// so a read without this returns whatever the last refresh saw.
inline JeStats je_snapshot() {
  JeStats s;
  if (&mallctl == nullptr) return s;  // system-allocator arm: nothing to read
  std::uint64_t epoch = 1;
  std::size_t esz = sizeof(epoch);
  if (mallctl("epoch", &epoch, &esz, &epoch, sizeof(epoch)) != 0) return s;
  // stats.* exist only in a --enable-stats build. That is jemalloc's default, but
  // a build without it fails the read rather than returning a wrong number, so
  // every field is required before the snapshot counts as available.
  const bool ok = je_read_u64("stats.allocated", &s.allocated) &&
                  je_read_u64("stats.active", &s.active) &&
                  je_read_u64("stats.metadata", &s.metadata) &&
                  je_read_u64("stats.resident", &s.resident) &&
                  je_read_u64("stats.mapped", &s.mapped) &&
                  je_read_u64("stats.retained", &s.retained);
  s.available = ok;
  return s;
}

// A JSON object, or nulls when the allocator cannot be interrogated. The key is
// always present so a consumer can tell "measured as absent" from "field missing
// because the harness predates this".
inline std::string je_json(const JeStats& s) {
  if (!s.available) {
    return "\"je\":{\"available\":false,\"allocated\":null,\"active\":null,"
           "\"metadata\":null,\"resident\":null,\"mapped\":null,\"retained\":null}";
  }
  char buf[320];
  std::snprintf(buf, sizeof(buf),
                "\"je\":{\"available\":true,\"allocated\":%llu,\"active\":%llu,"
                "\"metadata\":%llu,\"resident\":%llu,\"mapped\":%llu,\"retained\":%llu}",
                (unsigned long long)s.allocated, (unsigned long long)s.active,
                (unsigned long long)s.metadata, (unsigned long long)s.resident,
                (unsigned long long)s.mapped, (unsigned long long)s.retained);
  return buf;
}

}  // namespace bench
