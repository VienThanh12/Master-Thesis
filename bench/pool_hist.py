#!/usr/bin/env python3
"""Pool persisted HDR histograms across repeats, and verify that persisting them lost nothing.

`campaign.sh` writes one sidecar record per run (`campaign-<stamp>.hist.jsonl`)
holding the full occupied buckets of that run's latency histogram, and of its
inter-operation jitter histogram when `--jitter` was in effect. This script is
the analysis side of that file. It does two jobs.

**Pooling (default).** A single run at the campaign's representative load records
on the order of 170k latency samples, so its p99.99 rests on ~17 observations and
is dominated by sampling noise. Concatenating the distributions of 20 repeats
gives ~3.4M samples and ~340 observations past p99.99, which is what makes the
far tail readable at all.

Pooling is *not* the same statistic as the one `aggregate.py` reports, and the
two must not be mixed in a single claim:

  * `aggregate.py` takes the per-run percentile and reports the **median across
    repeats with a bootstrap CI**. Repeats are the unit of analysis, so the
    spread across runs is visible and a paired test is possible.
  * this script concatenates all samples and takes **one percentile of the
    pooled distribution**. Operations are the unit, the far tail is far better
    resolved, and there is **no across-repeat interval** -- one pooled number has
    no dispersion to quote.

So the pooled figure is the far-tail estimate, and the per-repeat figures remain
the basis for any paired comparison. See bench/README.md.

**Verification (`--verify`).** Recomputes each run's percentiles from its
persisted buckets and checks them against the values the benchmark binary printed
into the main JSONL for the same run. If those agree for every run in a campaign,
the sidecar is a faithful record of the histogram rather than a lossy summary of
it, which is the only reason to trust a far tail computed after the fact.

Both modes also assert that every persisted value is a point on the HDR lattice
implied by the run's own (low, high, sig), and that both languages used the same
lattice. The C++ port and the Rust `hdrhistogram` crate are independent
implementations of the same bucketing, so their agreement is checked rather than
assumed.

Usage:
  python3 bench/pool_hist.py results/campaign-XXXX.hist.jsonl
  python3 bench/pool_hist.py results/campaign-XXXX.hist.jsonl --out pooled.csv
  python3 bench/pool_hist.py results/campaign-XXXX.hist.jsonl \
      --verify results/campaign-XXXX.jsonl
"""
import argparse
import json
import math
import sys

# Quantiles reported from the pooled distribution. Same literals the two
# benchmark binaries pass to their own quantile functions, so a pooled number and
# a per-run number are the same statistic at a different unit of analysis.
POOLED_QUANTILES = [
    ("p50", 0.50),
    ("p90", 0.90),
    ("p99", 0.99),
    ("p999", 0.999),
    ("p9999", 0.9999),
]

# Percentiles checked by --verify, against the keys the binaries emit in lat_ns.
VERIFY_QUANTILES = [
    ("p25", 0.25),
    ("p50", 0.50),
    ("p75", 0.75),
    ("p90", 0.90),
    ("p99", 0.99),
    ("p999", 0.999),
    ("p9999", 0.9999),
]


class Lattice:
    """The HDR value grid implied by (low, high, sig).

    A faithful port of the bucketing in cpp/bench/hdr.hpp, which is itself a port
    of the canonical algorithm the Rust crate implements. Used only to validate
    persisted values: if a value is not a grid point, something wrote a raw
    sample rather than a bucket boundary.
    """

    def __init__(self, low, high, sig):
        self.low = max(int(low), 1)
        self.high = int(high)
        largest = 2 * 10 ** int(sig)
        sub_bucket_count_magnitude = math.ceil(math.log2(largest))
        self.half_mag = max(sub_bucket_count_magnitude, 1) - 1
        self.unit_mag = int(math.floor(math.log2(self.low)))
        self.sub_bucket_count = 2 ** (self.half_mag + 1)
        self.sub_bucket_half_count = self.sub_bucket_count // 2
        self.sub_bucket_mask = (self.sub_bucket_count - 1) << self.unit_mag

        smallest_untrackable = self.sub_bucket_count << self.unit_mag
        buckets = 1
        while smallest_untrackable < self.high:
            smallest_untrackable <<= 1
            buckets += 1
        self.bucket_count = buckets
        self.counts_len = (buckets + 1) * self.sub_bucket_half_count

    def _bucket_index(self, value):
        return (
            (value | self.sub_bucket_mask).bit_length()
            - self.unit_mag
            - (self.half_mag + 1)
        )

    def _lowest_equivalent(self, value):
        bi = self._bucket_index(value)
        si = value >> (bi + self.unit_mag)
        return si << (bi + self.unit_mag)

    def _equivalent_range(self, value):
        bi = self._bucket_index(value)
        si = value >> (bi + self.unit_mag)
        adjusted = bi + 1 if si >= self.sub_bucket_count else bi
        return 1 << (self.unit_mag + adjusted)

    def _value_at_index(self, index):
        bucket_index = (index >> self.half_mag) - 1
        sub_bucket_index = (index & (self.sub_bucket_half_count - 1)) + self.sub_bucket_half_count
        if bucket_index < 0:
            sub_bucket_index -= self.sub_bucket_half_count
            bucket_index = 0
        return sub_bucket_index << (bucket_index + self.unit_mag)

    def points(self):
        """Every highest-equivalent value the grid can emit."""
        out = set()
        for i in range(self.counts_len):
            v = self._value_at_index(i)
            out.add(self._lowest_equivalent(v) + self._equivalent_range(v) - 1)
        return out


def value_at_quantile(pairs, total, q):
    """Quantile of a sparse histogram given as ascending [value, count] pairs.

    Deliberately the same three steps both binaries use -- ceil(q * total),
    floored at one sample, then walk the buckets accumulating counts -- so a
    pooled or recomputed number is comparable to one the binary printed instead of
    being a differently-defined estimate that happens to be close.
    """
    if total <= 0:
        return 0
    q = min(q, 1.0)
    count_at = math.ceil(q * total)
    if count_at < 1:
        count_at = 1
    running = 0
    for value, count in pairs:
        running += count
        if running >= count_at:
            return value
    return pairs[-1][0] if pairs else 0


def load_sidecar(path):
    recs = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"{path}:{lineno}: malformed sidecar record: {e}")
    return recs


def check_lattices(recs):
    """Assert every persisted value is a grid point, and that both languages share the grid."""
    configs = {}
    for r in recs:
        h = r["hdr"]
        configs.setdefault((h["low"], h["high"], h["sig"]), set()).add(r["lang"])
    if len(configs) != 1:
        detail = "; ".join(f"{cfg} used by {sorted(langs)}" for cfg, langs in configs.items())
        sys.exit(f"FAIL: histogram configurations differ across runs: {detail}")
    (cfg, langs), = configs.items()
    lattice = Lattice(*cfg)
    points = lattice.points()

    bad = 0
    checked = 0
    for r in recs:
        for key in ("lat", "jitter"):
            block = r.get(key)
            if not block:
                continue
            for value, _count in block["pairs"]:
                checked += 1
                if value not in points:
                    bad += 1
                    if bad <= 5:
                        print(
                            f"  off-lattice value in {r['lang']}/{r['alloc']} {key}: {value}",
                            file=sys.stderr,
                        )
    if bad:
        sys.exit(f"FAIL: {bad}/{checked} persisted values are not HDR lattice points")
    print(
        f"lattice OK: {checked} persisted values, all on the "
        f"low={cfg[0]} high={cfg[1]} sig={cfg[2]} grid "
        f"({lattice.counts_len} slots), shared by {sorted(langs)}"
    )
    return lattice


def verify(recs, jsonl_path):
    """Recompute each run's percentiles from its buckets; compare with what the binary printed."""
    main = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                main.append(json.loads(line))
    if len(main) != len(recs):
        sys.exit(
            f"FAIL: {len(recs)} sidecar records against {len(main)} JSONL records. "
            "They are written one-for-one per run, so a mismatch means one of the "
            "two files is from a different campaign or a partial run."
        )

    failures = []
    for i, (side, row) in enumerate(zip(recs, main), 1):
        # Positional pairing is how the two files are written; confirm identity
        # rather than trusting it.
        for field in ("lang", "alloc", "workload", "shards", "producers", "rate", "ops_total"):
            if side.get(field) != row.get(field):
                sys.exit(
                    f"FAIL: record {i} identity mismatch on '{field}': "
                    f"sidecar {side.get(field)!r} vs JSONL {row.get(field)!r}"
                )

        lat = side["lat"]
        pairs, total = lat["pairs"], lat["total"]
        for name, q in VERIFY_QUANTILES:
            if name not in row["lat_ns"]:
                continue
            got = value_at_quantile(pairs, total, q)
            want = row["lat_ns"][name]
            if got != want:
                failures.append(f"record {i} ({side['lang']}/{side['alloc']}) {name}: "
                                f"from buckets {got} != printed {want}")
        if lat["max"] != row["lat_ns"]["max"]:
            failures.append(f"record {i} ({side['lang']}/{side['alloc']}) max: "
                            f"sidecar {lat['max']} != printed {row['lat_ns']['max']}")
        if sum(c for _v, c in pairs) != total:
            failures.append(f"record {i}: bucket counts sum to "
                            f"{sum(c for _v, c in pairs)}, header says {total}")

        jit = side.get("jitter")
        if jit and "jitter_ns" in row:
            for name, q in [("p50", 0.50), ("p99", 0.99), ("p999", 0.999)]:
                got = value_at_quantile(jit["pairs"], jit["total"], q)
                want = row["jitter_ns"][name]
                if got != want:
                    failures.append(f"record {i} ({side['lang']}/{side['alloc']}) jitter {name}: "
                                    f"from buckets {got} != printed {want}")
            if jit["total"] != row["jitter_ns"]["n"]:
                failures.append(f"record {i}: jitter total {jit['total']} != printed n "
                                f"{row['jitter_ns']['n']}")

    if failures:
        for line in failures[:20]:
            print("  " + line, file=sys.stderr)
        more = len(failures) - 20
        if more > 0:
            print(f"  ... and {more} more", file=sys.stderr)
        sys.exit(f"FAIL: {len(failures)} mismatches between persisted buckets and printed values")

    print(f"verify OK: {len(recs)} runs, every percentile recomputed from the persisted "
          "buckets matches the value the binary printed")


def pool(recs, producers=None):
    """Sum bucket counts across repeats per (lang, alloc, workload, offered load)."""
    groups = {}
    for r in recs:
        p = producers or int(r.get("producers", 1))
        offered = round(float(r.get("rate", 0.0)) * p)
        key = (r["lang"], r["alloc"], r.get("workload", "-"), offered)
        g = groups.setdefault(key, {"runs": 0, "lat": {}, "jitter": {}, "lat_max": 0,
                                    "jitter_max": 0})
        g["runs"] += 1
        for which in ("lat", "jitter"):
            block = r.get(which)
            if not block:
                continue
            acc = g[which]
            for value, count in block["pairs"]:
                acc[value] = acc.get(value, 0) + count
            g[f"{which}_max"] = max(g[f"{which}_max"], block["max"])
    return groups


def write_pooled(groups, path):
    cols = (["lang", "alloc", "workload", "offered_ops_s", "n_runs", "samples"]
            + [f"{n}_ns" for n, _ in POOLED_QUANTILES] + ["max_ns"]
            + ["jitter_samples"] + [f"jitter_{n}_ns" for n in ("p50", "p99", "p999")]
            + ["jitter_max_ns"])
    lines = [",".join(cols)]
    for (lang, alloc, workload, offered), g in sorted(groups.items()):
        lat_pairs = sorted(g["lat"].items())
        lat_total = sum(c for _v, c in lat_pairs)
        row = [lang, alloc, workload, str(offered), str(g["runs"]), str(lat_total)]
        row += [str(value_at_quantile(lat_pairs, lat_total, q)) for _n, q in POOLED_QUANTILES]
        row.append(str(g["lat_max"]))

        jit_pairs = sorted(g["jitter"].items())
        jit_total = sum(c for _v, c in jit_pairs)
        row.append(str(jit_total))
        row += [str(value_at_quantile(jit_pairs, jit_total, q)) for q in (0.50, 0.99, 0.999)]
        row.append(str(g["jitter_max"]))
        lines.append(",".join(row))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path} ({len(groups)} pooled points)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hist_jsonl", help="campaign-<stamp>.hist.jsonl from campaign.sh")
    ap.add_argument("--out", default=None,
                    help="write pooled far-tail percentiles here (default: <input>.pooled.csv)")
    ap.add_argument("--verify", default=None, metavar="JSONL",
                    help="check the persisted buckets against the campaign's main JSONL")
    ap.add_argument("--producers", type=int, default=None,
                    help="override the producer count used to compute offered load")
    ap.add_argument("--no-pool", action="store_true", help="verify only, write no CSV")
    args = ap.parse_args()

    recs = load_sidecar(args.hist_jsonl)
    if not recs:
        sys.exit(f"no records in {args.hist_jsonl}")
    print(f"read {len(recs)} run records from {args.hist_jsonl}")

    check_lattices(recs)

    if args.verify:
        verify(recs, args.verify)

    if not args.no_pool:
        out = args.out or args.hist_jsonl.replace(".jsonl", "") + ".pooled.csv"
        groups = pool(recs, args.producers)
        write_pooled(groups, out)
        # Whether the pooled far tail is readable at all, in the units that decide it.
        worst = min(sum(g["lat"].values()) for g in groups.values())
        past = worst * 1e-4
        note = "" if past >= 10 else "  -- too few to read a far tail; pool more repeats"
        print(f"pooled far tail: smallest group has {worst} samples, "
              f"~{past:.0f} past p99.99{note}" if past >= 10 else
              f"pooled far tail: smallest group has {worst} samples, "
              f"~{past:.1f} past p99.99{note}")


if __name__ == "__main__":
    main()
