# Chapter 5 — ShardCore, the sequential heart

**Open:** `cpp/include/uecm/shard_core.hpp`, then `cpp/src/shard_core.cpp`.
Keep `spec/SPECIFICATION.md` §5 and §6 beside them.

This is the chapter that pays for the rest. After it you can read every
other file as plumbing.

## The claim this layer makes

`ShardCore` is the single-threaded operation processor for **one** shard. It
owns that shard's map and implements the state machine. It is **not**
thread-safe. In the full service, exactly one worker thread ever calls these
methods for a given shard, so there is no lock on the map.

If you call `ShardCore` from two threads yourself, that is your data race.
The library's `Service` will not do that.

## The class, in the header

```text
ShardCore(const Config&, atomic<uint64_t>& activity_seq)

mutating: create, setup, signaling, add_drb, begin/complete/abort reconfigure, release
read-only: lookup, count
```

The map type is `std::unordered_map<UeId, UeContext, FnvHash>` unless the
`UECM_FLAT_MAP` probe is on. Ignore the `#ifdef` on a first read. The
measured arm is the `unordered_map`.

`count()` is `map_.size()`. Cheap, exact for this shard, and not an
`OpResult` because it cannot fail.

`next_seq()` is a relaxed fetch-add on a **service-wide** atomic. Shards
share the counter. They do not share the map. The spec wants a monotonic
per-service sequence stamped onto successful mutating ops. Relaxed is
enough for a counter that is not used for synchronisation.

## How to read `shard_core.cpp`

Every mutating method has the same spine. Learn the spine, then the
differences.

1. Reject `ue_id == 0` with `InvalidArgument`.
2. Extra argument checks that do not need the map (payload length, capacity
   of the shard on create).
3. `map_.find`. Absent means `NotFound` (except create, which wants absence).
4. State check. Wrong state means `InvalidState` and **no writes**.
5. Extra content checks (`MAX_DRBS`, duplicate `drb_id`).
6. Mutate. Stamp `last_activity_seq = next_seq()` except on `release`.
7. `return {}` or `return value`.

### `create_context`

Order of checks is the precedence the spec left unordered:

1. `ue_id == 0` → `InvalidArgument`
2. `map_.size() >= max_contexts_per_shard` → `CapacityExceeded`
3. key present → `AlreadyExists`

Capacity before duplicate. A full shard that already contains the id reports
`CapacityExceeded`, not `AlreadyExists`. Tests pin this.

On success the context is `Idle`, `drbs` empty, counters zero,
`rrc_transaction_id` left at 0, security key copied from params.

### `setup_connection` / `handle_signaling` / `add_drb`

`setup` requires `Idle`, moves to `Connected`.

`handle_signaling` checks payload length **before** lookup. An oversized
payload on a missing id is `InvalidArgument`, not `NotFound`. Then it
requires `Connected`, increments `messages_handled`, returns
`SignalingAck{true, new_count}`. `kind` and `payload` are not inspected.
`accepted` is always true on the success path.

`add_drb` requires `Connected`, then `drbs.size() < MAX_DRBS`, then unique
`drb_id`. Only `drb_id` is compared. `qos_flow_id` and `teid` are stored
verbatim.

### Reconfigure pair

`begin_reconfigure` requires `Connected`, sets `Reconfiguring`, **and**
writes `serving_cell_id = params.target_cell_id`.

`complete_reconfigure` and `abort_reconfigure` are the same function body:
require `Reconfiguring`, set `Connected`, stamp the sequence. Neither
touches the cell. Read them twice. The sameness is the spec.

### `release_context`

Find, erase, return. No sequence stamp: the record is gone. Valid from
Idle, Connected, or Reconfiguring. A second release is `NotFound`.

`Released` never appears in the map. Spec invariant I2.

### `lookup`

Copy every field into a `UeContextView`, including `drbs` by value. Const
method. Does not stamp the sequence.

## Constructor

`map_.reserve(cfg_.initial_shard_capacity)` so the first inserts do not
rehash. Same default (4096) on both languages.

## A check

Run the sequential suite:

```bash
cmake --build cpp/build --target test_shard_core test_state_matrix test_invariants
./cpp/build/test_shard_core
./cpp/build/test_state_matrix
./cpp/build/test_invariants
```

Then, in `shard_core.cpp`, find the two reconfigure-complete functions and
confirm they do not write `serving_cell_id`. Trace `create_context(1001, …)`
from `test_shard_core.cpp` through the implementation with your finger.
That test is spec §11.3 in C++ form. The same sequence reappears as
`spec/conformance/vectors/basic.vec`.

## Do not

Do not add a mutex to `ShardCore` "to make it safe". Safety is "one worker
owns me", which is `Service`'s job. Do not merge `UeContext` and
`UeContextView`. Do not make `abort_reconfigure` restore the old cell. There
is no old cell on the record.
