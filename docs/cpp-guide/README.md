# Learning the C++ UECM tree

This is a reading path for `cpp/`, written as if you have never opened it.
It is not a C++ tutorial and it is not a substitute for the specification.
It tells you **which file to open next, why it exists, and what to ignore until later**.

The encyclopedia in [`../guide/`](../guide/README.md) maps the whole thesis
repository. Come back here when the question is "how does this C++ service
work?"

## Before chapter 1

You need a C++23 compiler (g++ 13+ or clang 17+), CMake 3.20+, and Ninja.
Build once so every later chapter can point at a real binary:

```bash
cd cpp
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

That library is two translation units. Everything else in `cpp/` is a client
of it: tests, a parity runner, a benchmark driver, and two attribution probes
that are **not** the compared implementation.

## How to read

Each chapter names:

1. **Open these files.** Do that before reading the rest of the chapter.
2. **The claim this layer makes.** One paragraph.
3. **Walk-through.** What to look at, in order.
4. **A check.** A command or a question that shows you understood it.
5. **Do not.** The nearby file that looks related and will confuse you now.

Do the chapters in order. The sequential core (`ShardCore`) is the whole
service minus threads. If you skip to `Service` first you will spend an
afternoon on queues while the state machine is still opaque.

| Chapter | File | Layer |
| --- | --- | --- |
| [1 Orientation](01-orientation.md) | this tree | why the code exists |
| [2 The spec](02-the-spec.md) | `spec/SPECIFICATION.md` | the contract both languages encode |
| [3 Types, config, errors](03-types-and-errors.md) | three headers | the vocabulary |
| [4 Hashing](04-hashing.md) | `hash.hpp` | how a UE lands on a shard |
| [5 ShardCore](05-shard-core.md) | `shard_core.hpp/.cpp` | the sequential heart |
| [6 Queue and messages](06-queue-and-messages.md) | `message.hpp`, `bounded_queue.hpp` | the handoff |
| [7 Service](07-service.md) | `service.hpp/.cpp` | threads around chapter 5 |
| [8 Tests](08-tests.md) | `cpp/tests/` | what each binary can prove |
| [9 Conformance](09-conformance.md) | `spec/conformance/` | both languages, one transcript |
| [10 Bench and probes](10-bench-and-probes.md) | `cpp/bench/`, two headers | measurement, not the library |
| [11 Twin and edges](11-twin-and-edges.md) | `rust/`, `docs/CODE_REVIEW.md` | what looks like a bug and is not |

A first afternoon is chapters 1 to 5 plus the `test_shard_core` binary.
A second sitting is 6 to 8. Conformance and the bench can wait until you
can draw the request path from a typed API call to `ShardCore::handle_signaling`
without looking.

## Companion files, not chapters

| Path | Use it for |
| --- | --- |
| [`../../cpp/README.md`](../../cpp/README.md) | build flags, sanitiser and coverage scripts |
| [`../../spec/SPECIFICATION.md`](../../spec/SPECIFICATION.md) | normative behaviour |
| [`../../rust/README.md`](../../rust/README.md) | the twin, module for module |
| [`../CODE_REVIEW.md`](../CODE_REVIEW.md) | known edges (16 September 2026). Not the independent expert review. |
| [`../guide/03-evidence.md`](../guide/03-evidence.md) | how `cpp/` sits among `spec/`, `rust/`, `bench/`, `faults/`, `ffi/` |

`faults/cpp/` is a different tree. Those sources inject defects for research
question 2. They are not how the production library is written. Do not start
there.
