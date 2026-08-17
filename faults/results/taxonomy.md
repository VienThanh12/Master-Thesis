# RQ2 defect-class taxonomy

- C++ compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (`-std=c++23`)
- Rust compiler: `rustc 1.97.1 (8bab26f4f 2026-07-14)` (`--edition 2021`)
- ASLR wrapper: `setarch x86_64 -R`
- `TSAN_OPTIONS`: `detect_deadlocks=1:second_deadlock_stack=1`
- TSan deadlock-detector control (`deadlock_control.cpp`, inversion without blocking):
  **detected (detector live; the undetected verdict below is a real outcome)**

`integer_overflow` is built with `-O -C overflow-checks=off` so it matches
the `opt-level = 2` profile the thesis compares (spec §3). With the `rustc`
defaults it would panic, and the table would record a detection the measured
configuration does not have.

`lock_order_deadlock` is run 12 times under TSan rather than once.
Its detection is schedule-dependent: TSan closes a lock-order cycle only from
acquisitions that *succeed*, so a run whose first inversion blocks never
produces the second edge. `flaky` records that, where a single run would
record whichever outcome the scheduler happened to give.

| Defect class | C++ ASan | C++ TSan | C++ UBSan | C++ detection stage | Rust outcome | Note |
|---|---|---|---|---|---|---|
| use_after_free | detected | detected | clean | runtime (ASan+TSan) | compile-time prevented (E0499) | - |
| double_free | detected | clean | clean | runtime (ASan) | compile-time prevented (E0382) | - |
| iterator_invalidation | detected | detected | clean | runtime (ASan+TSan) | compile-time prevented (E0502) | - |
| data_race | clean | detected | clean | runtime (TSan) | compile-time prevented (E0373,E0382,E0502) | - |
| unguarded_shared_mutation | clean | detected | clean | runtime (TSan) | compile-time prevented (E0502,E0524,E0597) | - |
| lock_order_deadlock | hung | flaky | hung | runtime, intermittent (TSan) | not prevented (compiles; deadlocks) | TSan reported in 7/12 runs |
| lost_update | clean | clean | clean | undetected | not prevented (compiles; wrong result) | - |
| leak_cycle | detected | clean | clean | runtime (ASan) | not prevented (compiles; ran clean) | - |
| integer_overflow | clean | clean | detected | runtime (UBSan) | not prevented (compiles; wrong result) | - |
| worker_failure_blast_radius | clean | clean | clean | undetected | not prevented (compiles; wrong result) | - |
