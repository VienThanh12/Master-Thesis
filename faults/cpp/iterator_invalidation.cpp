// Defect: iterator invalidation.
// A container is mutated (push_back may reallocate) while being iterated, leaving
// the iterator dangling. This is the C++ analogue of adding a DRB to a context's
// bearer list while walking it. The reallocation frees the old buffer, so the
// subsequent dereference is a heap-use-after-free detected by AddressSanitizer.
#include <cstdio>
#include <vector>

struct DrbEntry {
  int drb_id;
};

int main() {
  std::vector<DrbEntry> drbs;
  for (int i = 0; i < 8; ++i) drbs.push_back(DrbEntry{i});

  for (auto it = drbs.begin(); it != drbs.end(); ++it) {
    if (it->drb_id == 3) {
      drbs.push_back(DrbEntry{99});  // may reallocate -> invalidates `it`
    }
    std::printf("drb_id=%d\n", it->drb_id);  // use of invalidated iterator
  }
  return 0;
}
