# RQ2: the unsafe boundary class under Miri

Regenerate with `faults/run_miri.sh`. Outcomes are categorical.

- Rust compiler: `rustc 1.97.1 (8bab26f4f 2026-07-14)`
- `miri 0.1.0 (34baba5394 2026-08-16)`
- Run timeout: 300s

| Case | Role | Outcome | Diagnostic |
|---|---|---|---|
| `seam_double_free` | defect | reported | `constructing invalid value of type std::boxed::Box<UeContext>: encounter` |
| `seam_double_free_control` | control | clean | `-` |

## What this answers, and what it does not

The compiler accepts the double release, because `unsafe` is where the
obligation moves from the compiler to the reviewer. Miri catches it, and
names it. So the stage for this class is test time rather than build time,
and the cost is an interpreter run rather than a rejected compile.

The limit is the one that matters for a migration. Miri interprets Rust.
It cannot execute the C++ host that a real seam has on the other side, so
the case checked here uses a Rust stand-in for that host. The tool that
finds this defect cannot be pointed at the configuration the defect ships
in, which is the seam of `ffi/`.
