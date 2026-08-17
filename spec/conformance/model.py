#!/usr/bin/env python3
"""Executable reference model of the UECM specification (spec/SPECIFICATION.md).

Why this exists
---------------
`run.sh` establishes two things: that each implementation reproduces the expected
results written into a vector file, and that the C++ and Rust transcripts are
byte-identical. Both are necessary and neither is sufficient. The expectations in
the seven hand-written vectors were derived from the specification by one person
reading it, and the cross-diff only shows the two implementations agree -- it
cannot distinguish "both correct" from "both wrong in the same way", which is the
failure mode a shared specification and a matched pair of authors makes most
likely.

This module is a third implementation of the same written specification, in a
third language, with no code shared with either. Used with `genvec.py` it turns
the parity argument from "two implementations agree on 223 hand-derived
operations" into "three independent implementations agree on tens of thousands of
generated ones, including sequences no human chose".

The model is deliberately the naive transcription of the specification: a dict per
shard, no optimisation, no cleverness. It is meant to be obviously correct on
inspection rather than fast.

Specification ambiguities, resolved here the way the vectors pin them
--------------------------------------------------------------------
Section 6 gives each operation's errors as a set, not an ordered sequence, so
where an operation can raise two errors at once the specification does not say
which wins. Three such orderings exist, all recorded in section 11:

  1. Argument validation runs before key lookup. `handle_signaling` on an absent
     id with `payload_len > 64` is `InvalidArgument`, not `NotFound`.
  2. `create_context` checks shard capacity before duplicate detection. Creating
     an existing id on a full shard is `CapacityExceeded`, not `AlreadyExists`.
  3. `add_drb` checks the DRB cap before duplicate detection. Re-adding an
     existing `drb_id` to a full list is `CapacityExceeded`, not `AlreadyExists`.

A fourth is not recorded in section 11 and is pinned by `states.vec`:
`abort_reconfigure` restores `state` but not `serving_cell_id`, which
`begin_reconfigure` has already overwritten. Section 5.2 calls the abort path
"state restored", which reads as though the cell should roll back too.

These four are the points where an independent reader could reasonably have
written a different model, so they are the points worth stating out loud.

Usage
-----
    model.py --check vectors/basic.vec      # replay a vector, verify its expectations
    model.py --check vectors/*.vec          # ... or the whole hand-written suite
    model.py --self-test                    # pinned-function known-answer tests
"""

from __future__ import annotations

import argparse
import glob
import sys
from dataclasses import dataclass, field

MASK64 = (1 << 64) - 1

# Section 9 defaults.
DEFAULT_N_SHARDS = 8
DEFAULT_QUEUE_CAPACITY = 1024
DEFAULT_MAX_CONTEXTS_PER_SHARD = 200000
MAX_DRBS = 8
MAX_SIGNALING_PAYLOAD = 64

STATE_NAMES = {0: "Idle", 1: "Connected", 2: "Reconfiguring", 3: "Released"}
IDLE, CONNECTED, RECONFIGURING = 0, 1, 2


def shard_index(ue_id: int, n_shards: int) -> int:
    """Section 8.1: SplitMix64 finalizer, then modulo n_shards.

    `n_shards == 0` is outside the specification: `Service` clamps a configured
    zero to one before any routing happens, so this function is never reached
    with it. Called directly it is undefined in C++ and a panic in Rust, so the
    generator never emits it.
    """
    x = ue_id & MASK64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK64
    x = x ^ (x >> 31)
    return x % n_shards


def fnv1a_64(key: int) -> int:
    """Section 8.2: FNV-1a over the 8 little-endian bytes of the key."""
    h = 0xCBF29CE484222325
    for i in range(8):
        b = (key >> (i * 8)) & 0xFF
        h = ((h ^ b) * 0x100000001B3) & MASK64
    return h


@dataclass
class Context:
    """Section 4.2, minus the fields no transcript line can observe.

    `security_key`, `rrc_transaction_id` and per-DRB contents are omitted: the
    canonical transcript never prints them, so the model cannot be held to them.
    They are covered by the mirrored `invariants` suites instead.
    """

    ue_id: int
    state: int = IDLE
    serving_cell_id: int = 0
    drb_ids: list[int] = field(default_factory=list)
    messages_handled: int = 0


class Model:
    """The specification, executed. One dict per shard, keyed by ue_id."""

    def __init__(
        self,
        n_shards: int = DEFAULT_N_SHARDS,
        queue_capacity: int = DEFAULT_QUEUE_CAPACITY,
        max_contexts_per_shard: int = DEFAULT_MAX_CONTEXTS_PER_SHARD,
    ) -> None:
        # Section 7.1: worker count equals shard count, and Service clamps 0 to 1.
        self.n_shards = max(1, n_shards)
        self.queue_capacity = queue_capacity  # backpressure only; not observable
        self.max_contexts_per_shard = max_contexts_per_shard
        self.shards: list[dict[int, Context]] = [{} for _ in range(self.n_shards)]

    # -- helpers ---------------------------------------------------------

    def _shard(self, ue_id: int) -> dict[int, Context]:
        return self.shards[shard_index(ue_id, self.n_shards)]

    def _get(self, ue_id: int) -> Context | None:
        return self._shard(ue_id).get(ue_id)

    def count(self) -> int:
        return sum(len(s) for s in self.shards)

    def state_of(self, ue_id: int) -> int | None:
        """Current state, or None if no such context. For steering a generator."""
        ctx = self._get(ue_id)
        return None if ctx is None else ctx.state

    # -- operations (section 6) -----------------------------------------
    #
    # Each returns the canonical transcript string the runners emit, so the
    # model's output is directly comparable to theirs.

    def create_context(self, ue_id: int, cell: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        shard = self._shard(ue_id)
        if len(shard) >= self.max_contexts_per_shard:
            return "Err(CapacityExceeded)"  # ambiguity 2: capacity before duplicate
        if ue_id in shard:
            return "Err(AlreadyExists)"
        shard[ue_id] = Context(ue_id=ue_id, state=IDLE, serving_cell_id=cell)
        return "Ok"

    def setup_connection(self, ue_id: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        if ctx.state != IDLE:
            return "Err(InvalidState)"
        ctx.state = CONNECTED
        return "Ok"

    def handle_signaling(self, ue_id: int, kind: int, payload_len: int) -> str:
        # ambiguity 1: both argument checks precede the key lookup
        if ue_id == 0 or payload_len > MAX_SIGNALING_PAYLOAD:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        if ctx.state != CONNECTED:
            return "Err(InvalidState)"
        ctx.messages_handled += 1
        return f"Ok(accepted=true,handled={ctx.messages_handled})"

    def add_drb(self, ue_id: int, drb_id: int, qfi: int, teid: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        if ctx.state != CONNECTED:
            return "Err(InvalidState)"
        if len(ctx.drb_ids) >= MAX_DRBS:
            return "Err(CapacityExceeded)"  # ambiguity 3: cap before duplicate
        if drb_id in ctx.drb_ids:
            return "Err(AlreadyExists)"
        ctx.drb_ids.append(drb_id)
        return "Ok"

    def begin_reconfigure(self, ue_id: int, cell: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        if ctx.state != CONNECTED:
            return "Err(InvalidState)"
        ctx.state = RECONFIGURING
        ctx.serving_cell_id = cell
        return "Ok"

    def _finish_reconfigure(self, ue_id: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        if ctx.state != RECONFIGURING:
            return "Err(InvalidState)"
        ctx.state = CONNECTED
        return "Ok"

    def complete_reconfigure(self, ue_id: int) -> str:
        return self._finish_reconfigure(ue_id)

    def abort_reconfigure(self, ue_id: int) -> str:
        # ambiguity 4: state rolls back, serving_cell_id does not
        return self._finish_reconfigure(ue_id)

    def release_context(self, ue_id: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        shard = self._shard(ue_id)
        if ue_id not in shard:
            return "Err(NotFound)"  # section 6.5: NotFound, so double-release is visible
        del shard[ue_id]
        return "Ok"

    def lookup(self, ue_id: int) -> str:
        if ue_id == 0:
            return "Err(InvalidArgument)"
        ctx = self._get(ue_id)
        if ctx is None:
            return "Err(NotFound)"
        return (
            f"Ok(state={STATE_NAMES[ctx.state]},cell={ctx.serving_cell_id},"
            f"drbs={len(ctx.drb_ids)},messages_handled={ctx.messages_handled})"
        )


# -- vector-file execution ------------------------------------------------


class VectorError(Exception):
    pass


def parse_line(raw: str) -> tuple[str, list[str], dict[str, str], str | None]:
    """Parse one vector line into (op, positional, keyword, expected)."""
    body = raw.split("#", 1)[0].strip()
    if not body:
        return "", [], {}, None
    expected: str | None = None
    if "=>" in body:
        lhs, rhs = body.split("=>", 1)
        body, expected = lhs.strip(), rhs.strip()
    op, *rest = body.split()
    pos: list[str] = []
    kv: dict[str, str] = {}
    for tok in rest:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
        else:
            pos.append(tok)
    return op, pos, kv, expected


def run_vector(path: str) -> tuple[list[str], list[tuple[int, str, str]]]:
    """Execute a vector against the model.

    Returns the transcript and the list of (lineno, expected, actual) mismatches
    for lines that carried an expectation.
    """
    n_shards = DEFAULT_N_SHARDS
    queue_capacity = DEFAULT_QUEUE_CAPACITY
    max_ctx = DEFAULT_MAX_CONTEXTS_PER_SHARD
    model: Model | None = None
    transcript: list[str] = []
    mismatches: list[tuple[int, str, str]] = []

    def ensure() -> Model:
        nonlocal model
        if model is None:
            model = Model(n_shards, queue_capacity, max_ctx)
        return model

    def num(kv: dict[str, str], key: str, default: int = 0) -> int:
        return int(kv[key]) if key in kv else default

    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            op, pos, kv, expected = parse_line(raw)
            if not op:
                continue

            if op == "config":
                if model is not None:
                    raise VectorError(f"{path}:{lineno}: config after operations")
                n_shards = num(kv, "n_shards", n_shards)
                queue_capacity = num(kv, "queue_capacity", queue_capacity)
                max_ctx = num(kv, "max_contexts_per_shard", max_ctx)
                continue

            uid = int(pos[0]) if pos else 0

            if op == "shard":
                # Uses the configured value, not the clamped one: the runners
                # call the free function directly rather than going through
                # Service, which is the only place the clamp lives.
                actual = str(shard_index(uid, n_shards))
            elif op == "count":
                actual = str(ensure().count())
            elif op == "create":
                actual = ensure().create_context(uid, num(kv, "cell"))
            elif op == "setup":
                actual = ensure().setup_connection(uid)
            elif op == "signal":
                actual = ensure().handle_signaling(uid, num(kv, "kind"), num(kv, "len"))
            elif op == "adddrb":
                actual = ensure().add_drb(uid, num(kv, "id"), num(kv, "qfi"), num(kv, "teid"))
            elif op == "begin_reconf":
                actual = ensure().begin_reconfigure(uid, num(kv, "cell"))
            elif op == "complete_reconf":
                actual = ensure().complete_reconfigure(uid)
            elif op == "abort_reconf":
                actual = ensure().abort_reconfigure(uid)
            elif op == "release":
                actual = ensure().release_context(uid)
            elif op == "lookup":
                actual = ensure().lookup(uid)
            else:
                raise VectorError(f"{path}:{lineno}: unknown op '{op}'")

            transcript.append(actual)
            if expected is not None and actual != expected:
                mismatches.append((lineno, expected, actual))

    return transcript, mismatches


# -- self-test ------------------------------------------------------------


def self_test() -> int:
    """Known-answer tests for the pinned functions of section 8.

    The same vectors the C++ and Rust suites use. A model that reimplemented
    SplitMix64 or FNV-1a subtly wrong would otherwise generate wrong shard
    expectations and blame the implementations for its own bug.
    """
    # The same tables cpp/tests/test_hash.cpp and rust/tests/conformance.rs use.
    mix_kat = [
        (0, 0x0000000000000000),
        (1, 0x5692161D100B05E5),
        (2, 0xDBD238973A2B148A),
        (1001, 0x7139BB2427627383),
        (0xFFFFFFFFFFFFFFFF, 0xB4D055FCF2CBBD7B),
    ]
    fnv_kat = [
        (0, 0xA8C7F832281A39C5),
        (1, 0x89CD31291D2AEFA4),
        (2, 0xE6BD86443DF8CE07),
        (255, 0x9016B196E349A31A),
        (256, 0xE3757CA7D64666EA),
        (1001, 0x2E5741B73FAF0DDD),
        (0xFFFFFFFFFFFFFFFF, 0x8CF51A8BFCA3883D),
    ]
    failures = 0

    for key, want in mix_kat:
        raw = mix_raw(key)
        if raw != want:
            print(f"FAIL splitmix64({key}) = {raw:#x}, want {want:#x}", file=sys.stderr)
            failures += 1

    for key, want in fnv_kat:
        got = fnv1a_64(key)
        if got != want:
            print(f"FAIL fnv1a_64({key}) = {got:#x}, want {want:#x}", file=sys.stderr)
            failures += 1

    # Range and determinism, over the shard counts the suite uses.
    for n in (1, 2, 8, 13, 64):
        for key in range(1, 2000):
            a = shard_index(key, n)
            if a != shard_index(key, n) or not 0 <= a < n:
                print(f"FAIL shard_index({key}, {n}) out of range or unstable", file=sys.stderr)
                failures += 1
                break

    # A non-power-of-two count must reach every bucket: this is what separates
    # the specified modulo from a bitmask.
    hit = {shard_index(k, 13) for k in range(1, 5000)}
    if hit != set(range(13)):
        print(f"FAIL shard_index mod 13 reached {sorted(hit)}", file=sys.stderr)
        failures += 1

    print(f"[model self-test] {failures} failures", file=sys.stderr)
    return 1 if failures else 0


def mix_raw(ue_id: int) -> int:
    """The SplitMix64 finalizer without the modulo, for known-answer testing."""
    x = ue_id & MASK64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK64
    return x ^ (x >> 31)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", nargs="*", default=[], metavar="VEC",
                    help="replay vector files and verify their expectations")
    ap.add_argument("--self-test", action="store_true",
                    help="known-answer tests for the pinned section 8 functions")
    args = ap.parse_args()

    rc = 0
    if args.self_test:
        rc |= self_test()

    paths: list[str] = []
    for pattern in args.check:
        paths.extend(sorted(glob.glob(pattern)) or [pattern])

    total_ops = total_bad = 0
    for path in paths:
        try:
            transcript, mismatches = run_vector(path)
        except (OSError, VectorError) as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            rc = 1
            continue
        total_ops += len(transcript)
        total_bad += len(mismatches)
        status = "ok" if not mismatches else f"FAIL ({len(mismatches)} mismatches)"
        print(f"{path:<40} {len(transcript):>5} ops  {status}")
        for lineno, expected, actual in mismatches:
            print(f"  line {lineno}: expected '{expected}' got '{actual}'")
        if mismatches:
            rc = 1

    if paths:
        print(f"model vs hand-written expectations: {total_ops} ops, {total_bad} mismatches")

    if not paths and not args.self_test:
        ap.print_help()
    return rc


if __name__ == "__main__":
    sys.exit(main())
