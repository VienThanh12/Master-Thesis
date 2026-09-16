# Chapter 11 — The Rust twin, and things that look like bugs

**Open:** `rust/src/lib.rs`, the matching `rust/src/*.rs` files, spec
§12, and `docs/CODE_REVIEW.md`.

## The claim this layer makes

You do not need to learn Rust to finish the C++ tree. You do need the
map, because every C++ design choice that looks odd is usually "this is
how C++ spells the same requirement". Spec §12 is that dictionary.

## File for file

| C++ | Rust |
| --- | --- |
| `include/uecm/types.hpp` | `src/types.rs` |
| `include/uecm/config.hpp` | `src/config.rs` |
| `include/uecm/error.hpp` | `src/error.rs` |
| `include/uecm/hash.hpp` | `src/hash.rs` |
| `include/uecm/shard_core.hpp` + `src/shard_core.cpp` | `src/shard_core.rs` |
| `include/uecm/message.hpp` | `src/message.rs` |
| `include/uecm/bounded_queue.hpp` | `std::sync::mpsc::sync_channel` (standard arm) |
| `include/uecm/service.hpp` + `src/service.cpp` | `src/service.rs` |
| `include/uecm/flat_map.hpp` | (no twin: C++-only map probe) |
| `include/uecm/ring_queue.hpp` | (no twin: C++-only ring probe) |
| — | `src/mutex_queue.rs` (`--features mutex-queue`, Rust-only queue probe) |
| `tools/conformance_runner.cpp` | `src/bin/conformance_runner.rs` |
| `bench/bench.cpp` | `examples/bench.rs` |
| `tests/test_*.cpp` | `tests/*.rs` (same questions, different names) |

`OpResult<T>` is `std::expected` here and `Result` there. Request is a
tagged struct plus `std::promise` here and an enum of typed oneshots
there. Hashing hooks up as `FnvHash` here and `FnvBuildHasher` there.
Lifecycle failure is `throw std::logic_error` here and `panic!` there.

The state machine, the five errors, the shard function, the FNV-1a
digest, the queueing discipline, and the completion 1:1 rule are not
allowed to differ.

## Things that look like bugs and are not

From `docs/CODE_REVIEW.md`, the table you will reach for:

| Observation | Why it is intended |
| --- | --- |
| `complete_reconfigure` and `abort_reconfigure` share a body | Spec §6.5: abort restores state only. |
| `UeState::Released` is never stored | Spec I2: release deletes the record. |
| `count()` is not a snapshot | Spec §6.7, on purpose. |
| Ops before `start()` / after `shutdown()` throw | Spec §7.1: not an `OpError`. |
| `flat_map.hpp`, `ring_queue.hpp` | Probes, not compared arms. |
| Inert fields that nobody reads | Spec §4.2: size and copy cost, plus a trap for a third implementation. |

Error precedences §6 left unordered are pinned in both test suites and
already agree.

## Known edges (real, logged, not on the campaign path)

1. **`queue_capacity == 0`.** C++ clamps to 1. Compared Rust `sync_channel(0)`
   is a rendezvous. Default and campaign capacity is 1024.
2. **Public `shard_index(_, 0)`.** C++: undefined behaviour. Rust: panic.
   `Service` clamps. The free function does not.
3. **Concurrent `shutdown()` while submitting.** C++ can race on `running_`.
   Rust cannot express that aliasing. Sequential misuse is guarded.
4. **Worker death.** `future.get()` throws if the promise is abandoned.
   Normal `ShardCore` paths do not throw.

An agent pass recorded these on 16 September 2026. It does not close
TODO item D2 (independent expert review). Suggested fixes, if any, are
in that note. None is required for current thesis claims.

## `faults/` is the next tree, not the next chapter of this one

`faults/cpp/*.cpp` injects fourteen defect classes (seven in-guarantee for
safe Rust, seven boundary). `seam_double_free` is `double_free` rewritten
through `unsafe`, not a new class. The C++ half of that pair stays
unchanged so only the Rust column moves. Read `faults/` when you are
learning RQ2, with `faults/README.md` in hand. Do not confuse those
sources with `cpp/src/`.

`ffi/` is RQ4: a C++ host over a Rust component through a C ABI. The
core C++ library you just learned stays out of that seam.

## A check

Open spec §12's C++ bullet list and tick each bullet against a file you
have now read. You should recognise every idiom: `std::expected`, tagged
`Request`, `std::promise`, mutex queue, `unordered_map` plus `FnvHash`,
`count()` wrapped in `OpResult` for variant uniformity, `logic_error` on
lifecycle.

Then, without looking, name the two CMake flags you must **not** turn on
when you want the compared C++ arm.

## What to do on day three

You know the library if you can:

1. Draw the request path from `Service::handle_signaling` to the map
   insert-or-update and back through the promise.
2. Say which file you would open to change a state-machine rule, a hash,
   a queue bound, or a transcript line.
3. Run `ctest` and `spec/conformance/run.sh` after a behaviour edit.
4. Leave probes, sanitiser builds, and campaign logs out of a sentence
   that claims a result.

When a later-you is lost, start again at chapter 5, not at `bench.cpp`.
