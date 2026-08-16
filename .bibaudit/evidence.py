#!/usr/bin/env python3
"""Run a batch of page-located searches over downloaded sources.

Usage: .evidence.py <batchname>
Each query prints the PDF page number and a snippet, so the resulting notes can
name the page an assertion was read from.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path("/tmp/srcs")

try:
    from pypdf import PdfReader
except ImportError:
    print("run with /tmp/.bibvenv/bin/python")
    raise

_cache = {}


def pages(name):
    if name not in _cache:
        r = PdfReader(SRC / name)
        out = []
        for p in r.pages:
            try:
                out.append(re.sub(r"[ \t]+", " ", p.extract_text() or ""))
            except Exception:
                out.append("")
        _cache[name] = out
    return _cache[name]


def grep(name, pattern, ctx=200, maxhits=3, label=""):
    print(f"\n### {label or pattern}  [{name}]")
    try:
        pgs = pages(name)
    except Exception as e:
        print(f"  ERROR opening: {e}")
        return
    rx = re.compile(pattern, re.I | re.S)
    n = 0
    for i, text in enumerate(pgs, 1):
        for m in rx.finditer(text):
            s, e = max(0, m.start() - ctx), min(len(text), m.end() + ctx)
            print(f"  p.{i}: ...{text[s:e].strip()}...".replace("\n", " | "))
            n += 1
            if n >= maxhits:
                return
    if n == 0:
        print("  NO MATCH")


def head(name, npages=1, chars=1200):
    print(f"\n### FRONT MATTER [{name}]")
    for i, text in enumerate(pages(name)[:npages], 1):
        print(f"  --- p.{i} ---")
        print("   " + text[:chars].replace("\n", " | "))


def txtgrep(name, pattern, ctx=250, maxhits=3, label=""):
    print(f"\n### {label or pattern}  [{name}]")
    raw = (SRC / name).read_text(errors="ignore")
    flat = re.sub(r"[ \t]+", " ", raw)
    rx = re.compile(pattern, re.I | re.S)
    n = 0
    for m in rx.finditer(flat):
        s, e = max(0, m.start() - ctx), min(len(flat), m.end() + ctx)
        # line number in original file
        line = raw[: m.start()].count("\n") + 1
        print(f"  line {line}: ...{flat[s:e].strip()}...".replace("\n", " | "))
        n += 1
        if n >= maxhits:
            return
    if n == 0:
        print("  NO MATCH")


BATCHES = {}


def batch(fn):
    BATCHES[fn.__name__] = fn
    return fn


@batch
def gpp():
    for f in ("ts38401_v1750.pdf", "ts38300_v1750.pdf", "ts38463_v1700.pdf", "tr38913_v1800.pdf"):
        head(f, 1, 900)
    grep("ts38401_v1750.pdf", r"gNB-CU-CP.{0,400}?gNB-CU-UP", 260, 2, "38.401 CU-CP/CU-UP split")
    grep("ts38401_v1750.pdf", r"E1 interface", 260, 2, "38.401 E1 interface")
    grep("ts38300_v1750.pdf", r"gNB-CU-CP", 260, 2, "38.300 CU-CP")
    grep("ts38463_v1700.pdf", r"E1AP|E1 Application Protocol", 200, 2, "38.463 scope")
    grep("tr38913_v1800.pdf", r"7\.4\s+Control plane latency", 320, 1, "38.913 clause 7.4")


@batch
def wg21():
    head("p3081r2.pdf", 1, 900)
    grep("p3081r2.pdf", r"deterministically decidable at compile time", 320, 2, "P3081R2 enforcement rule")
    grep("p3081r2.pdf", r"\b(type|bounds|lifetime|arithmetic)\b.{0,80}profile", 260, 3, "P3081R2 profile set")
    head("p3970r0.pdf", 1, 900)
    grep("p3970r0.pdf", r"experimental implementation", 400, 2, "P3970R0 implementation status")
    grep("p3970r0.pdf", r"concurrency profile", 320, 3, "P3970R0 concurrency profile deferred")
    txtgrep("p3390r0.html", r"borrow check", 260, 2, "Safe C++ borrow checking")


@batch
def usenix():
    head("nsdi06_schroeder.pdf", 1, 900)
    grep("nsdi06_schroeder.pdf", r"closed system|closed model", 300, 3, "open vs closed")
    head("nsdi20_firecracker.pdf", 1, 700)
    grep("nsdi20_firecracker.pdf", r"written in Rust|implemented in Rust", 300, 2, "Firecracker in Rust")
    head("osdi20_redleaf.pdf", 1, 700)
    grep("osdi20_redleaf.pdf", r"\bC\b.{0,60}(baseline|comparison)|DPDK", 260, 3, "RedLeaf C baselines")
    head("soups21_fulton.pdf", 1, 700)
    grep("soups21_fulton.pdf", r"learning curve|learn", 260, 3, "Fulton learning curve")
    head("atc24_rustforlinux.pdf", 1, 700)
    grep("atc24_rustforlinux.pdf", r"interoperability|interop", 260, 3, "Rust-for-Linux friction")
    head("atc25_converos.pdf", 1, 700)
    grep("atc25_converos.pdf", r"deadlock|data race", 300, 3, "Converos concurrency bugs reachable")


@batch
def lipics():
    head("ecoop23_morello.pdf", 1, 900)
    grep("ecoop23_morello.pdf", r"bounds check", 300, 3, "Morello bounds checks")
    head("ecrts25_asyncrust.pdf", 1, 900)
    grep("ecrts25_asyncrust.pdf", r"response.time analysis|bounded response", 300, 3, "async Rust response times")
    grep("ecrts25_asyncrust.pdf", r"maximize throughput rather than", 300, 2, "Tokio design goal")


@batch
def policy():
    head("oncd2024.pdf", 1, 700)
    grep("oncd2024.pdf", r"memory.safe programming language", 300, 3, "ONCD recommendation")
    head("cisa2023.pdf", 1, 700)
    grep("cisa2023.pdf", r"memory safe roadmap", 300, 3, "CISA roadmap")
    txtgrep("android2022.html", r"memory safe|memory-safe", 260, 3, "Android 13 memory-safe")
    txtgrep("android2025.html", r"20%|below 20|1000x|rollback", 260, 4, "Android 2025 numbers")


@batch
def misc():
    txtgrep("hdrhistogram.html", r"coordinated omission|dynamic range", 260, 3, "HdrHistogram")
    print("\n### lizard version [lizard_pypi.json]")
    j = json.loads((SRC / "lizard_pypi.json").read_text())
    print("   latest:", j["info"]["version"], "| releases incl 1.23.0:", "1.23.0" in j["releases"])
    txtgrep("alsoran_readme.md", r"gNodeB|CU-CP|E1", 260, 4, "Alsoran scope")
    head("cidr25_oltp.pdf", 1, 900)
    grep("cidr25_oltp.pdf", r"communication|isolation", 260, 3, "OLTP communication bottleneck")
    txtgrep("rfc3393.txt", r"ipdv|delay variation", 260, 3, "RFC 3393 PDV definition")


if __name__ == "__main__":
    for name in sys.argv[1:]:
        BATCHES[name]()
