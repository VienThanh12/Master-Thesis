# Conformance / parity vectors (spec §11)

Language-neutral test vectors that **both** implementations (`cpp/`, `rust/`) must satisfy
identically. A vector is a sequence of operations, each with a canonical expected result. A
shared runner in each language executes a vector, produces a canonical *actual* transcript, and
(a) diffs it against the expected results in the file and (b) is compared across languages by
`run.sh` so the two implementations are proven to agree op-for-op (spec §11.1).

## File format

- One directive/operation per line. `#` starts a comment; blank lines are ignored.
- An operation line is `LHS => EXPECTED`, where `LHS` is `op` followed by whitespace-separated
  args (positional `ue_id` first, then `key=value` pairs) and `EXPECTED` is the **canonical
  result string** the op must produce.
- A `config` line (optional, must precede all operations) sets service parameters and has no `=>`.

### Directives / operations

```
config n_shards=<u64> queue_capacity=<usize> max_contexts_per_shard=<u64>

create  <id> cell=<u32>                 => Ok | Err(<Code>)
setup   <id>                            => Ok | Err(<Code>)
signal  <id> kind=<u8> len=<u16>        => Ok(accepted=<bool>,handled=<u64>) | Err(<Code>)
adddrb  <id> id=<u8> qfi=<u8> teid=<u32>=> Ok | Err(<Code>)
begin_reconf    <id> cell=<u32>         => Ok | Err(<Code>)
complete_reconf <id>                    => Ok | Err(<Code>)
abort_reconf    <id>                    => Ok | Err(<Code>)
release <id>                            => Ok | Err(<Code>)
lookup  <id>  => Ok(state=<State>,cell=<u32>,drbs=<n>,messages_handled=<n>) | Err(<Code>)
count                                   => <n>
shard   <id>                            => <idx>     # uses config n_shards (default 8)
```

- `<Code>` ∈ `NotFound | AlreadyExists | InvalidState | CapacityExceeded | InvalidArgument`.
- `<State>` ∈ `Idle | Connected | Reconfiguring | Released`.
- `last_activity_seq` is intentionally **not** part of any canonical result (spec §11.2).
- The `EXPECTED` string must be written exactly in the canonical form the runner emits
  (no spaces inside `Ok(...)`), so comparison is plain string equality.

## The suite

| Vector | Config | What it pins |
|--------|--------|--------------|
| `basic.vec` | defaults | The §11.3 example, the error model, DRB fill/overflow, reconfigure begin/complete/abort. |
| `states.vec` | defaults | The full §5.2 transition matrix: every legal transition, every illegal one from each state, `lookup` observed in `Idle`/`Connected`/`Reconfiguring`, release from `Idle` and from `Reconfiguring`, and the §6.1 rule that a rejected op mutates nothing. |
| `errors.vec` | defaults | Every §6.6 error code on every operation that can raise it, `ue_id == 0` rejected by all ten operations (§6.1), the payload boundary at 64/65 bytes, and the **precedence** between competing errors. |
| `capacity.vec` | `n_shards=2`, `max_contexts_per_shard=2` | `CapacityExceeded` on `create`, which no other vector reaches, and that the limit is **per shard**: one shard refuses while another still accepts, and a release frees capacity on that shard only. |
| `routing.vec` | `n_shards=4` | That the service routes by §8.1 rather than merely computing it: four ids on four different shards, with interleaved lookups asserting per-context state stays private to its own shard (§10.1 I1). |
| `shards.vec` | `n_shards=8` | Shard assignment for a power-of-two shard count. |
| `shards13.vec` | `n_shards=13` | Shard assignment for a **non**-power-of-two count. This is the case that distinguishes the specified `x mod n_shards` from the `x & (n_shards - 1)` optimisation, which agree whenever `n` is a power of two; all 13 residues and the u64 extremes are covered. |

Expected values for the shard vectors were derived from the §8.1 pseudocode by a
separate reference implementation rather than read back out of either runner, so
the vectors hold both sides to the specification and not merely to each other.

The precedence cases in `errors.vec` and `capacity.vec` deserve a note: §6 lists
the errors each operation can return without ordering them, so when two apply at
once the choice is unspecified. Both implementations happen to agree (argument
validation before key lookup, capacity before duplicate detection), and the
vectors pin that agreement so a later change on one side cannot drift silently.

Properties that a sequential transcript cannot express — the queue and completion
machinery of §7, FIFO execution (§10.2 O1), the fields `lookup` does not print,
and the activity-sequence discipline of §10.3 — are covered instead by the
per-language suites, `cpp/tests/test_{invariants,concurrency}.cpp` and
`rust/tests/{invariants,concurrency}.rs`, which mirror each other case for case.

## Running

```bash
spec/conformance/run.sh
```

This builds both runners (`cpp/build/conformance_runner`, `rust/target/release/conformance_runner`),
runs every `vectors/*.vec` through each, checks both against the expected results, and diffs the
C++ vs. Rust actual transcripts. Exit code is non-zero if any check or cross-language diff fails.
