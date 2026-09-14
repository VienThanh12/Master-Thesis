#!/usr/bin/env python3
"""Summarise a matched pair of jemalloc heap profiles into JSON (RQ3 attribution).

Split out of bench/alloc_profile.sh so it can be tested without jeprof installed.
These profiles can only be collected where a prof-enabled jemalloc exists, and the
run that collects them is the testbed visit, so the parsing has to be known-good
beforehand; `--self-test` checks it against jeprof's actual text output, including
the shapes that carry no site.

What it reads: `jeprof --text --show_bytes` output, whose rows are

    flat  flat%  sum%  cum  cum%  symbol

with byte counts in the flat and cum columns because of --show_bytes.

What it will not do: difference the two languages per symbol. C++ and Rust do not
share call sites, mangling, or inlining behaviour, so a per-symbol subtraction
would be arithmetic on unrelated rows. Each side gets its own ranking, and the
comparison is made on the totals.

Usage:
  parse_jeprof.py summarise <outdir>
  parse_jeprof.py --self-test
"""
import json
import os
import re
import sys

# flat, flat%, sum%, cum, cum%, symbol
ROW = re.compile(r"^\s*([\d.]+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)\s+([\d.]+)%\s+(\S.*)$")
TOTAL = re.compile(r"^Total:\s+([\d.]+)\s*(\S*)")


def parse_jeprof(text):
    """Return (sites sorted by flat bytes desc, reported total bytes or None)."""
    sites = []
    reported_total = None
    for line in text.splitlines():
        m = TOTAL.match(line.strip())
        if m:
            reported_total = float(m.group(1))
            continue
        m = ROW.match(line)
        if not m:
            continue
        flat, _flat_pct, _sum_pct, cum, _cum_pct, symbol = m.groups()
        sites.append({
            "bytes_flat": float(flat),
            "bytes_cum": float(cum),
            "symbol": symbol.strip(),
        })
    sites.sort(key=lambda s: -s["bytes_flat"])
    return sites, reported_total


def flat_is_degenerate(sites, threshold=0.99):
    """True when one symbol holds essentially all of the flat bytes.

    jemalloc 5.3 keeps its own backtrace frame at the leaf of every sampled
    stack, so depending on the unwinder the whole flat column can land on
    `prof_backtrace_impl` and every application site reads zero flat bytes. The
    totals are unaffected, since flat still sums to the sampled live heap, but
    the flat *ranking* then says nothing and the cumulative one has to be read
    instead. Detected rather than assumed, because which unwinder jemalloc picked
    is a property of how it was built.
    """
    total = sum(s["bytes_flat"] for s in sites)
    if total <= 0:
        return False
    return max(s["bytes_flat"] for s in sites) / total >= threshold


def peak_rss_kb(bench_json_path):
    """Peak RSS from the profiled run's own JSON line, if it produced one."""
    if not os.path.exists(bench_json_path):
        return None
    try:
        lines = [l for l in open(bench_json_path).read().splitlines() if l.strip()]
        return json.loads(lines[-1]).get("rss_peak_kb") if lines else None
    except (json.JSONDecodeError, OSError, IndexError):
        return None


def summarise(outdir, top=25):
    summary = {"langs": {}}
    for lang in ("cpp", "rust"):
        prof_path = os.path.join(outdir, f"{lang}.jeprof.txt")
        if not os.path.exists(prof_path):
            sys.exit(f"missing {prof_path}: both variants are needed to attribute a difference")
        sites, reported = parse_jeprof(open(prof_path).read())
        if not sites:
            sys.exit(f"{prof_path} contains no attributable sites; the profile is empty")
        summary["langs"][lang] = {
            "sampled_live_bytes": sum(s["bytes_flat"] for s in sites),
            "reported_total_bytes": reported,
            "n_sites": len(sites),
            "peak_rss_kb": peak_rss_kb(os.path.join(outdir, f"{lang}.bench.json")),
            "flat_ranking_degenerate": flat_is_degenerate(sites),
            "top_sites": sites[:top],
            "top_sites_cum": sorted(sites, key=lambda s: -s["bytes_cum"])[:top],
        }

    c, r = summary["langs"]["cpp"], summary["langs"]["rust"]
    if c["peak_rss_kb"] and r["peak_rss_kb"]:
        summary["peak_rss_delta_kb"] = r["peak_rss_kb"] - c["peak_rss_kb"]
    summary["sampled_live_delta_bytes"] = r["sampled_live_bytes"] - c["sampled_live_bytes"]

    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    for lang in ("cpp", "rust"):
        d = summary["langs"][lang]
        rss = f"{d['peak_rss_kb']} kB" if d["peak_rss_kb"] else "unknown"
        print(f"\n{lang}: peak RSS {rss}, "
              f"sampled live {d['sampled_live_bytes'] / 1024:.0f} kiB "
              f"across {d['n_sites']} sites")
        key = "bytes_flat"
        if d["flat_ranking_degenerate"]:
            key = "bytes_cum"
            print("    (flat column collapsed onto the allocator's own leaf frame,"
                  " so this ranking is cumulative)")
        for s in d[f"top_sites{'_cum' if key == 'bytes_cum' else ''}"][:8]:
            print(f"    {s[key] / 1024:10.0f} kiB  {s['symbol'][:68]}")

    if "peak_rss_delta_kb" in summary:
        print(f"\npeak RSS delta (rust - cpp): {summary['peak_rss_delta_kb']} kB")
    print("sampled live delta (rust - cpp): "
          f"{summary['sampled_live_delta_bytes'] / 1024:.0f} kiB")
    print("\nRead each ranking on its own and compare the totals. The two languages")
    print("share no call sites, so a per-symbol difference would subtract unrelated")
    print("rows from each other.")
    print(f"\nwrote {os.path.join(outdir, 'summary.json')}")


def self_test():
    # Real `jeprof --text --show_bytes` output: two "Using local file" banners, a
    # Total line, then rows. Includes a 0-byte row and a symbol containing spaces
    # and commas, which C++ template names always do.
    sample = """Using local file bench.
Using local file cpp.heap.
Total: 11534336 B
   4194304  36.4%  36.4%  4194304  36.4% std::vector<uecm::DrbEntry, std::allocator<uecm::DrbEntry> >::_M_realloc_insert
   2097152  18.2%  54.5%  6291456  54.5% uecm::ShardCore::create_context
   1048576   9.1%  63.6%  1048576   9.1% operator new(unsigned long)
         0   0.0%  63.6%  4194304  36.4% std::thread::_State_impl
"""
    sites, total = parse_jeprof(sample)
    assert total == 11534336, total
    assert len(sites) == 4, sites
    assert sites[0]["bytes_flat"] == 4194304
    assert "DrbEntry" in sites[0]["symbol"], sites[0]
    assert sites[0]["symbol"].endswith("_M_realloc_insert"), sites[0]
    assert sites[-1]["bytes_flat"] == 0.0, sites[-1]
    # Sorted by flat bytes descending.
    assert [s["bytes_flat"] for s in sites] == sorted(
        (s["bytes_flat"] for s in sites), reverse=True)
    # Banners must not be mistaken for sites.
    assert all("Using local file" not in s["symbol"] for s in sites)

    # Rust symbols and a hex-suffixed generic instantiation.
    rust = """Total: 8388608 B
   4194304  50.0%  50.0%  4194304  50.0% alloc::raw_vec::RawVec<T,A>::grow_amortized::h1a2b3c
   2097152  25.0%  75.0%  2097152  25.0% std::sys::pal::unix::thread::Thread::new
"""
    rsites, rtotal = parse_jeprof(rust)
    assert rtotal == 8388608 and len(rsites) == 2, (rtotal, rsites)
    assert rsites[0]["symbol"].startswith("alloc::raw_vec"), rsites[0]

    # No rows at all must be distinguishable from rows summing to zero.
    empty, etotal = parse_jeprof("Using local file bench.\nTotal: 0 B\n")
    assert empty == [] and etotal == 0.0, (empty, etotal)

    # A flat column that has collapsed onto the allocator's own leaf frame, which
    # is what jemalloc 5.3 produces under some unwinders. Every application site
    # reads zero flat bytes while the cumulative column still carries them, so the
    # ranking has to switch and the switch has to be detected.
    collapsed = """Total: 8208574 B
 8208574 100.0% 100.0%  8208574 100.0% prof_backtrace_impl
       0   0.0% 100.0%  5019291  61.1% uecm::ShardCore::create_context
       0   0.0% 100.0%  2949120  35.9% bench::HdrHistogram::HdrHistogram
"""
    csites, _ = parse_jeprof(collapsed)
    assert flat_is_degenerate(csites), csites
    assert not flat_is_degenerate(sites), sites
    assert not flat_is_degenerate([]), "no sites is not a collapsed column"
    by_cum = sorted(csites, key=lambda s: -s["bytes_cum"])
    assert by_cum[1]["symbol"].endswith("create_context"), by_cum

    print("parse_jeprof self-test: all checks pass")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "summarise":
        summarise(sys.argv[2])
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
