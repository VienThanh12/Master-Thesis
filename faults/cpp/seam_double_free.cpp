// Boundary case, C++ half: double release across an opaque-handle boundary.
//
// This is the shape a C ABI forces on both languages. The component hands the
// host an opaque pointer and a release entry point, and the host is trusted to
// call it exactly once. A retransmitted release calls it twice, which is the
// same non-idempotent release path as cpp/double_free.cpp, now expressed the way
// a seam expresses it.
//
// The C++ half of this pair is unremarkable and that is deliberate. What the
// pair is for is the Rust half: rust/double_free.rs does not compile, while
// rust/seam_double_free.rs is the same defect written through `unsafe` and
// compiles. Holding the C++ side fixed is what makes the Rust column the only
// thing that moves.
#include <cstdio>

namespace {

struct UeContext {
  unsigned long ue_id;
  unsigned long messages_handled;
};

// The seam's entry points: the host sees an opaque pointer and nothing else.
void* ue_context_create(unsigned long ue_id) {
  return new UeContext{ue_id, 0};
}

void ue_context_release(void* handle) {
  delete static_cast<UeContext*>(handle);
}

}  // namespace

int main() {
  void* handle = ue_context_create(1001);

  ue_context_release(handle);  // release
  std::printf("released once\n");
  std::fflush(stdout);

  ue_context_release(handle);  // retransmitted release: the same storage again
  std::printf("released twice\n");
  return 0;
}
