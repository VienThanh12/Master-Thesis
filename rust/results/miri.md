# Rust suite under Miri

Regenerate with `rust/miri.sh`. Categorical outcome; the elapsed time is
incidental and is not a measurement.

- Toolchain: `nightly` (rustc 1.100.0-nightly (34baba539 2026-08-16))
- `miri 0.1.0 (34baba5394 2026-08-16)`
- `MIRIFLAGS`: `-Zmiri-disable-isolation -Zmiri-strict-provenance`
- Scope: `--test state_matrix --test invariants`

| Tests passed | Undefined-behaviour reports | Outcome |
|---:|---:|---|
| 14 | 0 | clean |

Clean. Miri found no undefined behaviour and no aliasing violation under
Stacked Borrows with strict provenance.

This is a weaker statement than it looks, and deliberately so. The core
contains no `unsafe` (spec §12), so the aliasing discipline Miri checks is
already enforced by the compiler; the run confirms the property rather than
discovering it. Its value is symmetry with `cpp/sanitise.sh`: both arms are
now checked by the strongest dynamic tool their language offers, so the
difference between them is a difference in what the tools can guarantee and
not in whether anyone looked.
