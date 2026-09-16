# Chapter 3 — Types, config, errors

**Open, in this order:** `cpp/include/uecm/types.hpp`, `config.hpp`, `error.hpp`.
None of these has a `.cpp`. They are the vocabulary `ShardCore` speaks.

## The claim this layer makes

Every name in the public API is a direct encoding of spec sections 4, 5, 6.6
and 9. If a field is in the spec it is on the struct. If a field is inert the
comment says so, or the spec does, and no operation reads it.

## `types.hpp`

Read it top to bottom. It is short.

- `UeId` is `uint64_t`. Zero is invalid at the API, not as a C++ type. The
  type system will not stop you passing `0`. `ShardCore` will.
- `UeState` is an `enum class : uint8_t` with the four spec values. `Released`
  is in the enum so the type matches the spec. The map never holds a context
  in that state.
- `DrbEntry`, `CreateParams`, `ReconfigParams`, `SignalingMsg`, `SignalingAck`
  are the argument and reply structs of section 6.
- `UeContext` is the stored record. `drbs` is `std::vector<DrbEntry>`.
- `UeContextView` duplicates the same fields. That duplication is the spec:
  lookup copies, it does not alias. A `using UeContextView = UeContext` would
  have been shorter and would have invited returning a reference.

`SignalingMsg::payload` is a 64-byte array with a separate `payload_len`. The
service checks the length and otherwise ignores kind and payload. They exist
so a request has a realistic copy cost.

## `config.hpp`

Four run-time knobs, fixed at construction:

| Field | Default | Meaning |
| --- | --- | --- |
| `n_shards` | 8 | Worker-thread count. `Service` clamps 0 to 1. |
| `queue_capacity` | 1024 | Bounded queue depth. `BoundedQueue` clamps 0 to 1. |
| `max_contexts_per_shard` | 200000 | `CapacityExceeded` beyond this. |
| `initial_shard_capacity` | 4096 | `unordered_map::reserve` at construction. |

Two compile-time constants: `MAX_DRBS = 8`, `MAX_SIGNALING_PAYLOAD = 64`.
Benchmarks override the struct. They do not edit this header.

The file uses `std::size_t` without including `<cstddef>`. It compiles through
transitive headers on this toolchain. That is a nit in `docs/CODE_REVIEW.md`,
not a behaviour bug.

## `error.hpp`

```cpp
enum class OpError : std::uint8_t { NotFound, AlreadyExists, InvalidState,
                                    CapacityExceeded, InvalidArgument };

template <class T>
using OpResult = std::expected<T, OpError>;
```

That is the closed set. `to_string` exists so transcripts and tests print the
canonical names (`"NotFound"`, not `"not found"`).

How to read a result in this codebase:

```cpp
OpResult<void> r = core.create_context(id, params);
if (r.has_value()) { /* Ok */ }
else { OpError e = r.error(); }
```

`OpResult<void>` uses `std::expected`'s void specialisation. Success is
`return {}`. Failure is `return std::unexpected(OpError::NotFound)`.

Do not call `.error()` on a successful expected. That is undefined. The
invariants suite wraps the check in a helper `is_err` for that reason.

A call that happens **before `start()` or after `shutdown()`** is not an
`OpError`. It throws `std::logic_error` from `Service`. Mixing those two
failure kinds is a common first confusion.

## A check

Write (on paper, not in the tree) the `UeContext` you would have after:

```text
create_context(1001, {serving_cell_id=7, security_key=all zero})
setup_connection(1001)
handle_signaling(1001, {kind=3, payload_len=10})
```

You should have `state == Connected`, `serving_cell_id == 7`, `drbs` empty,
`messages_handled == 1`, `rrc_transaction_id == 0`. You should not know
`last_activity_seq` as a specific number yet (it is a per-service counter).
That is chapter 5.

## Do not

Do not open `message.hpp` yet. `Request` is a transport envelope, not a
domain type. Do not hunt for a constructor that validates `ue_id != 0`.
Validation is in `ShardCore`, on every operation, by spec section 6.1.
