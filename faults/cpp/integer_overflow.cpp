// Boundary case: integer overflow in an optimised build.
//
// A TEID stride computation overflows. The pattern is real: CVE-2026-64467 in
// rust_binder is a usize-versus-u64 stride error of exactly this shape
// (LITERATURE_NOTES.md §5.1), so this is not a synthetic arithmetic puzzle.
//
// The comparison this class exists to make is sharper than "Rust is safer".
// In C++ signed overflow is *undefined*: the compiler may assume it never
// happens and optimise accordingly, so the program has no meaning at all. In
// Rust the same overflow is *defined* to wrap in a release build, because
// opt-level = 2 leaves overflow-checks off -- the program has a meaning and the
// meaning is wrong. Defined-but-wrong against undefined-and-wrong is a real
// distinction and it does not line up neatly with "safe" and "unsafe".
//
// C++ detection: UndefinedBehaviorSanitizer, and only UBSan. ASan and TSan are
// both silent, which is why the catalogue needed a third sanitiser column.
#include <cstdint>
#include <cstdio>

namespace {

// Base TEID for a bearer, given a per-UE stride. Signed on purpose: this is the
// case where the language says nothing at all.
std::int32_t teid_for(std::int32_t base, std::int32_t stride, std::int32_t index) {
  return base + stride * index;  // overflows for large stride * index
}

}  // namespace

int main() {
  // volatile so the multiply happens at run time. Constant-folded, g++ computes
  // the overflow during translation and UBSan never sees it -- the case would
  // then read as undetected purely because the operands were literals.
  volatile std::int32_t base_in = 1000;
  volatile std::int32_t stride_in = 50'000'000;
  // 50e6 * 45 = 2.25e9, past INT32_MAX (2 147 483 647). At 42 the product is
  // 2.1e9 and still fits, which is close enough to look like an overflow and
  // is not one.
  volatile std::int32_t index_in = 45;

  const std::int32_t base = base_in;
  const std::int32_t teid = teid_for(base, stride_in, index_in);

  std::printf("teid=%d (expected a value above %d)\n", teid, base);

  // A TEID must be positive; overflow has produced something that is not.
  if (teid <= base) {
    std::printf("overflow: computed TEID is not above the base\n");
    return 1;
  }
  return 0;
}
