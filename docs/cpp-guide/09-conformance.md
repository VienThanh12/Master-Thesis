# Chapter 9 — Conformance: both languages, one transcript

**Open:** `spec/conformance/README.md`, then `spec/conformance/vectors/basic.vec`,
then `cpp/tools/conformance_runner.cpp`.

## The claim this layer makes

The C++ unit tests prove this library against itself. Conformance proves
**C++ and Rust against the spec and against each other**. A vector is a
language-neutral script. Each language's runner executes it against the
threaded `Service` and prints a canonical transcript, one line per op.
`spec/conformance/run.sh` diffs those transcripts.

If you change `ShardCore` behaviour and only update `test_shard_core.cpp`,
you can split the twins. Always run the shared harness after a behaviour
change.

## A vector file, by example

`basic.vec` is `test_shard_core.cpp` written as a script. First lines:

```text
config n_shards=8 queue_capacity=1024 max_contexts_per_shard=200000
create 1001 cell=7                 => Ok
setup 1001                         => Ok
signal 1001 kind=3 len=10          => Ok(accepted=true,handled=1)
```

`=>` is the canonical string the runner must emit. Comparison is plain
string equality. No spaces inside `Ok(...)`. `last_activity_seq` is
intentionally absent from every expected string (spec §11.2): the two
languages may assign different numbers as long as the discipline of
§10.3 holds, which is a typed-API test, not a transcript test.

## The seven hand-written vectors

| Vector | What it pins |
| --- | --- |
| `basic.vec` | The §11.3 walk, errors, DRB fill, reconfigure begin/complete/abort. |
| `states.vec` | Full §5.2 matrix, including abort leaving the target cell in place. |
| `errors.vec` | Every code on every op that can raise it, plus competing-error precedence. |
| `capacity.vec` | Shard-full `create`, limit is per shard, release frees that shard only. |
| `routing.vec` | Routing is the real `shard_index`, not a toy round-robin. State stays private to a shard. |
| `shards.vec` | Assignment at 8 shards (power of two). |
| `shards13.vec` | Assignment at 13 shards (catches `x & (n-1)`). |

Known-answer shard vectors were derived from the spec pseudocode, not from
either runner, for the same reason as `test_hash.cpp`.

Two configs are **not** in this family: `n_shards=0` and `queue_capacity=0`.
The runners would disagree. Do not add those vectors to "be thorough".

## The C++ runner

`conformance_runner.cpp` is a small interpreter:

1. Parse lines, strip `#` comments.
2. On `config`, construct a `Service` with those knobs and `start()`.
3. On each op, call the typed API, format the canonical string, print it,
   compare to `=>` if present.
4. `shard` does not call the service. It prints `shard_index(id, n_shards)`
   using the **raw config value**. That is why `n_shards=0` is a footgun.

You do not need to memorise the parser. You need to know that the runner
exercises `Service`, not bare `ShardCore`. Threading, routing, and
completions are on the path. FIFO under contention is still not: a `.vec`
is sequential. That is why `test_concurrency.cpp` exists.

## How to run it

One vector, C++ only:

```bash
cmake --build cpp/build --target conformance_runner
./cpp/build/conformance_runner spec/conformance/vectors/basic.vec
```

Both languages, every hand-written vector, plus the oracle and generated
family:

```bash
spec/conformance/run.sh
```

`run.sh --random 60 --ops 2000` is the full generated campaign (minutes).
Do not start there. The seven files in `vectors/` are the ones to read.

The independent Python model in `spec/conformance/model.py` is a third
implementation. Its expectations must not be derived from `cpp/` or
`rust/`. If you are learning C++, you can ignore it until you are changing
the spec.

## A check

Run `basic.vec` through the C++ runner. Then open `test_shard_core.cpp` and
tick off each `CHECK` against a line of the vector. They should be the
same story. The extra abort path on UE 3003 is in the vector and not in
that particular test file. `test_state_matrix.cpp` covers it as a cell.

## Do not

Do not edit a `.vec` expected string to match a C++ change without checking
Rust and the spec. Do not assume transcript equality means memory safety.
Sanitisers are `cpp/sanitise.sh`. Do not put activity-sequence numbers
into a vector.
