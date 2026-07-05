# Shared Specification — UE Context Management Service

**Version:** 0.1 (DRAFT — not yet frozen)
**Status:** Draft for supervisor review. Once approved, bump to 1.0 and tag `spec-v1.0`.
**Applies to:** the C++ (`cpp/`) and Rust (`rust/`) implementations.

> This document is the *fairness baseline* of the thesis. Both implementations MUST
> conform to it exactly. Any place where the two languages force a different idiom for
> the same requirement MUST be recorded in Section 12 (Recorded Deviations) so it can be
> weighed in the evaluation. The specification is itself a deliverable and the primary
> control against implementation bias.
>
> Requirement keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY** are used in the
> RFC 2119 sense.

---

## 1. Purpose and scope

The subsystem under study is a **UE Context Management (UECM) service**, modeled on a
gNB-CU-CP service domain that owns the UE context lifecycle, RRC procedure execution, and
mobility/handover. This document specifies, in a language-agnostic way:

- the UE context **data model** (Section 4),
- the UE **state machine** (Section 5),
- the **public API**, its semantics and error model (Section 6),
- the **concurrency model** and data structures (Sections 7–8),
- the **configuration parameters** (Section 9),
- the **invariants** and **ordering guarantees** (Section 10),
- the **conformance/parity contract** (Section 11).

### 1.1 In scope
A single, self-contained, stateful, concurrent service that manages many UE contexts,
executes lifecycle/signaling procedures on them, and supports concurrent lookup under load.

### 1.2 Out of scope
The full gNB, PHY/L2 processing, real 3GPP ASN.1 encoding, actual radio/network I/O,
persistence, and production operational concerns. Message payloads are abstract structs,
not wire-format PDUs.

---

## 2. Terminology

| Term | Meaning |
|------|---------|
| UE | User Equipment; one connected device, identified by a `ue_id`. |
| UE context | The per-UE state record owned by the service (Section 4). |
| UECM | The UE Context Management service as a whole. |
| Shard | A partition of the UE-id space owned by exactly one worker thread. |
| Worker | The single thread that owns and mutates one shard's contexts. |
| Request | A submitted operation message routed to a shard (Section 6/7). |
| Completion | The result handed back to the caller when a request finishes. |

---

## 3. Design principles (fairness constraints)

1. **Identical algorithms and data structures.** Same shard function, same intra-shard map
   with the same pinned hash, same state machine, same queue discipline.
2. **Identical concurrency model.** A shared-nothing, thread-per-shard model (Section 7).
   Mixing async runtimes with the thread model is **MUST NOT**.
3. **Identical build/runtime knobs where the toolchains allow.** Same allocator (jemalloc),
   comparable optimization level, same configuration parameters at runtime.
4. **No language-specific shortcuts** that change algorithmic behavior. Standard-library
   containers are used on both sides, but the key hash is pinned (Section 8) so container
   performance is not an accidental language advantage.
5. **Determinism of observable behavior.** Given the same sequence of requests to a shard,
   both implementations MUST produce identical completions and identical final state
   (Section 11).

---

## 4. Data model

### 4.1 Primary key
Each UE context is keyed by a **`ue_id`**: an unsigned 64-bit integer (`u64` / `uint64_t`).
`ue_id` is the abstract CU-level UE identifier; `0` is a reserved invalid value and
**MUST NOT** be used as a key.

### 4.2 UE context record
The UE context has exactly the following logical fields. Field widths are fixed so memory
footprint and copy cost are comparable across languages.

| Field | Type | Notes |
|-------|------|-------|
| `ue_id` | `u64` | Primary key; immutable after creation. |
| `state` | enum `UeState` (Section 5), stored as `u8` | Current lifecycle state. |
| `serving_cell_id` | `u32` | Current serving cell. |
| `rrc_transaction_id` | `u16` | Last RRC transaction id used. |
| `security_key` | fixed array of 32 `u8` | Dummy security context (models AS keys). |
| `drbs` | dynamic list of `DrbEntry` | 0..=`MAX_DRBS` established data radio bearers. |
| `messages_handled` | `u64` | Count of signaling messages applied to this context. |
| `last_activity_seq` | `u64` | Monotonic per-service sequence stamped on each op. |

`DrbEntry` is:

| Field | Type |
|-------|------|
| `drb_id` | `u8` |
| `qos_flow_id` | `u8` |
| `teid` | `u32` |

- `MAX_DRBS` = 8 (Section 9). Attempts to exceed it are an error (Section 6.4).
- `drbs` is a **dynamic** list (`std::vector` / `Vec`) on purpose, so the allocator study
  (RQ3) observes realistic per-context allocation. It is *not* a fixed array.

### 4.3 Creation parameters
`create_context` takes `CreateParams { serving_cell_id: u32, security_key: [u8;32] }`.
On creation, `state = Idle`, `drbs = empty`, counters `= 0`, `rrc_transaction_id = 0`.

### 4.4 Read-only view
`lookup` returns a **`UeContextView`**: an immutable copy/snapshot containing all fields of
Section 4.2 (with `drbs` copied by value). The service MUST NOT hand out an aliasing
reference into a shard's live state (this keeps the shared-nothing guarantee intact and
keeps the two implementations semantically identical).

---

## 5. UE state machine

### 5.1 States (`UeState`)
| Value | State | Meaning |
|------:|-------|---------|
| 0 | `Idle` | Context exists, no active RRC connection. Initial state after create. |
| 1 | `Connected` | RRC connection established; signaling/bearers allowed. |
| 2 | `Reconfiguring` | A reconfiguration/handover procedure is in progress. |
| 3 | `Released` | Terminal; context is being/has been torn down and removed. |

`Released` is transient-terminal: reaching it causes the context to be **removed** from the
shard in the same operation (there is no observable resting `Released` context).

### 5.2 Events → transitions
The only ways to change state are via API operations (Section 6). Allowed transitions:

| Event (API op) | From | To | Notes |
|----------------|------|----|-------|
| `create_context` | (none) | `Idle` | Fails if key exists. |
| `setup_connection` | `Idle` | `Connected` | RRC setup. |
| `handle_signaling` | `Connected` | `Connected` | Updates fields, no state change. |
| `add_drb` | `Connected` | `Connected` | Bearer setup. |
| `begin_reconfigure` | `Connected` | `Reconfiguring` | Start handover/reconfig. |
| `complete_reconfigure` | `Reconfiguring` | `Connected` | Success path. |
| `abort_reconfigure` | `Reconfiguring` | `Connected` | Failure path (state restored). |
| `release_context` | any (`Idle`/`Connected`/`Reconfiguring`) | `Released` → removed | Idempotent-ish: see 6.5. |

Any event applied from a state not listed above is an **`InvalidState`** error (Section 6.6)
and MUST NOT mutate the context.

### 5.3 State diagram

```
                 create_context
                 ───────────────▶ ( Idle )
                                     │  setup_connection
                                     ▼
   handle_signaling / add_drb   ( Connected ) ◀───── complete_reconfigure / abort_reconfigure
        (self-loop)  ────────────▶  │   ▲                        │
                                     │   └────────────────────────┘
                       begin_reconfigure│
                                     ▼
                              ( Reconfiguring )

   release_context (from Idle | Connected | Reconfiguring) ─▶ ( Released ) ─▶ removed
```

---

## 6. Public API

The service exposes the operations below. Signatures are given in language-neutral pseudo
syntax; each implementation exposes an equivalent typed API. Every mutating call is routed
to the owning shard and executed by that shard's worker (Section 7); the caller receives a
**completion** carrying an `OpResult`.

```
create_context(ue_id: u64, params: CreateParams)      -> OpResult<()>
setup_connection(ue_id: u64)                           -> OpResult<()>
handle_signaling(ue_id: u64, msg: SignalingMsg)        -> OpResult<SignalingAck>
add_drb(ue_id: u64, drb: DrbEntry)                     -> OpResult<()>
begin_reconfigure(ue_id: u64, params: ReconfigParams)  -> OpResult<()>
complete_reconfigure(ue_id: u64)                       -> OpResult<()>
abort_reconfigure(ue_id: u64)                          -> OpResult<()>
release_context(ue_id: u64)                            -> OpResult<()>
lookup(ue_id: u64)                                     -> OpResult<UeContextView>   // read-only
count()                                                -> u64                        // total live contexts
```

Where `SignalingMsg { kind: u8, payload_len: u16, payload: bytes<=64 }` and
`SignalingAck { accepted: bool, new_messages_handled: u64 }`.

### 6.1 Common semantics
- Every **mutating** operation that succeeds stamps `last_activity_seq` with the next value
  of a per-service monotonic counter (Section 10.3). Read-only operations (`lookup`,
  `count`) MUST NOT modify any context (they return the current stored value), keeping the
  lookup path read-only for the concurrent-lookup workload.
- On any error, the context MUST remain unchanged (no partial mutation).
- `ue_id == 0` MUST be rejected with `InvalidArgument` for all operations.

### 6.2 `create_context`
- Pre: `ue_id != 0`, key absent, shard has capacity (Section 9 `MAX_CONTEXTS_PER_SHARD`).
- Post: context created in `Idle`; returns `Ok(())`.
- Errors: `AlreadyExists` if key present; `CapacityExceeded` if shard is full;
  `InvalidArgument` if `ue_id==0`.

### 6.3 `setup_connection`
- Pre: context exists in `Idle`.
- Post: `state = Connected`.
- Errors: `NotFound`; `InvalidState` if not `Idle`.

### 6.4 `handle_signaling` / `add_drb`
- Pre: context exists in `Connected`.
- `handle_signaling`: increments `messages_handled`, returns `SignalingAck { accepted:true,
  new_messages_handled }`. `payload_len` MUST be `<= 64`; else `InvalidArgument`.
- `add_drb`: appends `drb` if `len(drbs) < MAX_DRBS` and no existing entry has the same
  `drb_id`; else `CapacityExceeded` / `AlreadyExists` respectively.
- Errors: `NotFound`; `InvalidState` if not `Connected`.

### 6.5 Reconfiguration and release
- `begin_reconfigure`: `Connected → Reconfiguring`. `complete_reconfigure` /
  `abort_reconfigure`: `Reconfiguring → Connected`. Errors `NotFound`, `InvalidState`.
- `release_context`: valid from `Idle`/`Connected`/`Reconfiguring`; removes the context and
  returns `Ok(())`. If the context does not exist, returns `NotFound` (NOT ok) so tests can
  distinguish double-release.

### 6.6 Error model (`OpError`)
Exactly this closed set, stored as `u8`:

| Value | Error | When |
|------:|-------|------|
| 0 | `NotFound` | Key absent for an op that requires it. |
| 1 | `AlreadyExists` | Duplicate create / duplicate `drb_id`. |
| 2 | `InvalidState` | Event not allowed from current state. |
| 3 | `CapacityExceeded` | Shard full or `drbs` full. |
| 4 | `InvalidArgument` | `ue_id==0`, oversized payload, etc. |

`OpResult<T>` is `Ok(T)` or `Err(OpError)`. Implementations MUST use their idiomatic result
type (Rust `Result`, C++ `std::expected`/`tl::expected` or an equivalent status+value); the
mapping is recorded in Section 12.

---

## 7. Concurrency model — shared-nothing, thread-per-shard

This is the **specified** concurrency model. It mirrors how real RAN L3 partitions UE state
and is the fairest structure for comparing the two languages' safe-concurrency stories.

1. The UE-id space is partitioned into `N_SHARDS` shards (Section 9).
2. Each shard is owned by **exactly one worker thread**. Only that worker reads or mutates
   the shard's contexts. → **No shared mutable state between workers; no locks on context
   data.** (This is what makes the safe-concurrency comparison meaningful.)
3. Callers (load-generator threads) interact with a shard only by **submitting request
   messages** to that shard's input queue; they never touch context state directly.
4. Each shard has one **bounded MPSC queue** of capacity `QUEUE_CAPACITY` (Section 9).
   Multiple producers (callers), single consumer (the worker).
5. **Backpressure:** if the target shard's queue is full, `submit` **blocks** until space is
   available (bounded, blocking). This produces realistic queueing latency under overload
   and is the mechanism the tail-latency study exercises. Non-blocking/drop policy is
   explicitly **not** used (would hide overload).
6. **Completion:** each request carries a single-use completion channel/handle. The worker
   writes the `OpResult` to it after executing the op; the caller waits on it. The
   completion mechanism MUST be a 1:1 handoff (e.g. a one-shot channel / promise-future),
   not a shared mutable buffer.
7. The worker processes its queue strictly **FIFO** (Section 10.2).

> Rationale note (for the thesis, not a requirement): this model lets Rust express the
> shard as data owned by its worker with no `unsafe` and no locks, and lets C++ do the same
> with a `std::thread` + queue; the interesting comparison is the *queue + completion*
> machinery and ownership transfer of requests, not lock contention.

### 7.1 Threading and lifecycle
- `start()` spawns `N_SHARDS` workers. `shutdown()` enqueues a `Stop` sentinel to each shard
  and joins all workers. After `shutdown()` no further submits are allowed.
- Worker count == shard count. Pinning is a benchmark concern (see `bench/`), not part of
  this API.

---

## 8. Data structures and pinned functions

### 8.1 Shard selection (MUST be identical on both sides)
`shard_index(ue_id)` uses the SplitMix64 finalizer to avoid skew for sequential ids, then
maps into `[0, N_SHARDS)`:

```
fn shard_index(ue_id: u64, n_shards: u64) -> u64:
    x = ue_id
    x = (x XOR (x >> 30)) * 0xBF58476D1CE4E5B9   // wrapping u64 multiply
    x = (x XOR (x >> 27)) * 0x94D049BB133111EB   // wrapping u64 multiply
    x =  x XOR (x >> 31)
    return x mod n_shards
```

All arithmetic is wrapping (modulo 2^64). Both implementations MUST reproduce identical
shard assignments for identical `ue_id`.

### 8.2 Intra-shard container (MUST be identical in behavior)
- Container: the language's standard hash map — C++ `std::unordered_map<u64, UeContext>`,
  Rust `std::collections::HashMap<u64, UeContext, S>`.
- **Pinned key hash:** to prevent the standard hashers from being an accidental
  language advantage/disadvantage, both maps MUST use the **FNV-1a 64-bit** hash over the
  8 little-endian bytes of `ue_id`:

```
fn fnv1a_64(key_bytes) -> u64:
    h = 0xcbf29ce484222325
    for b in key_bytes:            // 8 bytes of ue_id, little-endian
        h = (h XOR b) * 0x100000001b3   // wrapping u64 multiply
    return h
```

  In Rust this is a custom `BuildHasher`; in C++ a custom hash functor. Recorded in §12.
- Initial bucket capacity: `INITIAL_SHARD_CAPACITY` (Section 9), reserved at `start()`.

### 8.3 Request/response types
`Request` is a tagged union / enum over the operations of Section 6, each variant carrying
its arguments plus the completion handle. Implementations use their idiomatic sum type
(Rust `enum`, C++ `std::variant` or tagged struct); recorded in §12.

---

## 9. Configuration parameters

All are set at construction and fixed for a run. Defaults are the baseline; sweeps override
them from `bench/`.

| Parameter | Symbol | Default | Notes |
|-----------|--------|--------:|-------|
| Number of shards / workers | `N_SHARDS` | 8 | Also the worker-thread count. |
| Per-shard queue capacity | `QUEUE_CAPACITY` | 1024 | Bounded; blocking backpressure. |
| Max contexts per shard | `MAX_CONTEXTS_PER_SHARD` | 200000 | `CapacityExceeded` beyond. |
| Initial shard map capacity | `INITIAL_SHARD_CAPACITY` | 4096 | Reserved at start. |
| Max DRBs per context | `MAX_DRBS` | 8 | |
| Max signaling payload | — | 64 bytes | |

`N_SHARDS`, `QUEUE_CAPACITY`, and the active-UE population are the primary sweep knobs.

---

## 10. Invariants and ordering

### 10.1 Structural invariants (MUST always hold)
- I1: every live `ue_id` is stored in exactly one shard, namely `shard_index(ue_id)`.
- I2: a context's state is always one of `Idle`/`Connected`/`Reconfiguring` (never a resting
  `Released`).
- I3: a shard's contexts are only ever accessed by that shard's worker thread.
- I4: `0 <= len(drbs) <= MAX_DRBS`, and `drb_id`s within a context are unique.

### 10.2 Ordering guarantees
- O1 (intra-shard): requests submitted to the same shard are executed in FIFO order.
- O2 (cross-shard): no ordering guarantee across shards.
- O3: a completion is signaled exactly once per request.

### 10.3 The activity sequence counter
`last_activity_seq` is stamped from a per-service monotonically increasing counter. Because
increments happen inside shard workers across threads, the counter MUST be a single atomic
(`fetch_add`, relaxed ordering is sufficient). This is the *only* piece of shared mutable
state permitted, and it is write-only bookkeeping that does not affect control flow. Its
presence and exact semantics are identical on both sides.

---

## 11. Conformance / parity contract

Both implementations MUST pass the same **conformance suite** (to live in `spec/conformance/`
as language-neutral test vectors). A test vector is a sequence of operations with expected
results and an expected post-state summary.

### 11.1 What MUST match exactly
1. The `OpResult` (Ok/Err and error code) of **every** operation in a sequence.
2. The final `count()` and, for each surviving `ue_id`, the `UeContextView` field values
   **except** `last_activity_seq` (see 11.2).
3. Shard assignment for every `ue_id` (Section 8.1).

### 11.2 What MAY differ
- Absolute `last_activity_seq` values and their cross-shard interleaving are timing-dependent
  and are **excluded** from parity comparison. (Per-context monotonic *ordering* of stamps
  applied by the same shard MUST still hold.)
- Wall-clock timing, memory addresses, iteration order of the map.

### 11.3 Test-vector format (draft)
```
# each line: OP arg1 arg2 ... => EXPECTED
create 1001 cell=7 => Ok
setup 1001          => Ok
signal 1001 kind=3 len=10 => Ok(accepted=true)
setup 1001          => Err(InvalidState)
lookup 1001         => Ok(state=Connected, drbs=0, messages_handled=1)
release 1001        => Ok
release 1001        => Err(NotFound)
count               => 0
```
A shared runner feeds vectors to each implementation and diffs actual vs expected.

**Status (2026-07):** implemented. Vectors live in `spec/conformance/vectors/*.vec`; the exact
grammar is in `spec/conformance/README.md`. Each language ships a `conformance_runner`
(`cpp/tools/conformance_runner.cpp`, `rust/src/bin/conformance_runner.rs`) that executes a vector
against the threaded `Service` and emits a canonical transcript. `spec/conformance/run.sh` runs
every vector through both runners, checks each against the expected results, **and** diffs the C++
vs. Rust transcripts so op-for-op agreement (§11.1) is enforced. Seeded suite: `basic.vec` (the
§11.3 example + full error model + DRB fill/overflow + reconfigure begin/complete/abort) and
`shards.vec` (shard-assignment parity, §11.1.3). Both implementations currently pass and agree.

---

## 12. Recorded deviations (forced-idiom log)

Any spot where the two languages MUST diverge to satisfy the same requirement is logged here
during implementation, with the requirement id and the reason. Examples that will land here:

- Result type: Rust `Result<T, OpError>` vs C++ `std::expected<T, OpError>` (or fallback).
- Sum types: Rust `enum` vs C++ `std::variant`/tagged struct for `Request`.
- Custom hashing hookup: Rust `BuildHasher` vs C++ hash functor.
- One-shot completion: Rust `oneshot`/`mpsc` vs C++ `std::promise`/`std::future` or a
  condition-variable handoff.
- Any `unsafe` block in Rust (location + justification) — expected to be **none** in the
  baseline implementation.

**C++ implementation (recorded 2026-07, `cpp/`):**
- Result type: `OpResult<T> = std::expected<T, OpError>` (C++23). No fallback needed
  (g++ 13.3 supports `std::expected`).
- Request: a tagged struct (`OpKind` + argument fields) rather than a `std::variant`, to keep
  a stable move-only type carrying a `std::promise` completion (`include/uecm/message.hpp`).
- Response: `std::variant<OpResult<void>, OpResult<SignalingAck>, OpResult<UeContextView>,
  OpResult<uint64_t>>`.
- One-shot completion: `std::promise` / `std::future` (§7.6); caller blocks on `future.get()`.
- Bounded blocking queue: hand-written `mutex` + two `condition_variable`s
  (`include/uecm/bounded_queue.hpp`).
- Intra-shard map: `std::unordered_map<UeId, UeContext, FnvHash>` with the pinned FNV-1a hash.
- `unsafe`-equivalent: none (no manual memory management beyond STL containers).
- Verified data-race free under ThreadSanitizer.

**Rust implementation (recorded 2026-07, `rust/`):**
- Result type: `OpResult<T> = Result<T, OpError>` (idiomatic; no wrapper needed).
- Request: a `Request` enum with one variant per operation, each carrying a typed one-shot
  `Sender` of its precise result type (`src/message.rs`) — replaces the C++ `std::variant`
  `Response`; no runtime variant dispatch on the caller side.
- One-shot completion: a fresh `std::sync::mpsc::channel()` per request; caller blocks on
  `recv()` (the analog of `std::future::get`).
- Bounded blocking queue: `std::sync::mpsc::sync_channel(capacity)` (blocking `send` gives
  the same backpressure as the C++ hand-written queue).
- Intra-shard map: `std::collections::HashMap<UeId, UeContext, FnvBuildHasher>`, where
  `FnvBuildHasher` hashes the key as 8 little-endian bytes so the digest is bit-identical to
  the pinned FNV-1a (verified by a test against `fnv1a_64`).
- `unsafe`: none (`#![forbid]`-clean; verified by grep). Safe Rust guarantees data-race
  freedom at compile time via `Send`/`Sync`, so no runtime sanitizer is required (stronger than
  the C++ TSan check). Miri (UB/data-race interpreter) can be run as an optional extra once a
  nightly toolchain is available.
- Optimisation parity: `[profile.release] opt-level = 2` pinned in `Cargo.toml` to match the
  C++ `-O2` build (§3).

---

## 13. Freeze checklist

- [ ] Supervisor review of data model, state machine, and API.
- [ ] Confirm concurrency model (thread-per-shard + bounded blocking queue) is acceptable.
- [ ] Confirm default parameters and sweep ranges with the evaluation plan.
- [x] Confirm the conformance-vector format and seed an initial suite. *(Format + `basic.vec`/`shards.vec` seeded; shared runner passes for both implementations. Supervisor sign-off on the format still pending.)*
- [ ] On approval: set Version 1.0, tag `spec-v1.0`, and treat changes as versioned amendments.

---

## Appendix A — Open decisions to confirm

1. **Reconfiguration richness.** The state machine includes a `Reconfiguring` state with
   begin/complete/abort. If the supervisor prefers a leaner model, `Reconfiguring` can be
   dropped, leaving `Idle`/`Connected` only. (Kept for now because handover is central to
   UE context management and gives the workload a non-trivial procedure.)
2. **Queue policy under overload.** Currently *bounded + blocking* (backpressure). The
   alternative (bounded + reject with `CapacityExceeded`) would measure loss instead of
   latency growth. Blocking is chosen to make tail latency the observable.
3. **`std::expected` availability.** Requires C++23; if the pinned compiler lacks it, fall
   back to a small hand-rolled `Expected`/status type (recorded in §12).
4. **DRB list dynamic vs fixed.** Chosen dynamic to exercise the allocator for RQ3; can be
   switched to a fixed inline array if allocator noise is undesirable.
