#!/usr/bin/env python3
"""Generate randomised conformance vectors with expectations taken from the model.

The seven hand-written vectors cover the cases a person thought to write down.
This generates the ones nobody thought of: long operation sequences drawn from a
seeded PRNG, with every expected result computed by `model.py` -- an
implementation of the specification that shares no code with either the C++ or
the Rust side.

Running the output through both `conformance_runner`s therefore checks three
things at once, where `run.sh` alone checks two:

  * C++ against an independent reading of the specification,
  * Rust against the same independent reading,
  * C++ against Rust, byte for byte, as before.

Generation is deterministic: the same seed and profile always produce the same
file, on any machine and any Python version, because the PRNG is a hand-written
SplitMix64 rather than the `random` module. A failing seed is therefore a
permanent, reproducible regression test -- print it, keep it, re-run it.

Profiles
--------
  lifecycle    realistic UE lifecycles: attach, signal, bearers, handover, release
  adversarial  weighted towards illegal transitions and boundary arguments
  capacity     tiny per-shard capacity and DRB lists, to sit on both limits
  routing      many shards and wide id ranges, to stress shard assignment
  mixed        an even blend of all of the above

Usage
-----
    genvec.py --seed 1 --ops 400 --profile mixed
    genvec.py --seed 1 --ops 400 --profile mixed --out generated/mixed-1.vec
"""

from __future__ import annotations

import argparse
import sys

from model import MASK64, Model, shard_index

PROFILES = ("lifecycle", "adversarial", "capacity", "routing", "mixed")


class SplitMix64:
    """The PRNG the benchmark harness already uses, so seeds mean the same thing.

    Hand-written rather than `random` so a seed reproduces byte-identically on
    any Python build; a generated vector that fails is only useful as a
    regression test if it can be regenerated exactly.
    """

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK64

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return z ^ (z >> 31)

    def below(self, n: int) -> int:
        return self.next_u64() % n

    def choice(self, seq):
        return seq[self.below(len(seq))]

    def chance(self, percent: int) -> bool:
        return self.below(100) < percent


# Every mutating operation, with the state it is legal from. Used both to steer
# generation towards deep states and to steer it deliberately away from them.
MUTATING_OPS = ("create", "setup", "signal", "adddrb",
                "begin_reconf", "complete_reconf", "abort_reconf", "release")

LEGAL_FROM = {
    "create": None,             # only when the context is absent
    "setup": 0,                 # Idle
    "signal": 1,                # Connected
    "adddrb": 1,                # Connected
    "begin_reconf": 1,          # Connected
    "complete_reconf": 2,       # Reconfiguring
    "abort_reconf": 2,          # Reconfiguring
    "release": "any",           # any live state
}


class Config:
    """Per-profile generation knobs."""

    def __init__(self, profile: str, rng: SplitMix64) -> None:
        self.profile = profile

        # drb_id_space must exceed MAX_DRBS or the list can never fill and
        # CapacityExceeded on add_drb becomes unreachable; keeping it just above
        # MAX_DRBS also makes duplicate drb_ids common, so both errors fire.
        # release_suppress is the chance of dropping release from an otherwise
        # legal set: release is legal from every live state, so left alone it
        # dominates and no context survives long enough to fill anything.

        if profile == "capacity":
            self.n_shards = rng.choice([1, 2, 3])
            self.max_contexts = rng.choice([2, 3, 4, 8])
            self.queue_capacity = rng.choice([1, 2, 16])
            self.id_pool_size = 12
            self.drb_id_space = 10
            self.valid_bias = 80
            self.release_suppress = 97
            self.drb_bias = 55
        elif profile == "routing":
            self.n_shards = rng.choice([1, 3, 7, 13, 16, 31, 64])
            self.max_contexts = 200000
            self.queue_capacity = 1024
            self.id_pool_size = 64
            self.drb_id_space = 10
            self.valid_bias = 60
            self.release_suppress = 75
            self.drb_bias = 20
        elif profile == "adversarial":
            self.n_shards = rng.choice([1, 5, 8, 13])
            self.max_contexts = rng.choice([4, 64, 200000])
            self.queue_capacity = rng.choice([1, 8, 1024])
            self.id_pool_size = 16
            self.drb_id_space = 10
            self.valid_bias = 25         # mostly illegal transitions
            self.release_suppress = 85
            self.drb_bias = 35
        elif profile == "lifecycle":
            self.n_shards = rng.choice([2, 4, 8, 13])
            self.max_contexts = 200000
            self.queue_capacity = rng.choice([16, 1024])
            self.id_pool_size = 24
            self.drb_id_space = 10
            self.valid_bias = 90         # mostly legal, so states run deep
            self.release_suppress = 88
            self.drb_bias = 35
        else:  # mixed
            self.n_shards = rng.choice([1, 3, 8, 13, 16])
            self.max_contexts = rng.choice([3, 32, 200000])
            self.queue_capacity = rng.choice([1, 64, 1024])
            self.id_pool_size = 32
            self.drb_id_space = 10
            self.valid_bias = 60
            self.release_suppress = 88
            self.drb_bias = 30


def build_id_pool(cfg: Config, rng: SplitMix64) -> list[int]:
    """Ids the generator draws from.

    Deliberately includes the reserved 0 and the u64 extremes, and for the
    routing profile a run of ids that all hash to one shard, which is the case
    that separates per-shard capacity from a service-wide limit.
    """
    pool = [0, 1, 2, MASK64, MASK64 - 1]

    while len(pool) < cfg.id_pool_size:
        kind = rng.below(4)
        if kind == 0:
            pool.append(rng.below(64) + 1)              # dense small ids
        elif kind == 1:
            pool.append(1000 + rng.below(1000))         # the 1001-style ids
        elif kind == 2:
            pool.append(rng.next_u64())                 # anywhere in u64
        else:
            pool.append((rng.next_u64() >> 32) | 1)     # sparse but not huge

    if cfg.profile in ("routing", "capacity"):
        # A handful of ids that provably land on the same shard.
        target = rng.below(cfg.n_shards)
        found, probe = 0, 1
        while found < 5 and probe < 200000:
            if shard_index(probe, cfg.n_shards) == target:
                pool.append(probe)
                found += 1
            probe += 1

    return pool


def pick_op(cfg: Config, model: Model, uid: int, rng: SplitMix64) -> str:
    """Choose the next operation for `uid`.

    With probability `valid_bias` the op is one the specification allows from the
    context's current state, so sequences make progress into Connected and
    Reconfiguring instead of bouncing off NotFound. Otherwise it is uniform over
    all operations, which is what produces the error cases.
    """
    if not rng.chance(cfg.valid_bias):
        return rng.choice(MUTATING_OPS)

    if uid == 0:
        return rng.choice(MUTATING_OPS)  # always InvalidArgument; nothing to steer

    state = model.state_of(uid)
    if state is None:
        return "create"

    legal = [op for op, need in LEGAL_FROM.items()
             if need == "any" or need == state]
    if len(legal) > 1 and rng.chance(cfg.release_suppress):
        legal = [op for op in legal if op != "release"]
    # Bearer setup competes with three other legal ops from Connected, so on an
    # even draw a context reaches MAX_DRBS only by luck and the DRB capacity
    # error stays unreachable.
    if "adddrb" in legal and rng.chance(cfg.drb_bias):
        return "adddrb"
    return rng.choice(legal)


def emit_op(cfg: Config, model: Model, op: str, uid: int, rng: SplitMix64) -> str:
    """Execute one operation against the model and render the vector line."""
    if op == "create":
        cell = rng.below(1000)
        return f"create {uid} cell={cell} => {model.create_context(uid, cell)}"

    if op == "setup":
        return f"setup {uid} => {model.setup_connection(uid)}"

    if op == "signal":
        kind = rng.below(8)
        # Sit on the payload boundary far more often than chance would.
        if rng.chance(30):
            length = rng.choice([0, 1, 63, 64, 65, 66, 255, 65535])
        else:
            length = rng.below(64)
        return f"signal {uid} kind={kind} len={length} => {model.handle_signaling(uid, kind, length)}"

    if op == "adddrb":
        drb_id = rng.below(cfg.drb_id_space)
        qfi = rng.below(16)
        teid = rng.below(100000)
        result = model.add_drb(uid, drb_id, qfi, teid)
        return f"adddrb {uid} id={drb_id} qfi={qfi} teid={teid} => {result}"

    if op == "begin_reconf":
        cell = rng.below(1000)
        return f"begin_reconf {uid} cell={cell} => {model.begin_reconfigure(uid, cell)}"

    if op == "complete_reconf":
        return f"complete_reconf {uid} => {model.complete_reconfigure(uid)}"

    if op == "abort_reconf":
        return f"abort_reconf {uid} => {model.abort_reconfigure(uid)}"

    if op == "release":
        return f"release {uid} => {model.release_context(uid)}"

    raise AssertionError(f"unhandled op {op}")


def generate(seed: int, ops: int, profile: str) -> tuple[list[str], int]:
    """Return the vector file's lines and the number of checked operations."""
    rng = SplitMix64(seed)
    cfg = Config(profile, rng)
    pool = build_id_pool(cfg, rng)
    model = Model(cfg.n_shards, cfg.queue_capacity, cfg.max_contexts)

    lines = [
        f"# GENERATED by genvec.py --seed {seed} --ops {ops} --profile {profile}",
        "# Expectations come from spec/conformance/model.py, an implementation of",
        "# the specification independent of both cpp/ and rust/. Do not hand-edit:",
        "# regenerate with the command above, which is deterministic.",
        "",
        f"config n_shards={cfg.n_shards} queue_capacity={cfg.queue_capacity} "
        f"max_contexts_per_shard={cfg.max_contexts}",
        "",
    ]
    checked = 0

    for _ in range(ops):
        uid = rng.choice(pool)
        op = pick_op(cfg, model, uid, rng)
        lines.append(emit_op(cfg, model, op, uid, rng))
        checked += 1

        # Observe often: a state divergence that only shows up in the final
        # sweep is far harder to localise than one caught two lines later.
        if rng.chance(25):
            lines.append(f"lookup {uid} => {model.lookup(uid)}")
            checked += 1
        if rng.chance(4):
            lines.append(f"count => {model.count()}")
            checked += 1

    # Final sweep: every id in the pool, so the whole surviving population is
    # compared field by field and not just the ids the run happened to revisit.
    lines.extend(["", "# --- final state sweep ---"])
    for uid in pool:
        lines.append(f"lookup {uid} => {model.lookup(uid)}")
        checked += 1
    lines.append(f"count => {model.count()}")
    checked += 1

    # Shard assignment for the whole pool (section 11.1 item 3). Skipped when the
    # id is 0 only in the sense that shard(0) is well defined and included.
    lines.extend(["", "# --- shard assignment ---"])
    for uid in pool:
        lines.append(f"shard {uid} => {shard_index(uid, cfg.n_shards)}")
        checked += 1

    lines.append("")
    return lines, checked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, required=True, help="PRNG seed (deterministic)")
    ap.add_argument("--ops", type=int, default=400, help="randomised operations to emit")
    ap.add_argument("--profile", choices=PROFILES, default="mixed")
    ap.add_argument("--out", help="output file (default: stdout)")
    args = ap.parse_args()

    lines, checked = generate(args.seed, args.ops, args.profile)
    text = "\n".join(lines)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"{args.out}: {checked} checked operations "
              f"(seed={args.seed} profile={args.profile})", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
