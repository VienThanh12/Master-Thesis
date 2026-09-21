# Shared Specification: UE Context Management Service

**Version:** 1.0
**Status:** Frozen. Supervisor review is complete. Tag: `spec-v1.0`. Changes after this version are versioned amendments.
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

The subsystem under study is a **UE Context Management (UECM) service**. It keeps
per-device state, as a gNB-CU-CP does, and covers the UE-context lifecycle, RRC procedure
execution, and mobility/handover. This document specifies, in a language-agnostic way:

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
| `serving_cell_id` | `u32` | Current serving cell. Also written by `begin_reconfigure` (§6.5). |
| `rrc_transaction_id` | `u16` | **Reserved, inert.** No operation in §6 writes it; it is `0` for the life of the context. |
| `security_key` | fixed array of 32 `u8` | Dummy security context (models AS keys). Written once at creation, never inspected. |
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
- Of a `DrbEntry`, only `drb_id` carries semantics (the uniqueness check of §6.4).
  `qos_flow_id` and `teid` are stored verbatim and never inspected; they exist to give the
  entry a realistic width.

**Inert fields.** `rrc_transaction_id`, `security_key`, `qos_flow_id` and `teid` are carried
but never read by any operation. They are part of the record so that its size and copy cost
model a real UE context, and they are named here as inert so that a third implementation
cannot conform while giving them behaviour. The per-language `invariants` suites check that
they round-trip through `lookup` unchanged (§11).

### 4.3 Operation parameters
`create_context` takes `CreateParams { serving_cell_id: u32, security_key: [u8;32] }`.
On creation, `state = Idle`, `drbs = empty`, counters `= 0`, `rrc_transaction_id = 0`.

`begin_reconfigure` takes `ReconfigParams { target_cell_id: u32 }`. It is applied
immediately — `serving_cell_id` becomes `target_cell_id` when the procedure *begins*, not
when it completes — and it is **not** rolled back by `abort_reconfigure` (§5.2, §6.5). The
consequence is observable through `lookup` and therefore part of parity (§11.1).

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
| `begin_reconfigure` | `Connected` | `Reconfiguring` | Start handover/reconfig; also sets `serving_cell_id = target_cell_id` (§4.3). |
| `complete_reconfigure` | `Reconfiguring` | `Connected` | Success path. |
| `abort_reconfigure` | `Reconfiguring` | `Connected` | Failure path. Restores `state` **only**: the serving cell is not rolled back (§6.5). |
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
  of a per-service monotonic counter (Section 10.3). `release_context` is the one exception:
  it removes the record, so there is nothing to stamp, and it MUST NOT consume a counter
  value. Read-only operations (`lookup`, `count`) MUST NOT modify any context (they return
  the current stored value), so the read path never mutates shard state.
- On any error, the context MUST remain unchanged (no partial mutation), and a failed
  operation MUST NOT consume a counter value.
- `ue_id == 0` MUST be rejected with `InvalidArgument` by all nine operations that take one
  (`count` takes no `ue_id`).

> **What "read-only" does and does not buy.** `lookup` is non-mutating, but it is still
> routed to the owning shard's worker and executed from the same FIFO queue as the mutating
> operations (§7). There is no shared-read fast path: read concurrency is `N_SHARDS`-way
> across shards, and *within* a shard a lookup queues behind whatever precedes it and pays
> the full request handoff. This is a consequence of the shared-nothing model, not an
> oversight, and it is why the end-to-end latency of any operation is dominated by the
> handoff rather than by the operation.

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
  new_messages_handled }`. `payload_len` MUST be `<= 64`; else `InvalidArgument`. `kind` and
  `payload` are **opaque**: the service MUST NOT branch on either, and `accepted` is
  therefore always `true` on the success path. (The payload is carried so that the request's
  copy cost is realistic, not so that it can be interpreted.)
- `add_drb`: appends `drb` if `len(drbs) < MAX_DRBS` and no existing entry has the same
  `drb_id`; else `CapacityExceeded` / `AlreadyExists` respectively. Only `drb_id` is
  inspected (§4.2).
- Errors: `NotFound`; `InvalidState` if not `Connected`.

### 6.5 Reconfiguration and release
- `begin_reconfigure`: `Connected → Reconfiguring`, and sets
  `serving_cell_id = params.target_cell_id` in the same operation.
- `complete_reconfigure` / `abort_reconfigure`: `Reconfiguring → Connected`. Neither touches
  `serving_cell_id`, so an **aborted** reconfiguration leaves the context reporting the cell
  it failed to move to. This is a deliberate simplification — the record carries no saved
  pre-handover cell to roll back to — and it is pinned by `states.vec` so it cannot drift.
- Errors for all three: `NotFound`, `InvalidState`.
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

### 6.7 `count`

`count()` returns `u64` and cannot fail: it takes no `ue_id`, so none of the §6.6 codes
applies. An implementation MAY carry it in its result type internally for uniformity with the
other operations; that is a representation choice, recorded in §12, and MUST NOT introduce an
error case.

Because the population is partitioned, `count()` is computed by routing one request to **each**
shard and summing the replies (§7). It is therefore **not a snapshot**: with mutations in
flight the shards are read at different instants and the sum need not equal the population at
any single instant. It is exact when the service is quiescent, which is the only condition
under which §11.1 compares it. Implementations MUST NOT add cross-shard synchronisation to
make it atomic — that would introduce shared state the concurrency model forbids (§7.2).

---

## 7. Concurrency model: shared-nothing, thread-per-shard

This is the **specified** concurrency model. It is a fairness control for the language
comparison, not a copy of a production gNB-CU-CP runtime, and it is the fairest structure
for comparing the two languages' safe-concurrency stories.

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
  and joins all workers. Both are idempotent.
- Worker count == shard count. Pinning is a benchmark concern (see `bench/`), not part of
  this API.

**Lifecycle precondition (normative).** Every operation of §6 requires the service to be
running: `start()` called, `shutdown()` not yet called. A call outside that window is a
**caller error, not a runtime condition** — it MUST NOT be reported through `OpError`, which
stays the closed five-value set of §6.6.

An implementation MUST detect the violation and fail deterministically: it MUST NOT route the
request, and MUST NOT read shard state that does not exist. The idiomatic mechanism differs
per language and is recorded in §12 (C++ throws `std::logic_error`; Rust panics). What both
MUST provide is that the failure is immediate, diagnosable, and free of undefined behaviour.

> Why this is spelled out. Until 2026-08 this section said only that submits after
> `shutdown()` were "not allowed", and neither implementation checked. The prohibition was on
> the caller with no mechanism behind it, which is exactly the shape of requirement that the
> two languages do *not* fail equivalently: in C++ the unchecked path indexed a cleared
> container, giving a heap-use-after-free after `shutdown()` and a segmentation fault before
> `start()`, while the same misuse in Rust was already a bounds-check panic. The defect was in
> code written to be correct, reachable through the public API, and invisible to the whole
> parity suite, which never calls an operation outside the window. See §12 and the RQ2
> discussion.

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
- Container: the language's standard hash map: C++ `std::unordered_map<u64, UeContext>`,
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
| Max signaling payload | n/a | 64 bytes | |

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
vs. Rust transcripts so op-for-op agreement (§11.1) is enforced.

Suite as of 2026-08 (223 checked operations across seven vectors; both implementations pass all of
them and produce byte-identical transcripts): `basic.vec` (the §11.3 example + error model + DRB
fill/overflow + reconfigure begin/complete/abort), `states.vec` (the full §5.2 transition matrix
plus the §6.1 no-mutation-on-error rule), `errors.vec` (every §6.6 code on every operation that can
raise it, `ue_id == 0` on all nine operations that take one, the payload boundary, and the precedence between
competing errors), `capacity.vec` (`CapacityExceeded` on `create`, and that §9's limit is per shard
rather than service-wide), `routing.vec` (§10.1 I1: state stays private to its own shard),
`shards.vec` and `shards13.vec` (shard assignment for a power-of-two and a non-power-of-two shard
count; the latter is what distinguishes the specified modulo from a bitmask). Per-vector detail is
in `spec/conformance/README.md`.

Properties a sequential transcript cannot express are covered by mirrored per-language suites
rather than by vectors: the §7 queue and completion machinery, FIFO execution (§10.2 O1), the
fields `lookup` does not print (`security_key`, `rrc_transaction_id`, per-DRB contents), and the
activity-sequence discipline of §10.3/§11.2. See `cpp/tests/test_{invariants,concurrency}.cpp` and
`rust/tests/{invariants,concurrency}.rs`.

One consequence worth recording for §11.1: the vectors pin four decisions that §6 originally
left open, because it gave each operation's errors as a *set* rather than an order. Three are
error-precedence choices — argument validation before key lookup, and capacity before duplicate
detection, both for `create` and for `add_drb`. The fourth is not about errors at all:
`abort_reconfigure` restores `state` but not `serving_cell_id` (§6.5), which is observable
through `lookup` and so is a parity commitment like any other. Both implementations already
agreed on all four, so nothing had to change; the vectors exist so the agreement cannot regress
unnoticed, and §4.3/§6.5 now state the fourth normatively rather than leaving it to be inferred
from the vector. The independent reference model in `spec/conformance/model.py` documents the
same four as the points where a third reader could reasonably have diverged.

### 11.4 Independent oracle and generated vectors (added 2026-08)

The suite above establishes that each implementation reproduces the expectations written into a
vector, and that the two transcripts are byte-identical. Neither distinguishes *both correct*
from *both wrong in the same way*, which is the failure mode a shared specification and a single
author make most likely, and the 223 expectations were derived from this document by the same
person who wrote both implementations.

`spec/conformance/model.py` is therefore a **third implementation of this specification**, in
Python, sharing no code with `cpp/` or `rust/`. It is validated before it is trusted: known-answer
tests for the §8.1 and §8.2 functions, then a replay of all seven hand-written vectors, which it
reproduces exactly. `spec/conformance/genvec.py` then generates randomised operation sequences
under five profiles with every expected result computed by the model, and `run.sh` runs them
through both runners. Generation is deterministic (a hand-written SplitMix64, not a library PRNG),
so a failing seed is a permanently reproducible regression test.

**Status:** roughly 793 000 generated operations across the five profiles, with no divergence
between the two implementations and the model.

The model also records, in its own header, the four places where this document under-determines
behaviour and an independent reader could reasonably have written something else: the three
error precedences named above, plus `abort_reconfigure` restoring `state` but not
`serving_cell_id`. §5.2 calls the abort path "state restored", which reads as though the cell
should roll back too; it does not, in either implementation, and `states.vec` pins that. The
v1.0 freeze keeps that wording: abort restores `state` only, as the table in §5.2 and the
notes in §4.3/§6.5 already state. Later amendments are versioned.

### 11.5 Dynamic analysis and coverage (added 2026-08)

Three checks bound the suite from directions a transcript cannot reach.

- **Sanitisers (C++).** `cpp/sanitise.sh` builds the whole tree under ASan+UBSan, TSan, and
  UBSan alone, and runs every test binary and every conformance vector under each. All clean.
  This matters for the fairness baseline of §3: safe Rust carries data-race and memory-safety
  freedom by construction, so without this the C++ arm's equivalent property would rest on not
  having failed yet. Results in `cpp/results/sanitisers.md`.
- **Miri (Rust).** `rust/miri.sh` runs the state-machine and invariant suites under Miri with
  strict provenance. No undefined behaviour. This confirms rather than discovers — the core has
  no `unsafe` (§12) — and exists so the two arms are checked by the strongest dynamic tool each
  language offers. Results in `rust/results/miri.md`.
- **Coverage.** A negative result from a sanitiser is only as broad as the code that ran, so the
  suite's reach is measured: 94.6% of C++ library lines (`cpp/coverage.sh`, gcov) and 98.2% of
  Rust library lines (`rust/coverage.sh`, llvm-cov), with `ShardCore` and `Service` fully covered
  on both sides. The two figures are **not comparable with each other** — different tools
  counting different things over implementations with no line-for-line correspondence — but each
  bounds the claims made about its own side.

---

## 12. Recorded deviations (forced-idiom log)

Any spot where the two languages MUST diverge to satisfy the same requirement is logged here
during implementation, with the requirement id and the reason. Examples that will land here:

- Result type: Rust `Result<T, OpError>` vs C++ `std::expected<T, OpError>` (or fallback).
- Sum types: Rust `enum` vs C++ `std::variant`/tagged struct for `Request`.
- Custom hashing hookup: Rust `BuildHasher` vs C++ hash functor.
- One-shot completion: Rust `oneshot`/`mpsc` vs C++ `std::promise`/`std::future` or a
  condition-variable handoff.
- Any `unsafe` block in Rust (location + justification): expected to be **none** in the
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
- `count()`: the worker replies with `OpResult<std::uint64_t>` so that every `Response`
  alternative is an `OpResult`, and `Service::count()` unwraps it. §6.7 specifies a bare
  `u64`; this is representation only and no error case is reachable. Rust needs no wrapper
  and sends `u64` directly.
- Lifecycle precondition (§7.1): `submit()` and `count()` check the `running_` flag and throw
  `std::logic_error`. This costs one predictable branch on the submit path, which the Rust arm
  already paid as a slice bounds check, so the check narrows a small pre-existing asymmetry
  rather than creating one.
- `unsafe`-equivalent: none (no manual memory management beyond STL containers).
- Verified data-race free under ThreadSanitizer.

**Rust implementation (recorded 2026-07, `rust/`):**
- Result type: `OpResult<T> = Result<T, OpError>` (idiomatic; no wrapper needed).
- Request: a `Request` enum with one variant per operation, each carrying a typed one-shot
  `Sender` of its precise result type (`src/message.rs`), replaces the C++ `std::variant`
  `Response`; no runtime variant dispatch on the caller side.
- One-shot completion: a fresh `std::sync::mpsc::channel()` per request; caller blocks on
  `recv()` (the analog of `std::future::get`).
- Bounded blocking queue: `std::sync::mpsc::sync_channel(capacity)` (blocking `send` gives
  the same backpressure as the C++ hand-written queue). At `capacity == 0` this is a
  rendezvous channel. C++ `BoundedQueue` clamps 0 to 1. The compared campaign uses 1024.
  See the 2026-09-16 recording below.
- Lifecycle precondition (§7.1): `shard_tx()` and `count()` assert `running`. Before the
  assertion existed the violation was already a panic — the slice index into a cleared `shards`
  vector — so the change makes the diagnostic explicit rather than changing the outcome. The
  C++ analogue is a thrown `std::logic_error`; `panic!` and `throw` are the matched idioms
  here, both unwinding and both deterministic.
- Intra-shard map: `std::collections::HashMap<UeId, UeContext, FnvBuildHasher>`, where
  `FnvBuildHasher` hashes the key as 8 little-endian bytes so the digest is bit-identical to
  the pinned FNV-1a (verified by a test against `fnv1a_64`).
- `unsafe`: none in `rust/src` (verified by grep). The crate does not currently carry
  `#![forbid(unsafe_code)]`, so a later `unsafe` block would compile until that attribute is
  added. Safe Rust guarantees data-race freedom at compile time via `Send`/`Sync`, so no
  runtime sanitizer is required (stronger than the C++ TSan check). Miri has since been run
  as well (`rust/miri.sh`, §11.5): clean, which confirms the property rather than discovering
  it, and keeps the two arms symmetrically evidenced.
- Dependency-freedom is preserved deliberately. The Loom and Shuttle models of the RQ2 boundary
  classes live in a **separate crate**, `faults/rust-model-checking/`, rather than as
  dev-dependencies of `rust/`: the dependency-free core is load-bearing for the RQ4 supply-chain
  argument and should not be weakened for models that never touch the library.
- Optimisation parity: `[profile.release] opt-level = 2` pinned in `Cargo.toml` to match the
  C++ `-O2` build (§3).

**Attribution probes (recorded 2026-08, not compared configurations):**

These builds exist to test an attribution, not to be reported. The compared pair keeps
each language's standard containers, because the study compares the languages as a
developer actually finds them; a probe holds the language fixed and changes one
container, so that a measured difference can be assigned to the container or not.

- **C++ open-addressed intra-shard map** (`-DUECM_FLAT_MAP=ON`,
  `cpp/include/uecm/flat_map.hpp`). Same pinned FNV-1a hash, power-of-two capacity,
  7/8 load factor and linear probing, so the analogue is to Rust's `hashbrown` rather
  than to open addressing in general. Passes all five C++ test binaries and keeps
  byte-for-byte transcript parity with Rust on all seven conformance vectors, which is
  expected by construction since no `ShardCore` operation iterates the map.

  **Result (10 interleaved repeats, WSL2 development host, indicative only):** median
  core-operation cost 16.4 ns for `std::unordered_map`, 15.3 ns for the open-addressed
  probe, 8.9 ns for Rust. The swap closes roughly **15%** of the C++-to-Rust gap, which
  falls from 1.84x to 1.72x.

  This does not support the explanation currently given for the core-operation result.
  Node-based layout is a real cost and it is in the measured direction, but on this
  evidence it is a minority of the difference rather than the cause of it. Two things
  bound the reading: the probe uses plain linear probing where `hashbrown` probes
  sixteen slots at a time with SIMD, so a production flat map would likely close more;
  and this is an unpaired informal run on the development laptop, not the measurement
  host. The proper version runs through `bench/latency_budget.sh` with its interleaved
  repeats and paired test. Until then the thesis should not lean on the node-based
  account, and cache-miss counters are no longer the only way to test it.

- **Rust mutex-and-condvar shard queue** (`--features mutex-queue`,
  `rust/src/mutex_queue.rs`). Replaces `std::sync::mpsc::sync_channel` with the design
  the C++ arm uses: one mutex, a `VecDeque`, and separate not-full and not-empty
  condition variables. Introduces no `unsafe` — the auto traits already hold, because
  every mutable field sits behind the mutex — so the core's safety story is unchanged.
  Passes all 16 Rust tests including the capacity-1 blocking-backpressure case, is
  clippy-clean, and keeps transcript parity with C++ on all seven vectors.

  **Result (5 interleaved repeats at the overload rate, WSL2, indicative only):**
  sustained throughput 43.5 kops/s for C++, 30.8 for Rust on the standard channel, and
  30.4 for Rust on the probe queue. Matching the queue design closes **none** of the
  divergence; the ratio moves from 1.41x to 1.43x, which is noise in the wrong
  direction.

  What this probe alone does *not* establish is that the queue is exonerated, and the
  first version of this entry claimed it did. The probe matched the C++ arm's
  *synchronisation* — one mutex, two condition variables, the same predicates — but not
  its *buffer*. `BoundedQueue` stores elements in a `std::queue`, which is deque-backed,
  and a `VecDeque` is not: it grows by doubling and never shrinks, so after warm-up the
  probe allocates nothing where the C++ arm allocates continuously. Ruling the
  synchronisation out therefore left the allocation untested. The next entry tests it.

- **C++ preallocated ring inside the shard queue** (`-DUECM_RING_QUEUE=ON`,
  `cpp/include/uecm/ring_queue.hpp`). Replaces the `std::queue` inside `BoundedQueue`
  with a fixed-capacity ring exposing the same five members, so the locking, the
  predicates and the notify discipline are byte-identical and only the storage changes.
  Passes all six C++ test binaries and keeps byte-for-byte transcript parity with Rust
  on all seven vectors.

  The mechanism it removes is measurable directly, and was verified before the
  throughput run rather than assumed: with global `operator new`/`delete` counted around
  3000 pushes and 3000 pops of a real `Request`, the deque-backed queue performs **1008
  allocations** — libstdc++ sizes a deque node at 512 bytes and a `Request` is 160, so
  three fit per node and a node is allocated on every third push and freed on every third
  pop, inside the queue mutex. The ring performs **zero**.

  **Result (7 interleaved repeats at the overload rate, WSL2, indicative only):**
  sustained throughput 43.2 kops/s deque-backed, 43.1 ring-backed, 30.0 for Rust.
  Removing the allocation entirely changes the C++ arm by **-0.2%**, far inside the
  run-to-run spread, and moves the ratio from 1.44x to 1.43x.

  **The queue is now exonerated on both counts**, which the earlier probe could only
  half-establish: neither its synchronisation design nor its hot-path allocation
  reproduces the ordering, and the contended-primitive microbenchmark had already shown
  the primitives alone do not. Note that the microbenchmark shares the second blind spot
  — its job is 32 bytes, so sixteen fit per deque node and it allocates at a fifth of the
  service's rate — so it too was weaker evidence than it looked; the ring probe is what
  closes the question. At the time this was written that left one untested *service-side* entry: the
  tagged-struct dispatch and the 160-byte request the C++ side moves through the
  queue against Rust's 96. That candidate has the wrong sign for a gap in which
  C++ completes more work, and the 18 September probes below test the open-loop
  instrument instead. Host caveat as above — 14 logical CPUs here against 16
  vCPUs on the measurement guest, so the absolute ratio is smaller (1.4x here,
  `\OverloadThrRatio` there) — but both probes are within-host comparisons of
  two builds of the same language, which is what they need to be.

**All three probes returned negative, which is the finding.** The two mechanisms the
thesis offers for its two most notable performance results are, when tested by
substitution rather than argued from structure, largely unsupported: the container
accounts for a minority of the core-operation gap, and the queue for none of the overload
divergence — neither its design nor the allocation it performs. Neither result is
overturned — the differences are real and reproduce — but their stated causes need
revising, and all three were testable without the hardware counters the text names as the
only route.

Worth recording as a methodological lesson, because it caught two of the three probes: a
substitution probe has to substitute *everything* the candidate mechanism covers. The
Rust queue probe matched a design and not an allocation pattern; the contended-primitive
microbenchmark isolated primitives but shrank the allocation rate fivefold by using a
smaller job. Each looked like a controlled experiment and each silently varied a second
thing along with the first.

**Overload instrument probes (recorded 2026-09-18, not compared configurations):**

These do not swap a container. They ask whether the published floor is the service
or the open-loop harness: the capped coordinated-omission backfill, and the
unbounded per-request completion channel. The compared pair is untouched.
Runner: `bench/overload_probes.sh`. System allocator, mixed workload, 7 shards
and 7 producers, interleaved inside each repeat. `--correction-cap` defaults to
10 000 so a campaign binary without the flag is the reported instrument.
`--features sync-oneshot` is probe-only.

- **P0 Closed loop.** Same service, no `--rate`, so the producer never sleeps
  on a schedule and the 10 000-sample backfill never runs. Throughput is
  `ops_total / measured_wall_s` under `--max-run-s`.
- **P1 Open loop, `--correction-cap 0`.** The send schedule stays. The real
  sample is still recorded. Only the synthetic backfill is dropped. Throughput
  is the row that must be compared. Collapsed p50 will stay large, because the
  intended send time is still the origin.
- **P2 Rust `sync_channel(1)` completions** (`--features sync-oneshot`). Array
  flavour, one slot, still a 1:1 blocking completion, no `unsafe`. The shard
  queue stays on `sync_channel(1024)`. C++ is unchanged.
- **P3 Other clocks.** `--latency-origin start` records the call from the
  instant the producer actually sent, with no fill. `--correction-when after`
  keeps the intended origin and the 10 000-sample cap, but the fill runs
  after the timed window. Throughput should then match P1 cap 0. Service-time
  p50 is the language comparison of the call.

**Result (8 interleaved repeats, WSL2 development host, 2 s measured,
140 kops/s offered on P1/P2, indicative only).** Log:
`bench/results/overload_probes-20260918-134345.jsonl`. The script refused to
certify every phase: every arm's throughput varied by more than 5% across
repeats (P0 12%, P1 default-cap 6–9%, P1 cap-0 20%, P2 6–8%). A median of a
spread that wide is a location of a cluster, not a measurement. Direction,
from the ranges:

- P0: C++ 67–100 kops/s, Rust 67–103. Complete overlap. Closed-loop max is
  not a language split on this host. CPU clusters ~436% (C++) and ~461%
  (Rust).
- P1, default 10 000-sample cap (the campaign instrument): C++ 47–62 kops/s,
  Rust 37–45. The ranges do not overlap. C++ completes more. Rust draws more
  CPU (cluster ~538% against ~486%). Same signature as the overload table.
- P1, cap 0: C++ 42–94 kops/s, Rust 42–96. Both recover toward the closed-loop
  band. Each has one low outlier near 42 kops/s. CPU recedes to the
  closed-loop cluster (~437% / ~457%). The default-cap C++ advantage is no
  longer visible. Collapsed p50 stays on the order of a second, as expected:
  the producer is still late relative to the intended schedule. The work
  that moved is the histogram backfill, not service time.
- P2: standard Rust 37–46 kops/s, `sync_channel(1)` 40–46, C++ 51–65. The
  oneshot swap does not move the floor.

Host caveat as for the 2026-08 probes. The tagged-struct / request-size
entry (D1) remains unrun and still has the wrong sign. **Do not copy these
WSL2 kops/s into `figures/gen_macros.tex` or the thesis.**

**Result (10 interleaved repeats, certified, Cherry Chicago AMD EPYC 7443P,
19 September 2026).** Same runner, mixed, 7/7, system allocator, 3 s
measured, 784 kops/s offered on P1/P2, pinned to cores 2–17 after SMT off.
Host kernel Ubuntu 24.04.4, `virtualisation: none`, no `isolcpus`, no
`nohz_full`. Toolchain is the Rocky image (`g++` 15.2.1, `rustc` 1.97.1).
512 GB RAM. Log: `bench/results/overload_probes-20260919-153013.jsonl`.
The script certified every phase (spread under 5% on every arm). This is
not the Nokia/UH 7443 of `campaign-20260827-151927`. It is the same CPU
SKU as the 26 August confirmation host (`7443P`), a different machine.

- P0 closed loop: C++ 455 kops/s `[454, 458]`, Rust 487 kops/s `[485, 488]`.
  C++/Rust 0.94×, paired *p* = 1.95×10⁻³. Closed-loop max is not a C++ win.
  CPU ~573% / ~592%.
- P1, default 10 000-sample cap: C++ 138 kops/s `[136, 138]`, Rust 83 kops/s
  `[81, 84]`. C++/Rust **1.67×**, paired *p* = 1.95×10⁻³. Same ordering and
  nearly the same ratio as `\OverloadThrRatio` on the reported campaign
  (147 / 84). Rust draws more CPU (~650% against ~632%) while completing
  less. Same signature as `tab:overload`.
- P1, cap 0: C++ 446 kops/s `[440, 451]`, Rust 467 kops/s `[463, 470]`.
  C++/Rust **0.95×**. Both recover to the closed-loop band. CPU recedes to
  ~569% / ~585%. The default-cap C++ advantage is gone.
- P2: standard Rust 83 kops/s, `sync_channel(1)` 83 kops/s, C++ 138.
  The oneshot swap does not move the floor.

**Do not copy these kops/s into `figures/gen_macros.tex`.** They are not
the compared pair. They license a *cause* sentence: under this open-loop
instrument the published floor gap is the 10 000-sample coordinated-omission
backfill, not the languages' closed-loop maximum and not the completion
channel. D1 (request size) is not the mechanism of a gap that disappears
when the cap is 0.

**Result (4 interleaved repeats, WSL2 development host, 2 s measured,
140 kops/s offered, P3, 20 September 2026, indicative only).** Log:
`bench/results/overload_probes-20260920-132221.jsonl`. Spread under 5%.
Not the measurement host. Do not copy kops/s into `figures/gen_macros.tex`.

- `--latency-origin start`: C++ 108 kops/s `[108, 109]`, Rust 111 kops/s
  `[110, 112]`. C++/Rust **0.97×**. Service-time p50 C++ 63 µs, Rust 59 µs.
  The call is not slower in Rust.
- `--correction-when after`: C++ 108 kops/s `[108, 109]`, Rust 109 kops/s
  `[108, 109]`. C++/Rust **0.99×**. Intended-origin p50 stays hundreds of
  milliseconds (schedule drift). Throughput sits with P1 cap 0, not with
  the campaign fill.

**Result (10 interleaved repeats, certified, Cherry Chicago AMD EPYC 7443P,
20 September 2026, P3).** Same packing as the 19 September P0–P2 run: mixed,
7/7, system allocator, 3 s measured, 784 kops/s offered, `--pin 2-17` after
SMT off. Host `calm-husky` (Ubuntu 24.04.4, kernel 6.17.0-23-generic,
`virtualisation: none`, no `isolcpus`, no `nohz_full`, ~512 GB RAM). Not
the 19 September box (`exciting-moose`) and not the Nokia/UH 7443. Same
CPU SKU. Rocky image (`g++` 15.2.1, `rustc` 1.97.1). Log:
`bench/results/overload_probes-20260920-183540.jsonl`. Env:
`bench/results/env-20260920-183531.txt`. The script certified every arm
(spread 1.1–2.9%).

- `--latency-origin start` (no fill): C++ 448 kops/s `[440, 453]`, Rust 471
  kops/s `[463, 475]`. C++/Rust **0.95×**, paired *p* = 3.91×10⁻³. Service-time
  p50 C++ 15.7 µs `[15.7, 15.8]`, Rust 15.2 µs `[15.2, 15.3]`. CPU ~568% /
  ~590%. Throughput sits with P0 / P1 cap 0, not with the campaign floor.
  The call is not slower in Rust.
- `--correction-when after` (intended origin, fill after the timed loop):
  C++ 453 kops/s `[449, 455]`, Rust 454 kops/s `[446, 467]`. C++/Rust
  **1.00×**, paired *p* = 5.37×10⁻¹. The test cannot tell the languages
  apart. Intended-origin p50 stays about a second of schedule drift
  (C++ 1260 ms, Rust 1119 ms). CPU ~571% / ~592%. Throughput sits with P1
  cap 0 (446 / 467), not with P1 default cap (138 / 83).

**Do not copy these kops/s into `figures/gen_macros.tex`.** They license
the same cause sentence as P1 cap 0: under this open-loop instrument the
published floor gap is the at-record 10 000-sample fill on the producer,
not service time and not a fill deferred until after the timed window.

**14-load fair-clock sweep (`bench/fair_latency_sweep.sh`, added 20 September
2026).** Same per-producer rates as `campaign-20260827-151927`, 7/7, mixed,
20 repeats, 3 s measured. Clock A (`--clocks start`, default) is
`--latency-origin start --correction-cap 0`. Clock B (`--clocks after`) is
`--correction-when after`. Logs are `fair-start-*.jsonl` and
`fair-after-*.jsonl`, never `campaign-*.jsonl`. `campaign.sh` refuses those
clock flags unless `--prefix` is set, so the main campaign discovery cannot
mistake either log for the compared pair.

**Macro source (added 20 September 2026).** `bench/probe_facts.py` reads both
logs and writes `figures/gen_probes.tex` under the `\ProbeStart*` and
`\ProbeAfter*` prefixes, so prose quoting either sweep quotes a generated
value. Two refusals are built in. It does not emit Clock B percentiles,
because that clock keeps the intended origin and past saturation its
percentiles are schedule drift in seconds rather than service time. And
neither prefix may enter `gen_macros.tex`, because the reported campaign stays
the pre-committed compared pair for the below-saturation tail result. The
refresh script calls this generator before `plot_figures.py`, which reads the
Clock B log separately for the overload instrument comparison.

**Result (Clock A, 1120 runs, certified, Cherry Chicago AMD EPYC 7443P
`calm-husky`, 20 September 2026).** Full 14-load grid, four variants, 20
interleaved repeats, `--pin 2-17` after SMT off, Rocky image. Log:
`bench/results/fair-start-20260920-195304.jsonl`. Env:
`bench/results/env-20260920-195229.txt`. Worst throughput spread across all
56 cells is 2.5%, so every cell certifies.

- **Rust's p99 is lower at all fourteen loads**, by 1 to 2 µs. Pooled over
  allocators the p99 runs 21 µs (C++) against 19 µs (Rust) across the whole
  sweep. At 784 kops/s offered the paired difference is
  $+1.49\,\mu$s (system) and $+2.66\,\mu$s (jemalloc) in C++'s disfavour,
  exact paired permutation *p* = 3.91×10⁻³ on 16 pairs in both.
- **The cliff does not appear on this clock.** Both languages track to
  448 kops/s offered, then plateau rather than collapse: at 784 kops/s
  offered C++ holds 441 kops/s and Rust 470. The reported campaign has
  147 and 84 at the same point. The drop below each language's own tracking
  rate is therefore the at-record fill, not the service.
- Service-time p50 at 784 kops/s offered: C++ 15.8 µs (system) and 15.9
  (jemalloc), Rust 15.2 and 14.7.

**This is not the compared pair and does not replace it.** Do not copy any
kops/s or microsecond from this sweep into `figures/gen_macros.tex`. The
reported campaign stays `campaign-20260827-151927` on its own clock.

**Result (Clock B, 1120 runs, certified, same host, same evening).** Intended
origin, cap 10 000, fill applied after the timed loop.
`bench/results/fair-after-20260920-213440.jsonl`. Env:
`bench/results/env-20260920-213438.txt`. Worst throughput spread 2.5%. Both
languages track to 448 kops/s offered and then plateau: at 784 kops/s offered
C++ holds 447 kops/s and Rust 461 (0.97×). On the system allocator the paired
throughput difference is not significant (*p* = 7.01×10⁻² on 16 pairs). On
jemalloc Rust is ahead (*p* = 3.91×10⁻³). Intended-origin p50 at 784 kops/s
offered is schedule drift on the order of a second, as expected on this
clock. Throughput sits with Clock A and with P1 cap 0, not with the reported
campaign floor. The correction itself can stay. Charging it inside the timed
loop is what made the cliff.

**Bare-metal status (2026-08-26).** The divergence itself reproduces on a dedicated
AMD EPYC 7443P: at 640 kops/s offered, where every arm has collapsed and each one's
15 repeats agree to within 0.4%, C++ sustains 158 kops/s against Rust's 96, a ratio of
1.64 against the 1.8 the thesis reports from the KVM guest. Different vendor, different
microarchitecture, no hypervisor, same ordering and roughly the same magnitude.

The three 2026-08 queue and map probes above are **not** re-established on
the Nokia/UH 7443, and one attempt to
do so has to be discarded. It ran at 512 kops/s, the first swept load past the knee, which
the same campaign shows to be **metastable**: the Rust arms are bimodal across repeats
there, serving the full offered rate in some and collapsing in others, with throughput
varying by 37%. A median across a distribution with a mode at each end is not a
measurement, and the probe ratios computed from it (which appeared to reverse the
divergence) mean nothing. A re-run at 640 kops/s was started and the machine was released
before it finished. **Treat the 19 September 7443P result as the current
evidence for P0–P2, and the 20 September 7443P result as the current
evidence for P3.** The 18–20 September WSL2 runs stay on file as
uncertified direction. Do not quote the discarded 512 kops/s queue-probe
attempt.

The lesson generalises the one above it: a substitution probe also has to be run at an
operating point whose repeats agree. `bench/queue_probes.sh` builds all four arms and runs
them interleaved inside one repeat, so both probes share their baselines. It refuses to
certify a run when the baseline arm is still serving its offered rate, and when any arm's
throughput varies by more than 5% across repeats. `bench/overload_probes.sh` uses the
same two checks, and the 18 September WSL2 run fired the spread check on every phase. Replayed against the discarded 512 kops/s
data that second check fires on three of the four arms, the Rust channel at 39%, so the run
that produced the misleading ratios would not have been reportable.

**Benchmark harness (recorded 2026-07, `bench/`):**
- Latency capture: C++ uses a from-scratch, header-only HDR histogram
  (`cpp/bench/hdr.hpp`, a port of the canonical HdrHistogram bucketing algorithm);
  Rust uses the canonical `hdrhistogram` crate. Both configured identically:
  range `[1 ns, 3.6 s]`, 3 significant figures. This is a *recorded deviation* (no
  system HdrHistogram_c was available); the C++ port was validated against a known
  uniform distribution (p50/p90/p99 within 3-sig-fig tolerance).
- Matched allocator: C++ links the system `libjemalloc.so.2` via
  `-DUECM_USE_JEMALLOC=ON`; Rust sets a `#[global_allocator]` from `tikv-jemallocator`
  behind the `jemalloc` feature (built from source by `tikv-jemalloc-sys`). Default
  builds use each language's system allocator.
- The workload and CLI are identical across languages; see `bench/README.md`. Two
  workloads: `signal` (preload + `handle_signaling` hot path) and `mixed` (a pinned RAN
  lifecycle generator: attach → signaling → bearer setup → handover → release). The
  mixed generator keeps a per-slot expected-state model so emitted ops are valid, and
  advances it optimistically with a fixed SplitMix64 draw order, so the per-op-kind
  counts are **identical** in C++ and Rust for a given `(active_ues, seed)`, verified
  equal, an extra parity signal beyond §11.
- Coordinated omission is handled by an optional `--rate` (fixed send schedule + HDR
  correction from intended send time). The synthetic backfill is capped at 10 000
  samples per completed operation (`kMaxCorrectionSamples` in `cpp/bench/hdr.hpp`,
  `MAX_CORRECTION_SAMPLES` in `rust/examples/bench.rs`). `--correction-cap N`
  overrides that cap. `N == 0` records the real sample and drops the synthetics.
  The default is 10 000, so a campaign binary without the flag is the reported
  instrument. P1 of the 18 September probes uses 0.
  `--correction-when after` records real samples during the timed loop and
  applies the same capped fill once the producer finishes (P3). Default is
  `record`. `--latency-origin start` records `t_done - t_actual_send` instead
  of the intended send time (P3). Default is `intended`. Neither flag is a
  campaign default. Coordinated omission is skipped when the origin is `start`.
  `bench/fair_latency_sweep.sh` applies them across the reported 14-load grid
  and writes `fair-*.jsonl`. Clock A ran on `calm-husky` on 20 September 2026
  and is certified. Clock B ran on the same host that evening and is
  certified.
- Resource capture (RQ3): each run reports peak RSS and total CPU via `getrusage`
  (`ru_maxrss`, `ru_utime`+`ru_stime`), emitted in JSON/CSV. The Rust side's single
  `unsafe` `getrusage` FFI call lives only in the benchmark example (`libc`
  dev-dependency); the library remains `unsafe`-free and dependency-free.
- Allocator-internal accounting (RQ3, added Aug 2026): each run also reports
  jemalloc's own `stats.allocated`, `stats.active`, `stats.metadata`,
  `stats.resident`, `stats.mapped` and `stats.retained`, under the `je` key. This
  splits peak RSS into live allocation, arena and tcache bookkeeping, and space
  retained but unmapped, which `ru_maxrss` cannot do. Both languages read the same
  six counters from the same allocator after writing `epoch` to refresh them, so the
  two are differenceable — the same one-instrument principle already applied to
  `lizard` for the complexity proxies and to `jeprof` for the allocation profiles.
  This is a *recorded deviation* in how the counters are reached: C++ calls `mallctl`
  declared as a weak symbol (the Ubuntu runtime ships in `libjemalloc.so.2` while the
  header is a separate dev package, and the system-allocator arms deliberately do not
  link jemalloc at all), while Rust uses `tikv-jemalloc-ctl` with its `stats` feature.
  The system-allocator arms report every field as `null`, never `0`, since a zero
  would read as "no arena metadata" rather than "not measured" — the same convention
  `bench/counters.sh` uses for uncountable PMU events.
  Note the pre-existing asymmetry this inherits and does not introduce: the C++ arm
  links the distribution's jemalloc while the Rust arm builds 5.3.1 from source
  through `tikv-jemalloc-sys`, so a metadata difference between the two arms is a
  difference between two builds of the allocator as well as between two programs.
  `bench/campaign.sh` pins `thp:never,narenas:16` on both sides, which removes the
  larger part of that confound but not the version difference.
- Heap profiling for the peak-RSS attribution (RQ3, revised Aug 2026,
  `bench/alloc_profile.sh`). Three recorded deviations, all confined to a dedicated
  profiling build tree that no timed run uses, and all found by running the script in
  the container rather than on the testbed:
  1. **A prof-enabled allocator for the C++ arm.** The distribution jemalloc both the
     measurement host and the container link is built without `--enable-prof`, so the
     C++ arm could not be profiled at all: the binary answers `Invalid conf pair:
     prof:true` and no dump lands. `docker/Dockerfile` builds a prof-enabled jemalloc
     from the *same source the Rust arm links* (the tree vendored in
     `tikv-jemalloc-sys`, 5.3.1-0-g81034ce), and `cpp/build-jemalloc-prof` links it by
     absolute path when `UECM_JEMALLOC_PROF_LIB` is set. Same source and version on
     both sides therefore, though not an identical configure line: the Rust side is
     static and `_rjem_`-prefixed, this one shared and unprefixed. Note this *removes*
     the allocator-version confound recorded above for the profile specifically, and
     leaves it in place for the campaign, which still links the distribution build.
  2. **Frame pointers on both sides.** jemalloc walks the stack without libunwind here,
     so at `-O2` with frame pointers omitted the walk stops inside the allocator and no
     application site appears at all. The profiling tree adds
     `-fno-omit-frame-pointer` (after `-O2`, which re-enables omission) and the Rust
     profiling build adds `-C force-frame-pointers=yes`. Symmetric, and attribution
     only: a frame pointer costs a register, so neither belongs in a timed build.
  3. **Dumps taken during the run, not at exit.** `prof_final` dumps the live heap when
     the process exits, which is after the contexts and shard queues have been dropped:
     measured, the C++ exit dump held 92 kB and the Rust one 640 bytes against a live
     heap of 2.3 MB mid-run. The script now also sets `lg_prof_interval` and keeps the
     dump with the highest live byte count, with the whole series and its trajectory
     kept beside it. Without this the profile is empty and looks like a heap with no
     allocations in it.
  One reading caveat, recorded because it changes which column carries the answer:
  jemalloc 5.3 keeps its own backtrace frame at the leaf of every sampled stack, so the
  *flat* column collapses onto `prof_backtrace_impl` and application sites read zero
  flat bytes. Sampled live totals are unaffected, since flat still sums to the sampled
  heap, and the cumulative column carries the attribution.
  `bench/parse_jeprof.py` detects the collapse and reports the cumulative ranking.
- Load sweep: `bench/load_sweep.sh` sweeps offered rate × the four variants and writes a
  latency/throughput/RSS/CPU-vs-load CSV (`bench/plot_sweep.py` renders it).
- Dependency hygiene: the Rust core library stays dependency-free: `hdrhistogram`
  is a `dev-dependency` and the bench lives under `examples/` so only the benchmark,
  not the library, pulls it in.

**Implementation review (recorded 2026-09-16, `docs/CODE_REVIEW.md`):**

An agent pass of production `cpp/`, `rust/src`, and `ffi/` against this specification found
no logic, memory, or state-machine defect on the path the thesis measures. It does not
close the independent two-expert review in `docs/TODO.md` item D2. Three edges sit
outside the campaign and the seven-vector suite:

- `QUEUE_CAPACITY == 0`. C++ `BoundedQueue` clamps 0 to 1. The Rust mutex-queue probe
  does the same. The compared Rust arm uses `sync_channel(capacity)`, and
  `sync_channel(0)` is a rendezvous channel. Default and campaign capacity is 1024.
- Public `shard_index(_, 0)`. `Service` clamps `N_SHARDS == 0` to 1. The free function
  in §8.1 does not: C++ `% 0` is undefined behaviour, Rust panics. Conformance vectors
  never pass 0. The `shard` op in both runners uses the raw config value.
- Concurrent `shutdown()` while another thread is still submitting. Sequential misuse
  is guarded (§7.1). C++ `running_` is a plain `bool`, so that aliasing is a data race.
  Rust `shutdown` takes `&mut self` and the aliasing does not compile. Benches join
  producers before shutdown.

The Rust `unsafe` bullet above is corrected in the same pass: `rust/src` has no `unsafe`
(grep), and `rust/src/lib.rs` does not currently carry `#![forbid(unsafe_code)]`.

---

## 13. Freeze checklist

Frozen 2026-09-15 as v1.0, tag `spec-v1.0`. Changes after this version are versioned
amendments (1.1, 1.2, ...) with a dated note in this section. Do not silently edit a
frozen requirement.

- [x] Supervisor review of data model, state machine, and API. *(Internal design review of
      §4–§6 carried out 2026-08-17 against both implementations. It found no defect in the
      state machine or the error model, and six places where this document did not describe
      what the code does; all six are now fixed here: `ReconfigParams` was undefined (§4.3);
      `rrc_transaction_id` was described as "last used" but is inert (§4.2); the abort path was
      called "state restored" when the serving cell is not restored (§5.2, §6.5); §6.1 claimed
      every successful mutation stamps the activity counter, which `release_context` does not;
      `count()` had no stated return type, atomicity, or snapshot semantics (§6.7); and §7.1
      prohibited submits outside the running window without a mechanism, which was a
      heap-use-after-free in C++ and a panic in Rust — now guarded in both. **Supervisor
      sign-off recorded 2026-09-15.**)*
- [x] Confirm concurrency model (thread-per-shard + bounded blocking queue) is acceptable.
- [x] Confirm default parameters and sweep ranges with the evaluation plan.
- [x] Confirm the conformance-vector format and seed an initial suite. *(Format + `basic.vec`/`shards.vec` seeded; shared runner passes for both implementations. Supervisor sign-off on the format recorded 2026-09-15 with the rest of the freeze.)*
- [x] On approval: set Version 1.0, tag `spec-v1.0`, and treat changes as versioned amendments. *(Done 2026-09-15.)*

**Amendment 2026-09-16 (recording only, requirements unchanged).** §12 now records three
configuration and lifecycle edges found by the 16 September implementation review, and
corrects the Rust `unsafe` line: no `unsafe` in `rust/src`, crate attribute absent.
Details in `docs/CODE_REVIEW.md`. Version remains 1.0. Tag `spec-v1.0` is unchanged.

**Amendment 2026-09-18 (wording only, requirements unchanged).** §1 names UECM as
per-device state work of the sort a gNB-CU-CP does, not as a production service domain.
§7 states that the thread-per-shard layout is a fairness control, not a copy of a
production runtime. Behaviour, API, and conformance vectors are unchanged.
Version remains 1.0. Tag `spec-v1.0` is unchanged.

**Amendment 2026-09-18 (recording only, requirements unchanged).** §12 records the
P0/P1/P2 overload-instrument probes (`bench/overload_probes.sh`). The harness
gains `--correction-cap` (default 10 000). Rust gains `--features sync-oneshot`
(probe only, completions via `sync_channel(1)`). Compared pair, API, and
conformance vectors are unchanged. Version remains 1.0. Tag `spec-v1.0` is
unchanged.

**Amendment 2026-09-20 (recording only, requirements unchanged).** §12 records
P3 of the overload-instrument probes: `--latency-origin start` and
`--correction-when after` (`bench/overload_probes.sh --phase p3`). The same
day's Cherry Chicago 7443P P3 run is certified there. The 14-load fair-clock
sweep is `bench/fair_latency_sweep.sh`, and its Clock A run on `calm-husky`
is certified in the same section. Clock B is certified there too. Compared
pair, API, and conformance vectors are unchanged. Version remains 1.0. Tag
`spec-v1.0` is unchanged.

---

## Appendix A: Frozen design decisions

These four choices were open at v0.1 and are locked at v1.0. They record what was
confirmed, not options still on the table.

1. **Reconfiguration richness.** The `Reconfiguring` state with begin/complete/abort is
   kept. Handover is central to UE context management and gives the workload a
   non-trivial procedure.
2. **Queue policy under overload.** Bounded + blocking (backpressure) is kept. Blocking
   makes tail latency the observable. The reject-with-`CapacityExceeded` alternative would
   have measured loss instead of latency growth.
3. **`std::expected` availability.** C++23 is the pinned language, and `std::expected` is
   used. No hand-rolled fallback was needed.
4. **DRB list dynamic vs fixed.** Dynamic (`std::vector` / `Vec`) is kept, so the
   allocator study (RQ3) observes realistic per-context allocation.
