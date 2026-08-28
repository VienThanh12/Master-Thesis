#!/usr/bin/env python3
"""Generated macros for the virtualised-host campaign, kept for the validity argument.

Until 27 August 2026 this campaign *was* the thesis. Every table reported it, and
the far tail below saturation was the standing open question because the host
could not resolve it. The canonical repeat on bare metal replaced it as the
primary dataset, and the honest thing to do with the old one is not to delete it
but to report what it could and could not measure, because that contrast is the
strongest evidence the study has that its instrument is now adequate.

The two campaigns share a design exactly: same shard and producer count, same
fourteen load levels, same twenty repeats, same toolchain. They differ in the
machine. That is what makes the comparison worth a section, and it is also why
the numbers here have to be generated rather than remembered: a claim about the
difference between two hosts is a claim about two datasets at once.

Reads bench/results/campaign-20260812-154528.jsonl and writes figures/gen_guest.tex.
"""

import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(HERE, "results")

sys.path.insert(0, HERE)
from plot_figures import (  # noqa: E402
    REPR_LOAD_OPS, bootstrap_ci, deadline_limited_load, load_campaign,
    balance_repeats, rss_low_run_offset,
)

NS_PER_US = 1000.0
KB_PER_MIB = 1024.0

#: The virtualised campaign this thesis reported before the bare-metal repeat.
GUEST = "campaign-20260812-154528"
#: Its environment capture, matched by stamp.
GUEST_ENV = "env-20260812-154523.txt"


def variants(rows):
    return sorted({(r["lang"], r["alloc"]) for r in rows})


def at_load(rows, load):
    return [r for r in rows if int(r["rate"]) * r["producers"] == load]


def fmt(v, digits=0):
    return f"{v:.{digits}f}"


def host_facts(macros):
    path = os.path.join(RESULTS, GUEST_ENV)
    if not os.path.exists(path):
        return [f"no {GUEST_ENV}; host rows not generated"]
    text = open(path, encoding="utf-8").read()

    def grab(pattern, default="unknown"):
        # MULTILINE, because the capture is a block of lines and several of the
        # patterns below anchor to the start of one of them.
        m = re.search(pattern, text, re.M)
        return m.group(1).strip() if m else default

    model = grab(r"Model name:\s+(.+)")
    # The guest's lscpu reports the marketing string with the clock in it, which
    # tab:testbed already carries in its own row.
    macros["GuestCpu"] = re.sub(r"\s*@.*$", "", model).strip()
    macros["GuestCores"] = grab(r"^CPU\(s\):\s+(\d+)", "unknown")
    macros["GuestVirt"] = grab(r"virtualisation:\s+(\S+)")
    macros["GuestKernel"] = grab(r"Linux \S+ (\S+)")
    macros["GuestDistro"] = grab(r"distro:\s+(.+)")
    # The two host properties that turned out to matter, and neither was chosen.
    # Transparent hugepages is the leading candidate for the allocator effect
    # this host measured and no bare-metal host reproduced.
    macros["GuestThp"] = grab(r"transparent hugepages:\s+(\S+)")
    macros["GuestSteal"] = grab(r"steal ticks \(1 s sample\):\s+(\S+)")
    for field, key in (("isolcpus", "GuestIsolcpus"), ("nohz_full", "GuestNohzFull")):
        val = grab(rf"{field}:\s+(.+)")
        macros[key] = "none" if val.strip() == "(none)" else val.strip()
    macros["GuestGovernor"] = grab(r"governors:\s+(.+)")
    macros["GuestSmt"] = grab(r"smt/control:\s+(\S+)")
    gpp = grab(r"(g\+\+ \(.*?\) [\d.]+)")
    if gpp:
        macros["GuestGpp"] = re.sub(r"g\+\+ \(.*?\) ", "", gpp)
    rustc = grab(r"rustc (\d+\.\d+\.\d+|\d+\.\d+)")
    if rustc:
        macros["GuestRustc"] = rustc
    return []


def instrument_facts(macros, rows):
    """What the host did to the measurement, rather than what the code did.

    The decisive pair. The widest confidence interval on a single variant's p99
    against the spread between the four variants: when the first exceeds the
    second the campaign cannot order the variants at all, whatever the languages
    are doing, and that is a statement about the machine.
    """
    sub = at_load(rows, REPR_LOAD_OPS)
    if not sub:
        return [f"guest campaign has no {REPR_LOAD_OPS} ops/s level"]
    widths, meds = [], []
    for key in variants(rows):
        vals = [r["lat_ns"]["p99"] / NS_PER_US for r in sub
                if (r["lang"], r["alloc"]) == key]
        if not vals:
            continue
        med, lo, hi = bootstrap_ci(vals)
        widths.append(hi - lo)
        meds.append(med)
    macros["GuestPNineNineMaxCI"] = fmt(max(widths))
    macros["GuestPNineNineRange"] = fmt(max(meds) - min(meds))
    macros["GuestPNineNine"] = fmt(statistics.median(meds))
    macros["GuestPFifty"] = fmt(statistics.median(
        [r["lat_ns"]["p50"] / NS_PER_US for r in sub]))
    # The rule the representative load used to be chosen by. On this host it
    # returned a load where p99 sat just under the deadline, so it was locating
    # the host's noise floor and not the service's capacity.
    macros["GuestDeadlineLoad"] = fmt(deadline_limited_load(rows) / 1000.0)
    return []


def resource_facts(macros, rows):
    """The allocator effect this host measured and no bare-metal host reproduced."""
    steady = [r for r in rows if int(r["rate"]) * r["producers"] >= 32000]
    cell = {}
    for r in steady:
        cell.setdefault((r["lang"], r["alloc"], r["rate"]), []).append(r["rss_peak_kb"])
    rates = sorted({k[2] for k in cell})

    def med(lang, alloc, rate):
        return statistics.median(cell[(lang, alloc, rate)]) / KB_PER_MIB

    lang_eff, alloc_eff = [], []
    for rate in rates:
        for alloc in ("system", "jemalloc"):
            lang_eff.append(med("rust", alloc, rate) - med("cpp", alloc, rate))
        for lang in ("cpp", "rust"):
            alloc_eff.append(med(lang, "jemalloc", rate) - med(lang, "system", rate))
    macros["GuestRssLangLo"] = fmt(min(lang_eff), 1)
    macros["GuestRssLangHi"] = fmt(max(lang_eff), 1)
    macros["GuestRssAllocLo"] = fmt(min(alloc_eff), 1)
    macros["GuestRssAllocHi"] = fmt(max(alloc_eff), 1)
    # How many times the allocator effect exceeded the language effect here. The
    # thesis called this an order of magnitude for as long as this was the only
    # campaign, and no bare-metal host has reproduced it.
    macros["GuestRssAllocOverLang"] = fmt(
        statistics.median(alloc_eff) / statistics.median(lang_eff))

    # The bimodality that cost one peak-RSS row its place in the significance
    # family. Computed by the same helper the main campaign uses, so the two
    # figures are the same quantity and the comparison between them is a
    # comparison and not two definitions.
    offset = rss_low_run_offset(rows, REPR_LOAD_OPS)
    if offset is not None:
        macros["GuestRssLowRunOffset"] = fmt(offset)
    return []


def test_family_facts(macros, rows):
    """What the same test family returned on this host.

    Table tab:equivalence exists to separate a null worth reporting from a
    campaign declining to answer, and on the reported host every row resolves, so
    the table's own reason for existing is only visible in the earlier campaign.
    These two macros supply that contrast rather than leaving the prose to
    remember it. Computed by the same `significance_results` the main campaign
    uses, at the same representative load and the same overload point, so the
    counts are comparable by construction.
    """
    from plot_figures import pick_overload_load, significance_results

    sig = significance_results(rows, REPR_LOAD_OPS, pick_overload_load(rows))
    if not sig:
        return ["guest campaign yielded no paired tests"]
    macros["GuestNTests"] = str(len(sig))
    macros["GuestNSignificant"] = str(sum(1 for r in sig if r["holm"] < 0.05))
    macros["GuestNEqvUnresolved"] = str(sum(1 for r in sig if r["holm"] >= 0.05))
    # How many rows tab:equivalence actually shows. write_equivalence_table keeps
    # only the representative-load comparisons, so the family size and the table's
    # row count are different numbers and a sentence saying "N of the M rows" has
    # to use this one. Quoting GuestNTests there would name a denominator the
    # reader cannot count in the table in front of them.
    macros["GuestNEqvRows"] = str(
        sum(1 for r in sig if r.get("point", "repr") == "repr"))
    tail = [r["eqv"] for r in sig if r["kind"] == "tail"]
    if tail:
        macros["GuestEqvBoundTailMax"] = fmt(max(tail))
    return []


def throughput_facts(macros, rows):
    thr = {}
    for r in rows:
        thr.setdefault(int(r["rate"]) * r["producers"], []).append(r["throughput_ops_s"])
    loads = sorted(thr)
    tracking = [l for l in loads if statistics.median(thr[l]) >= 0.95 * l]
    macros["GuestTrackingLoad"] = fmt(max(tracking) / 1000.0)
    macros["GuestSatKnee"] = fmt(max(statistics.median(thr[l]) for l in loads) / 1000.0)

    top = max(loads)
    per = {}
    for r in rows:
        if int(r["rate"]) * r["producers"] == top:
            per.setdefault(r["lang"], []).append(r["throughput_ops_s"] / 1000.0)
    if "cpp" in per and "rust" in per:
        c, u = statistics.median(per["cpp"]), statistics.median(per["rust"])
        macros["GuestOverloadThrRatio"] = fmt(max(c, u) / min(c, u), 1)
    return []


def main():
    path = os.path.join(RESULTS, f"{GUEST}.jsonl")
    if not os.path.exists(path):
        sys.exit(f"missing {path}; the guest campaign is the subject of this script")
    rows = balance_repeats(load_campaign(path))

    macros, notes = {}, []
    macros["GuestRuns"] = str(len(rows))
    levels = len({int(r["rate"]) for r in rows})
    macros["GuestLoadLevels"] = str(levels)
    macros["GuestRepeats"] = str(len(rows) // (levels * len(variants(rows))))
    macros["GuestShards"] = str(rows[0]["shards"])
    macros["GuestProducers"] = str(rows[0]["producers"])

    notes += host_facts(macros)
    notes += instrument_facts(macros, rows)
    notes += resource_facts(macros, rows)
    notes += test_family_facts(macros, rows)
    notes += throughput_facts(macros, rows)

    out = os.path.join(ROOT, "figures", "gen_guest.tex")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("% Generated by bench/guest_facts.py -- do not edit by hand.\n")
        for k in sorted(macros):
            fh.write(f"\\newcommand{{\\{k}}}{{{macros[k]}}}\n")

    print(f"wrote {os.path.relpath(out, ROOT)} ({len(macros)} macros)")
    for k in sorted(macros):
        print(f"  {k} = {macros[k]}")
    for note in notes:
        print("  SKIP:", note, file=sys.stderr)


if __name__ == "__main__":
    main()
