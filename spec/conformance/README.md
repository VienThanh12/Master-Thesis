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

## Running

```bash
spec/conformance/run.sh
```

This builds both runners (`cpp/build/conformance_runner`, `rust/target/release/conformance_runner`),
runs every `vectors/*.vec` through each, checks both against the expected results, and diffs the
C++ vs. Rust actual transcripts. Exit code is non-zero if any check or cross-language diff fails.
