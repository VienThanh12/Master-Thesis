# Chapter 8 — Tests as a reading order

**Open:** `cpp/tests/test_util.hpp`, then the six `test_*.cpp` files **in the
order below**. Do not read them all at once. Each file answers a question
the previous one cannot.

## The claim this layer makes

There is no gtest. Each file is a standalone `main()` linked against `uecm`,
registered in the `foreach` list in `CMakeLists.txt`. `rust/tests/` mirrors
these case for case. If you add a C++ case, the twin is the Rust file of
the same question.

`CHECK(cond)` increments a counter, prints `FAIL file:line: cond` on
failure, and does not abort. The process exit code is `summary(...)`.
Failed checks still run the rest of the file, so you see more than the
first breakage.

## The six questions

| File | Question it can answer | What it cannot |
| --- | --- | --- |
| `test_hash.cpp` | Are the pinned hashes the spec's hashes? | Anything about UE state. |
| `test_shard_core.cpp` | Does the sequential core walk the §11.3 example, the error model, DRBs, and one reconfigure path? | Every cell of the transition matrix. Threads. |
| `test_state_matrix.cpp` | Every op against every condition, exact error, post-state, no mutation on failure, plus unordered precedences. | Queueing, FIFO, completions. |
| `test_invariants.cpp` | Fields the `.vec` transcript never prints, §6.1 no-mutation, activity-sequence discipline, I1/I4. | Concurrency. |
| `test_service.cpp` | Same functional path through **threads**, plus a disjoint-id concurrent smoke test, plus sequential lifecycle misuse. | FIFO, 1:1 completion, capacity-1 backpressure. |
| `test_concurrency.cpp` | Blocking backpressure loses nothing, per-shard FIFO, concurrent lookup, completion 1:1. | The 36-cell matrix (that is `test_state_matrix`). |

Run them as you read:

```bash
cd cpp
ctest --test-dir build --output-on-failure
```

Or one binary at a time, which is better while learning:
`./build/test_shard_core`.

## How to read a test file

Start at the comment. Several of these files spend twenty lines saying
**why they exist**, because the reason is the thing you would otherwise
rediscover as a gap. `test_state_matrix.cpp` in particular: the other
suites *sample* paths, this one *enumerates* them.

Then find the table or helper that encodes the spec. In
`test_state_matrix.cpp` that is `kExpect[][]` plus `Cond` and `Op` enums.
`Released` is not a condition. After release the id is `Absent`. The file
asserts that equivalence rather than assuming it.

`test_invariants.cpp` works through the typed API because a conformance
transcript only prints state, cell, DRB **count**, and `messages_handled`.
`security_key` round-trips, `rrc_transaction_id` stays 0, a rejected
`add_drb` does not append, a failed op does not consume `last_activity_seq`,
`release` does not consume one either. Those sentences are spec §6.1 /
§10.3. The test is those sentences in code.

`test_concurrency.cpp` is the first file that is really about C++ as a
concurrent language. Build it under ThreadSanitizer when you get to
`sanitise.sh`. The Rust twin needs no sanitizer for data-race freedom.

## Adding a test later

1. New `tests/foo.cpp` with its own `main()` and `test_util.hpp`.
2. Add `foo` to the `foreach` in `CMakeLists.txt`.
3. Add the matching file under `rust/tests/`.

Do not add gtest to "make this look like a real project". Dependency
freedom is load-bearing for the adoption-cost argument (RQ4).

## A check

In `test_state_matrix.cpp`, find the cell for `handle_signaling` from
`Reconfiguring`. Confirm it expects `InvalidState` and that the helper
asserts the cell id did not change. Then find the precedence section at
the bottom (capacity before duplicate on create). Match those ifs to
`shard_core.cpp` line by line.

## Do not

Do not treat a green `ctest` as "the C++ is memory-safe". That is
`sanitise.sh`. Do not treat a green `test_service` as "the concurrency
model is verified". That is `test_concurrency` plus TSan. Do not edit a
test to match code you just changed until you have checked the spec. The
test might be the thing that is right.
