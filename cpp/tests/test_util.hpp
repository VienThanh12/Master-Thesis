#pragma once
#include <cstdio>
#include <string_view>

// Minimal dependency-free test harness (no gtest needed for scaffolding).
namespace uecm::test {

inline int g_failures = 0;
inline int g_checks = 0;

inline void report(bool ok, std::string_view expr, const char* file, int line) {
  ++g_checks;
  if (!ok) {
    ++g_failures;
    std::fprintf(stderr, "FAIL %s:%d: %.*s\n", file, line,
                 static_cast<int>(expr.size()), expr.data());
  }
}

inline int summary(const char* name) {
  std::fprintf(stderr, "[%s] %d checks, %d failures\n", name, g_checks, g_failures);
  return g_failures == 0 ? 0 : 1;
}

}  // namespace uecm::test

#define CHECK(cond) ::uecm::test::report((cond), #cond, __FILE__, __LINE__)
