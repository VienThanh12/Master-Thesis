// Rust counterpart to cpp/integer_overflow.cpp (integer overflow in an
// optimised build).
//
// Boundary case: this COMPILES and, in a release build, silently produces the
// wrong answer.
//
// The detail that matters is the build profile. `debug-assertions` on -- the
// default for `cargo build` and for plain `rustc` -- makes this a panic, and a
// panic is a detection. The thesis compares an `opt-level = 2` Rust build
// against a `-O2` C++ build (spec §3), and `opt-level = 2` leaves
// `overflow-checks` off, so the arithmetic wraps and nothing is reported. The
// runner therefore compiles this case with the release flags rather than the
// defaults; compiled the other way it would record a detection the measured
// configuration does not actually have.
//
// The comparison is sharper than "Rust is safer". C++ signed overflow is
// *undefined*, so the program has no meaning; Rust's wrap is *defined*, so the
// program has a meaning and the meaning is wrong. Defined-but-wrong is easier
// to debug and no less incorrect, and it is not what "memory safe" is usually
// taken to promise.
//
// The pattern is real: CVE-2026-64467 in rust_binder is a usize-versus-u64
// stride error of this shape (LITERATURE_NOTES.md §5.1).

/// Base TEID for a bearer, given a per-UE stride.
///
/// Plain `+` and `*`, deliberately not the `wrapping_` forms: the whole point of
/// the case is that the same source has two different meanings depending on the
/// build profile. With `overflow-checks` on this panics, which is a detection;
/// with them off, as at `opt-level = 2`, it wraps and says nothing. Writing
/// `wrapping_mul` here would make the profile irrelevant and the case would
/// stop testing anything.
#[inline(never)]
fn teid_for(base: i32, stride: i32, index: i32) -> i32 {
    base + stride * index
}

fn main() {
    let base: i32 = std::hint::black_box(1000);
    let stride: i32 = std::hint::black_box(50_000_000);
    // 50e6 * 45 = 2.25e9, past i32::MAX (2 147 483 647). At 42 the product is
    // 2.1e9 and still fits, which is close enough to look like an overflow and
    // is not one.
    let index: i32 = std::hint::black_box(45);

    let teid = teid_for(base, stride, index);

    println!("teid={teid} (expected a value above {base})");

    // A TEID must be positive; the wrap has produced something that is not.
    if teid <= base {
        println!("overflow: computed TEID is not above the base");
        std::process::exit(1);
    }
}
