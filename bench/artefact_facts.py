#!/usr/bin/env python3
"""Measure the artefact-level facts the thesis quotes outside the campaign.

The campaign numbers reach the prose through figures/gen_macros.tex and the
size proxies through figures/gen_complexity.tex. A third group was still typed
in by hand: record sizes, parity-suite coverage, the size of the conformance
campaign, and the size of the FFI seam. Each is a measurement, so each could go
stale silently the moment the code moved, which is what the no-transcription
rule exists to prevent. They are measured here and written to
figures/gen_artefacts.tex.

Six sources, none of them a campaign log:

  * record sizes   -- compiled and run: cpp/tools/layout_probe.cpp and
                      rust/examples/layout.rs report sizeof/size_of and, on the
                      C++ side, the field offsets the prose uses to explain the
                      padding.
  * coverage       -- cpp/results/coverage.csv and rust/results/coverage.csv,
                      written by cpp/coverage.sh and rust/coverage.sh.
  * conformance    -- spec/conformance/results/summary.json, written by
                      spec/conformance/run.sh.
  * FFI seam       -- counted from ffi/ source.
  * fault outcomes -- faults/results/taxonomy.csv and the runner's own logs: the
                      intermittent deadlock's detection rate, the lost-update
                      counts, and how many classes no C++ sanitiser reports.
  * suite size     -- cpp/tests and rust/tests, counted from source.

The last two joined this file in August 2026, after a grading pass found that
every one of the numbers they now produce had been typed into the prose by hand
and every one of them was wrong. That is the failure mode the whole file exists
to prevent, so they belong here rather than in a paragraph.

Missing inputs are reported and skipped rather than guessed, so a macro is
never invented; if a macro the thesis uses disappears, the LaTeX build fails
loudly, which is the intended failure mode.

Usage:
    python3 artefact_facts.py [--outdir ../figures] [--no-build]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

# The compared build's settings (cpp/CMakeLists.txt, rust/Cargo.toml). Layout is
# ABI-determined for C++ and compiler-chosen for Rust, and the Rust choice is the
# point of the comparison, so the probe is built the way the measured code is.
CXX_STD = "c++23"
CXX_OPT = "-O2"


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def parse_kv(text):
    out = {}
    for line in text.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            if v.strip().isdigit():
                out[k.strip()] = int(v)
    return out


def cpp_layout(root, build):
    """sizeof and offsetof for the C++ records, from the real headers."""
    exe = os.path.join(tempfile.mkdtemp(prefix="layout-"), "layout_probe")
    if build:
        run(["g++", f"-std={CXX_STD}", CXX_OPT, "-I", os.path.join(root, "cpp/include"),
             os.path.join(root, "cpp/tools/layout_probe.cpp"), "-o", exe])
    return parse_kv(run([exe]).stdout)


def rust_layout(root, build):
    """size_of for the Rust records, from the crate the campaign builds."""
    args = ["cargo", "run", "--release", "--quiet", "--example", "layout"]
    if not build:
        args = [os.path.join(root, "rust/target/release/examples/layout")]
    return parse_kv(run(args, cwd=os.path.join(root, "rust")).stdout)


def coverage_total(path, percent_column):
    """The TOTAL row of a coverage CSV, as written by the two coverage scripts."""
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["file"] == "TOTAL":
                return float(row[percent_column])
    raise SystemExit(f"artefact_facts.py: no TOTAL row in {path}")


def ffi_seam(root):
    """The size and width of the interoperability seam, counted from source.

    Entry points are counted by the attribute that makes them one, so adding a
    function to the seam moves the number in the thesis without anyone
    remembering to.
    """
    lib = os.path.join(root, "ffi/rust-uecm-ffi/src/lib.rs")
    hdr = os.path.join(root, "ffi/rust-uecm-ffi/include/uecm_ffi.h")
    with open(lib, encoding="utf-8") as fh:
        rust_src = fh.read()
    with open(hdr, encoding="utf-8") as fh:
        header_lines = len(fh.read().splitlines())
    code = "\n".join(ln for ln in rust_src.splitlines() if not ln.lstrip().startswith("//"))
    exported = len(re.findall(r'pub\s+(?:unsafe\s+)?extern\s+"C"\s+fn', code))
    unsafe_fns = len(re.findall(r'\bunsafe\s+(?:extern\s+"C"\s+)?fn\b', code))
    return {
        "lines": len(rust_src.splitlines()),
        "header_lines": header_lines,
        "entry_points": exported,
        "unsafe_fns": unsafe_fns,
    }


def thousands(n):
    """A count as the thesis sets it: thin space, not a comma, between groups."""
    return f"{n:,}".replace(",", "\\,")


def fault_facts(root):
    """Outcomes of the fault-injection catalogue, from the runner's own logs.

    Three quantities the prose quotes that no campaign log holds: how often
    ThreadSanitizer catches the intermittent lock-order inversion, how many
    increments each language's lost-update case drops, and how many classes no
    C++ sanitiser reports at all.

    The deadlock rate is taken twice and the two readings have to agree. The
    catalogue's own note field is the runner's summary, and the per-run logs are
    the evidence behind it; if a rerun ever leaves one stale the mismatch is an
    error here rather than a wrong number on the page.
    """
    results = os.path.join(root, "faults/results")
    taxonomy = os.path.join(results, "taxonomy.csv")
    with open(taxonomy, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    deadlock = next(r for r in rows if r["defect"] == "lock_order_deadlock")
    stated = re.search(r"TSan reported in (\d+)/(\d+) runs", deadlock["note"])
    if not stated:
        raise SystemExit(
            "artefact_facts.py: taxonomy.csv no longer records the deadlock "
            f"detection rate in its note field ({deadlock['note']!r})")
    hits, runs = int(stated.group(1)), int(stated.group(2))

    # The per-run logs, counted independently of the note.
    logs = sorted(glob.glob(os.path.join(results, "deadlock.tsan.log.run*")))
    if logs:
        counted = sum(
            1 for p in logs
            if "WARNING: ThreadSanitizer" in open(p, encoding="utf-8", errors="replace").read())
        if (counted, len(logs)) != (hits, runs):
            raise SystemExit(
                f"artefact_facts.py: the deadlock run logs report {counted}/{len(logs)} "
                f"but taxonomy.csv says {hits}/{runs}; rerun faults/run_faults.sh so "
                "the catalogue and its evidence agree before the thesis quotes either")

    # A class is untouched when no C++ sanitiser reports it at all. The
    # intermittently detected deadlock is deliberately not counted here: it is
    # detected, unreliably, which is a different claim and the thesis makes it
    # separately. A run that had to be killed still counts as untouched, since
    # "undetected (hung)" records how the run ended and not a report anyone got.
    undetected = [r["defect"] for r in rows
                  if r["cpp_detection"].startswith("undetected")]

    lost = {}
    for lang, stem in (("Rust", "lost_update.rust.log"), ("Cpp", "lost_update.tsan.log")):
        with open(os.path.join(results, stem), encoding="utf-8") as fh:
            text = fh.read()
        m = re.search(r"messages_handled=(\d+) expected=(\d+) lost=(\d+)", text)
        if not m:
            raise SystemExit(f"artefact_facts.py: no lost-update tally in {stem}")
        lost[lang] = tuple(int(g) for g in m.groups())
    if lost["Rust"][1] != lost["Cpp"][1]:
        raise SystemExit(
            "artefact_facts.py: the two lost-update runs expected different totals "
            f"({lost['Rust'][1]} vs {lost['Cpp'][1]}); the prose quotes one figure for both")

    macros = {
        "DeadlockTsanHits": hits,
        "DeadlockTsanRuns": runs,
        "FaultClasses": len(rows),
        "FaultClassesUndetected": len(undetected),
        "LostUpdateExpected": thousands(lost["Rust"][1]),
    }
    for lang, (handled, _, dropped) in lost.items():
        macros[f"LostUpdate{lang}Handled"] = thousands(handled)
        macros[f"LostUpdate{lang}Lost"] = thousands(dropped)
    return macros


def suite_sizes(root):
    """The parity suite as a count: C++ test binaries and Rust test functions.

    Only the integration tests under rust/tests are counted, which is what
    `cargo test --release` runs for the compared build. The three in
    rust/src/mutex_queue.rs belong to the specification section 12 attribution
    probe and compile only under `--features mutex-queue`, so counting them
    would report a configuration the campaign never measured.
    """
    binaries = glob.glob(os.path.join(root, "cpp/tests/test_*.cpp"))
    tests = 0
    for path in glob.glob(os.path.join(root, "rust/tests/*.rs")):
        with open(path, encoding="utf-8") as fh:
            tests += len(re.findall(r"^\s*#\[test\]", fh.read(), re.M))
    return {"CppTestBinaries": len(binaries), "RustTests": tests}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="../figures")
    ap.add_argument("--no-build", action="store_true",
                    help="reuse previously built probes instead of compiling them")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    outdir = args.outdir if os.path.isabs(args.outdir) else os.path.abspath(
        os.path.join(here, args.outdir))
    os.makedirs(outdir, exist_ok=True)
    build = not args.no_build

    macros = {}
    notes = []

    # -- record layout ------------------------------------------------------
    cpp = cpp_layout(root, build)
    rust = rust_layout(root, build)

    ctx_gap = cpp["ue_context_bytes"] - rust["ue_context_bytes"]
    key_end = cpp["off_security_key"] + 32
    macros.update({
        "CppUeCtxBytes": cpp["ue_context_bytes"],
        "RustUeCtxBytes": rust["ue_context_bytes"],
        "UeCtxGapBytes": ctx_gap,
        "CppUeCtxStatePad": cpp["off_serving_cell_id"] - (cpp["off_state"] + 1),
        "CppUeCtxKeyEnd": key_end,
        "CppUeCtxKeyPad": cpp["off_drbs"] - key_end,
        "CppRequestBytes": cpp["request_bytes"],
        "RustRequestBytes": rust["request_bytes"],
        "SignalingMsgBytes": cpp["signaling_msg_bytes"],
    })
    if cpp["signaling_msg_bytes"] != rust["signaling_msg_bytes"]:
        raise SystemExit(
            "artefact_facts.py: the signalling message differs in size between the "
            f"two implementations ({cpp['signaling_msg_bytes']} vs "
            f"{rust['signaling_msg_bytes']} bytes); the prose quotes one figure for both")

    # Two consequences of the layout difference that the prose derives rather
    # than measures. Deriving them here keeps the arithmetic tied to the sizes.
    sweep_ues = 5000
    macros["SweepUes"] = f"{sweep_ues // 1000}\\,000"
    macros["UeCtxGapTotalKB"] = f"{ctx_gap * sweep_ues / 1000:.0f}"

    default_shards, queue_cap = 8, 1024
    slots = default_shards * queue_cap
    macros["CppQueueResidentMB"] = f"{slots * cpp['request_bytes'] / 1e6:.1f}"
    macros["RustQueueResidentMB"] = f"{slots * rust['request_bytes'] / 1e6:.1f}"

    # -- parity-suite coverage ----------------------------------------------
    cpp_cov = os.path.join(root, "cpp/results/coverage.csv")
    rust_cov = os.path.join(root, "rust/results/coverage.csv")
    if os.path.exists(cpp_cov) and os.path.exists(rust_cov):
        macros["CppLineCov"] = f"{coverage_total(cpp_cov, 'percent'):.1f}"
        macros["RustLineCov"] = f"{coverage_total(rust_cov, 'line_percent'):.1f}"
        macros["RustRegionCov"] = f"{coverage_total(rust_cov, 'region_percent'):.1f}"
    else:
        notes.append("coverage CSVs missing; run cpp/coverage.sh and rust/coverage.sh")

    # -- conformance campaign size ------------------------------------------
    summary = os.path.join(root, "spec/conformance/results/summary.json")
    if os.path.exists(summary):
        with open(summary, encoding="utf-8") as fh:
            conf = json.load(fh)
        macros["ConfHandOps"] = f"{conf['model_checked_ops']}"
        # Rounded to thousands: the exact count depends on how many operations a
        # generated vector spends before hitting a terminal state, and the prose
        # says "roughly".
        macros["ConfGenOps"] = f"{round(conf['generated_ops'] / 1000)}\\,000"
    else:
        notes.append("no conformance summary; run spec/conformance/run.sh "
                     "--random 60 --ops 2000")

    # -- FFI seam ------------------------------------------------------------
    seam = ffi_seam(root)
    macros.update({
        "FfiSeamLines": seam["lines"],
        "FfiHeaderLines": seam["header_lines"],
        "FfiEntryPoints": seam["entry_points"],
        "FfiUnsafeFns": seam["unsafe_fns"],
    })

    # -- fault-injection outcomes and suite size -----------------------------
    faults = os.path.join(root, "faults/results/taxonomy.csv")
    if os.path.exists(faults):
        macros.update(fault_facts(root))
    else:
        notes.append("no fault catalogue; run faults/run_faults.sh")
    macros.update(suite_sizes(root))

    gen = os.path.join(outdir, "gen_artefacts.tex")
    with open(gen, "w", encoding="utf-8") as fh:
        fh.write("% Generated by bench/artefact_facts.py -- do not edit by hand.\n")
        for k, v in macros.items():
            fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

    print(f"C++  layout: {cpp}")
    print(f"Rust layout: {rust}")
    print(f"FFI seam   : {seam}")
    print("wrote", os.path.relpath(gen, here))
    for note in notes:
        print("  SKIP:", note, file=sys.stderr)


if __name__ == "__main__":
    main()
