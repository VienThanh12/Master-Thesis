# Chapter 2 — The spec is the first source file

**Open:** `spec/SPECIFICATION.md`. Read sections 1 to 7 and section 10.
Skim section 8 (hashing) and section 9 (defaults). Leave 11 to 13 for
chapters 9 and 11.

## The claim this layer makes

The C++ you are about to read is not free to invent behaviour. Both
implementations **must** match this document. Where C++ and Rust are forced
into different idioms for the same requirement, the difference is written
down in section 12 rather than papered over. If the code and the spec
disagree, the spec wins until someone amends it. The spec is frozen at
version 1.0 (tag `spec-v1.0`).

## What to extract, not memorise

You need six facts before any header makes sense.

### 1. The record

Section 4 lists the fields. Four of them are **inert**: stored so size and
copy cost look like a real context, never read by an operation.

| Field | Live? |
| --- | --- |
| `ue_id`, `state`, `serving_cell_id`, `drbs` (via `drb_id` only), `messages_handled`, `last_activity_seq` | yes |
| `rrc_transaction_id`, `security_key`, `qos_flow_id`, `teid` | inert |

`drbs` is a dynamic list on purpose (allocator study). It is not a fixed
array. `MAX_DRBS` is 8.

`lookup` returns a **by-value snapshot** (`UeContextView`). The service must
not hand out a reference into live shard state. That keeps shared-nothing
intact and keeps the two languages comparable.

### 2. The state machine

Section 5.2 is a table. Learn it as "which op is legal from which state",
not as a diagram you can redraw from memory. Two traps:

- `begin_reconfigure` writes `serving_cell_id = target_cell_id` **when the
  procedure begins**, not when it completes.
- `abort_reconfigure` restores `state` to `Connected` and **does not** roll
  the cell back. After an abort, `lookup` reports the cell the UE failed to
  move to. That is deliberate. The record has no saved pre-handover cell.

`complete_reconfigure` and `abort_reconfigure` therefore share a body in
C++. That looks like a copy-paste bug. It is section 6.5.

### 3. The closed error set

Exactly five codes, stored as `u8`: `NotFound`, `AlreadyExists`,
`InvalidState`, `CapacityExceeded`, `InvalidArgument`. Success is `Ok`.
There is no sixth code for "you called this while the service was stopped".
That is a caller error, reported out of band (C++ throws `std::logic_error`).

On any error the context must remain unchanged, and a failed op must not
consume an activity-sequence value.

Section 6 lists which errors each op **can** return. It does **not** always
say which one wins when two apply at once. Both implementations picked the
same order (capacity before duplicate on create, argument checks before
lookup on signaling). Tests pin that agreement. You will see it as
if-statements in `shard_core.cpp`. The order of those ifs is load-bearing.

### 4. Shared-nothing

Section 7, in one sentence: one worker owns one shard's map, callers only
enqueue, the queue is bounded and **blocks** when full, each request carries
its own completion, the worker is strictly FIFO.

There is no shared-read fast path. `lookup` pays the same queue handoff as a
mutating op. End-to-end latency is dominated by that handoff, not by the
map operation. The thesis measures that split later. You only need to know
it so you do not go looking for a lock on `UeContext`. There is none.

### 5. `count()` is not a snapshot

It fans out one request per shard and sums. Concurrent mutations mean the
sum need not equal the population at any instant. It is exact when the
service is quiescent. Implementations must not add a cross-shard lock to
make it atomic. That would be shared state the model forbids.

### 6. Hashing is pinned

Section 8. Shard selection is SplitMix64 then modulo. The map key hash is
FNV-1a over the eight little-endian bytes of `ue_id`. Both languages must
produce bit-identical shard assignments and bit-identical digests. Standard
library hashers are not allowed to be an accidental language advantage.

## A check

Without looking at C++, answer:

1. Can `handle_signaling` run in `Reconfiguring`?
2. After `abort_reconfigure`, what is `serving_cell_id`?
3. What does a second `release_context` on the same id return?
4. Is `lookup` allowed to return a `const UeContext&`?

Answers: (1) no, `InvalidState`. (2) the target cell from `begin_reconfigure`.
(3) `NotFound`, not `Ok`. (4) no, it must copy.

## Do not

Do not read section 11's vector grammar yet. Do not read section 12's probe
numbers and treat them as the thesis result. Probes are indicative and
host-bound. The compared configurations are named in section 12 as the
standard map and the standard queue.
