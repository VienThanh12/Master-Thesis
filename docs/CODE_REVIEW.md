# Implementation review: C++ and Rust UECM

**Date:** 16 September 2026  
**Scope:** production `cpp/`, `rust/src` plus tests and examples, `ffi/`  
**Out of scope:** `faults/` (injected RQ2 catalogue, including `seam_double_free`)  
**This is not D2.** `docs/TODO.md` item D2 is an independent review by two language experts with a pre-committed protocol. This note is an agent pass against the frozen spec. It does not close that threat.

## Verdict

The production implementations look sound. No logic, memory, or state-machine bug was found on the path the thesis measures. Nothing here would invalidate the parity suite or the reported campaign (`campaign-20260827-151927`).

The only accidental behavioural mismatch between the two libraries is `queue_capacity == 0` on the standard Rust channel. Everything else is an intentional spec choice, an FFI contract, or a lifecycle edge that C++ can still express and Rust cannot.

## What was run

| Check | Result |
| --- | --- |
| `cd rust && cargo test --release` | all passed |
| six C++ binaries from `cpp/build-san-address-undefined/` (`test_hash`, `test_shard_core`, `test_invariants`, `test_state_matrix`, `test_service`, `test_concurrency`) | 0 failures, no ASan/UBSan report |

## What is in good shape

- State machine, error codes, and precedence match `spec/SPECIFICATION.md` and each other. The 36-cell matrix, capacity-before-duplicate, payload-before-lookup, and abort-does-not-roll-back-the-cell cases are pinned in both languages (`cpp/tests/test_state_matrix.cpp`, `rust/tests/state_matrix.rs`).
- Shared-nothing threading is correct under the intended lifecycle: one worker owns each `ShardCore`, callers only enqueue, completions are 1:1.
- Hashing is pinned (SplitMix64 shard index, FNV-1a over little-endian key bytes) with known-answer tests on both sides.
- `rust/src` has no `unsafe`. The C++ suite under ASan+UBSan did not report use-after-free, leaks, or UB.

## Findings

Severity is for the *code*, not for the thesis grade. None of items 1–5 is exercised by the reported campaign.

### 1. `queue_capacity == 0` diverges (parity, accidental)

C++ `BoundedQueue` clamps 0 to 1 (`cpp/include/uecm/bounded_queue.hpp`). The Rust mutex-queue probe does the same (`rust/src/mutex_queue.rs`). The measured Rust arm uses `sync_channel(self.cfg.queue_capacity)` (`rust/src/service.rs`). `sync_channel(0)` is a rendezvous channel, not a 1-slot buffer.

Default and campaign capacity is 1024, so reported numbers are unaffected. The mismatch would appear if someone configured capacity 0.

**If fixing:** clamp on the standard `sync_channel` path, `queue_capacity.max(1)`, to match C++ and the probe.

### 2. Public `shard_index(_, 0)` (edge-case crash / UB)

`Service` clamps `n_shards == 0` to 1. The free function does not:

- C++: `x % n_shards` in `cpp/include/uecm/hash.hpp` is undefined behaviour when `n_shards == 0`
- Rust: `x % n_shards` in `rust/src/hash.rs` panics

Conformance vectors never pass 0. The `shard` op in both runners uses the raw config value, not the clamped service value, so a vector with `n_shards=0` would disagree with routing even if the modulo were defined.

### 3. C++ lifecycle vs concurrent `shutdown()` (API hazard)

`running_` is a plain `bool` (`cpp/include/uecm/service.hpp`). Spec §7.1 forbids ops outside the running window, and sequential misuse is guarded (`std::logic_error` in C++, panic in Rust). That path was unguarded until 2026-08 and is now covered by `test_service` / `concurrency.rs`.

If one thread calls `shutdown()` while another is still submitting, C++ can race on `running_` and `shards_`, enqueue work after the `Stop` sentinel, then hang or hit a broken promise when the queue is destroyed. Rust `shutdown` takes `&mut self`, so that aliasing does not compile.

Benches join producers before shutdown. The campaign does not exercise this. Spec §12's "verified data-race free under ThreadSanitizer" claim is about the suite, which does not concurrent-shutdown.

### 4. FFI handle contract (documented unsafety)

`ffi/rust-uecm-ffi/src/lib.rs`: `uecm_service_destroy` is `Box::from_raw` with no synchronisation. Concurrent destroy, double-destroy, or a wild pointer is use-after-free. Ops on a shared handle are intended to be safe. Destroy is "exactly once, nobody else using it" (`uecm_ffi.h`).

`uecm_count(null)` returns `0`, which is indistinguishable from an empty service. Other entry points return `UECM_ERR_NULL` (`-1`).

This is the RQ4 C-ABI seam. The core library stays `unsafe`-free. The hazard lives at the boundary, which is the point the thesis makes.

### 5. Worker death panics the caller (library sharpness)

Rust: `expect("worker alive")` / `expect("completion")` on every typed API method.  
C++: `future.get()` throws if the promise is abandoned.

Normal `ShardCore` paths do not panic or throw. This is "worker died" treated as an invariant violation, matching §7.1's out-of-band reporting for caller errors.

### 6. Spec claim vs crate (documentation drift, closed in the spec)

On the day of this pass, `spec/SPECIFICATION.md` §12 said the Rust core was `#![forbid]`-clean. There is no `#![forbid(unsafe_code)]` in `rust/src/lib.rs`. The claim is true in practice (no `unsafe` in `rust/src`). The attribute is missing, so the crate would not refuse a later `unsafe` block.

The spec recording is now corrected (16 September amendment, version remains 1.0). The crate still lacks the attribute.

**If fixing the crate:** add `#![forbid(unsafe_code)]` to `rust/src/lib.rs`. That matches the recorded claim and costs nothing.

## Things that look like bugs and are not

| Observation | Why it is intended |
| --- | --- |
| `complete_reconfigure` and `abort_reconfigure` share one body | Spec §6.5: abort restores state only, not `serving_cell_id` |
| `UeState::Released` is never stored | Spec I2: release deletes the record |
| `count()` is not a snapshot | Spec §6.7, on purpose |
| Ops before `start()` / after `shutdown()` throw or panic | Spec §7.1: not an `OpError` |
| FFI omits reconfigure and sends a zero payload / key | Narrow RQ4 seam, not a full API mirror |
| `flat_map.hpp`, `ring_queue.hpp`, `mutex_queue.rs` | Attribution probes, not the compared arms |

Error precedences that §6 leaves unordered are pinned in both test suites and already agree: capacity before duplicate on create, argument checks before key lookup on signaling, state then DRB cap then duplicate on `add_drb`.

## Nits

- `cpp/include/uecm/config.hpp` uses `std::size_t` without `#include <cstddef>`. It compiles via transitive headers on this toolchain.
- C++ `start()` sets `running_ = true` before spawning workers. If `std::thread` construction throws mid-spawn, ops can be accepted against a shard with no consumer. Unrealistic on the measurement host. Rust sets `running` only after the spawn loop.

## Suggested fixes, if any

None of these is required for the current thesis claims. Cheapest first:

1. Add `#![forbid(unsafe_code)]` to `rust/src/lib.rs`.
2. Clamp `queue_capacity.max(1)` on the standard Rust `sync_channel` path (and document `shard_index` for `n_shards == 0`).
3. Make `uecm_count(null)` distinguishable, or document that 0 means both null and empty.
4. Leave concurrent `shutdown` as a language difference. Encoding it as a mutex on C++ would add shared state the concurrency model forbids for the compared arm.

Do not re-measure after (1). Re-measure only if (2) is adopted *and* a campaign is ever run at capacity 0, which the frozen parameter table does not do.

## Where this is recorded

| File | What it now says |
| --- | --- |
| `spec/SPECIFICATION.md` §12 and §13 | Dated 16 September recording. `#![forbid]` claim corrected. Three edges logged. Requirements unchanged. Version stays 1.0. |
| `docs/TODO.md` D2 and Phase 5 | This pass does not close D2. `queue_capacity == 0` sits outside the vector suite. |
| `rust/README.md`, `cpp/README.md`, `ffi/README.md` | Same edges, at the component. `uecm_ffi.h` now says `uecm_count(null)` returns 0. |
| `docs/guide/03-evidence.md`, `README.md`, `AGENT.md` §7 | Pointers. D2 remains the two-expert protocol. |
