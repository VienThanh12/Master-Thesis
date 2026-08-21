#!/usr/bin/env python3
"""Measure the adoption-cost axes RQ4 asks about and the FFI prototype does not answer.

RQ4 asks what incremental adoption costs in effort, interoperability and risk.
The seam measurement answers interoperability. Three axes were left unmeasured,
and each is the axis a build engineer asks about before any of the ones the
thesis already reports:

  * build time     -- the most cited practical objection to Rust adoption.
  * static footprint -- what the artefact costs on disk, beside peak RSS.
  * supply chain   -- how much third-party code, and how much `unsafe` inside it,
                      each configuration pulls in.

Two design rules carried over from the rest of the harness.

*One instrument, both languages.* The same clock, the same job count and the
same interleaving are applied to both build systems, for the reason `lizard`
measures both cores and jemalloc's own `prof` profiles both arms: a pair
measured by two tools cannot be differenced.

*Substitute everything the candidate mechanism covers.* Specification section 12
records two probes that varied a second thing along with the first and so proved
less than they appeared to. The footprint comparison here has exactly that
hazard: g++ resolves libstdc++ at run time while rustc links libstd into the
binary, so the shipped sizes differ by linkage policy before they differ by
language. Both policies are therefore measured on both sides, and the comparison
is read at matched policy.

Host sensitivity splits the axes, and the split is deliberate. Build time moves
with load, so it is recorded to bench/results/ and replayed from the record by
default: ffi/build.sh overwrote its own evidence once by being run merely to
check that it still worked, and a script the thesis refresh calls should not be
able to do that. Footprint and supply chain are deterministic given the
toolchain, so they are recomputed on every run and cannot go stale.

Note that bench/results/ is listed in .gitignore and the campaign records there
are tracked only because they were force-added. The adoption record needs the
same treatment, or a fresh clone has no build-time rows to replay.

Usage:
    python3 adoption_cost.py --measure [--repeats 15] [--jobs 14]
    python3 adoption_cost.py       # replay build time, remeasure the rest
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

# The compared build's settings (cpp/CMakeLists.txt, rust/Cargo.toml).
CXX_STD = "c++23"
CXX_OPT = "-O2"

# The executable measured for footprint. The conformance runner is the tightest
# matched pair in the repository: the specification defines it, both languages
# build one, their transcripts agree byte for byte, and neither side pulls a
# dev-dependency to produce it. The benchmark binaries are the obvious
# alternative and are the wrong choice -- the C++ one compiles a header-only HDR
# histogram while the Rust one links the `hdrhistogram` crate and its transitive
# tree, so their sizes would differ by that asymmetry as well as by language.
FOOTPRINT_TARGET = "conformance_runner"

# Touched to provoke an incremental rebuild. The C++ side gets two cases because
# its recompilation granularity depends on which file moved, which is the whole
# point of the comparison; Rust has one case because the crate is the unit.
CPP_TU = "src/shard_core.cpp"
CPP_HEADER = "include/uecm/shard_core.hpp"
RUST_UNIT = "src/shard_core.rs"


class Timer:
    """Wall clock and child CPU time for one command.

    CPU time is the primitive the decomposition below relies on: it is additive
    across parallel work where wall clock is not, and it is the more stable of
    the two on a host running anything else.
    """

    def __init__(self):
        self.wall = 0.0
        self.cpu = 0.0

    def run(self, cmd, cwd=None, env=None):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        self.wall = time.perf_counter() - t0
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.cpu = ((after.ru_utime - before.ru_utime)
                    + (after.ru_stime - before.ru_stime))
        if proc.returncode != 0:
            raise SystemExit(
                f"adoption_cost.py: command failed ({' '.join(cmd)}):\n"
                f"{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        return self


def timed(cmd, cwd=None, env=None):
    t = Timer()
    t.run(cmd, cwd=cwd, env=env)
    return {"wall": t.wall, "cpu": t.cpu}


# ---------------------------------------------------------------------------
# Build time
# ---------------------------------------------------------------------------

def cmake_configure(root, builddir):
    return timed(["cmake", "-S", os.path.join(root, "cpp"), "-B", builddir,
                  "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"])


def cpp_build(builddir, jobs, target=None):
    cmd = ["cmake", "--build", builddir, "-j", str(jobs)]
    if target:
        cmd += ["--target", target]
    return timed(cmd)


def cargo(root, args, jobs, targetdir, env=None):
    # Incremental compilation is pinned off rather than left to the default.
    # Cargo disables it for release profiles today, but the first-party figure
    # below is only a from-scratch crate compile while that holds, and a default
    # is not a control.
    full = dict(env or os.environ, CARGO_INCREMENTAL="0")
    return timed(["cargo"] + args + ["-j", str(jobs), "--target-dir", targetdir],
                 cwd=os.path.join(root, "rust"), env=full)


def touch(path):
    """Move mtime forward without editing the file.

    A whole second, because ninja and cargo both compare timestamps and a
    sub-second bump can land inside the resolution the filesystem reports.
    """
    now = time.time() + 1
    os.utime(path, (now, now))


def touch_tree(root_dir):
    for dirpath, _, names in os.walk(root_dir):
        for name in names:
            if name.endswith(".rs"):
                touch(os.path.join(dirpath, name))


def measure_build_times(root, repeats, jobs, warmup=1, verbose=True):
    """One interleaved repeat measures every scope in both languages.

    Interleaving rather than batching, for the reason campaign.sh interleaves:
    thermal and background drift then lands on both arms of a comparison instead
    of biasing whichever ran second.

    The first repeats are discarded, for the reason the campaign discards its
    first operations: a compiler reads its own headers and standard library off
    disk, so the first pass measures the page cache as much as the toolchain. The
    effect is large enough to see, roughly half again on a clean C++ build here.
    """
    samples = []
    cpp_dir = os.path.join(root, "cpp")
    for i in range(warmup + repeats):
        if verbose:
            label = ("warm-up" if i < warmup
                     else f"repeat {i - warmup + 1}/{repeats}")
            print(f"  {label}", flush=True)
        rec = {}
        with tempfile.TemporaryDirectory(prefix="adopt-cpp-") as cb, \
             tempfile.TemporaryDirectory(prefix="adopt-rust-") as rparent:
            # Cargo writes CACHEDIR.TAG only into a target directory it created
            # itself, and refuses to clean one without the tag, so the path is
            # handed over unmade rather than pre-created here.
            rb = os.path.join(rparent, "target")

            # -- scope A: the core library alone, clean ----------------------
            # The matched scope. Both sides compile first-party source only:
            # the C++ library has no dependency beyond the standard library and
            # the default Rust build is dependency-free, so nothing third-party
            # is inside either number. This is also the file set complexity.py
            # measures, so the size proxies and this describe the same code.
            rec["cpp_configure"] = cmake_configure(root, cb)
            rec["cpp_lib_clean"] = cpp_build(cb, jobs, "uecm")
            rec["rust_lib_clean"] = cargo(root, ["build", "--release", "--lib"],
                                          jobs, rb)

            # -- scope B: everything the default build produces --------------
            # Not a matched scope, and reported as such: the target sets differ
            # and the Rust side compiles its dev-dependency tree here.
            rec["cpp_all_clean"] = cpp_build(cb, jobs)
            timed(["cargo", "clean", "--target-dir", rb],
                  cwd=os.path.join(root, "rust"))
            rec["rust_all_clean"] = cargo(
                root, ["build", "--release", "--all-targets"], jobs, rb)

            # First-party alone, with the dependency tree left warm. The
            # difference against the line above is what the ecosystem costs,
            # which is a separate question from what the compiler costs, and it
            # is the decomposition the "Rust is slow to compile" objection needs.
            #
            # Every crate source is touched rather than cleaned: `cargo clean -p`
            # matched the path package and removed nothing here, which recorded a
            # no-op build as the first-party cost. Touching is also the operation
            # whose meaning does not depend on a cargo version.
            touch_tree(os.path.join(root, "rust", "src"))
            rec["rust_all_firstparty"] = cargo(
                root, ["build", "--release", "--all-targets"], jobs, rb)

            # -- scope C: incremental ----------------------------------------
            # C++ recompiles the translation units affected by the file that
            # moved, so a source file and a widely included header are different
            # cases and both are measured. Rust recompiles the crate whichever
            # file moved, so it has one case.
            touch(os.path.join(cpp_dir, CPP_TU))
            rec["cpp_inc_tu"] = cpp_build(cb, jobs)
            touch(os.path.join(cpp_dir, CPP_HEADER))
            rec["cpp_inc_header"] = cpp_build(cb, jobs)
            touch(os.path.join(root, "rust", RUST_UNIT))
            rec["rust_inc"] = cargo(
                root, ["build", "--release", "--all-targets"], jobs, rb)

        if i >= warmup:
            samples.append(rec)
    return samples


# ---------------------------------------------------------------------------
# Static footprint
# ---------------------------------------------------------------------------

def section_sizes(path):
    """text/data/bss from size(1), plus the file's own size on disk."""
    out = subprocess.run(["size", path], capture_output=True, text=True,
                         check=True).stdout.splitlines()
    text, data, bss = (int(x) for x in out[1].split()[:3])
    with tempfile.TemporaryDirectory(prefix="strip-") as td:
        stripped = os.path.join(td, os.path.basename(path))
        shutil.copy2(path, stripped)
        subprocess.run(["strip", "--strip-all", stripped], check=True,
                       capture_output=True)
        stripped_bytes = os.path.getsize(stripped)
    return {
        "bytes": os.path.getsize(path),
        "stripped": stripped_bytes,
        "text": text,
        "data": data,
        "bss": bss,
        "dynamic": dynamic_deps(path),
    }


def dynamic_deps(path):
    """Shared objects the binary resolves at run time, excluding the loader."""
    out = subprocess.run(["ldd", path], capture_output=True, text=True).stdout
    names = []
    for line in out.splitlines():
        name = line.strip().split(" ")[0]
        if name and not name.startswith(("linux-vdso", "/lib64/ld-")):
            names.append(name)
    return sorted(names)


def measure_footprint(root, jobs):
    """The matched executable pair under both linkage policies.

    Four builds rather than two. Reading the shipped pair alone would report the
    toolchains' differing defaults as a language difference: g++ leaves libstdc++
    to the dynamic loader and rustc links libstd in, so most of the gap between
    the two shipped binaries is that choice. Measuring each language under the
    other's policy is what separates the two.
    """
    out = {}
    with tempfile.TemporaryDirectory(prefix="fp-cpp-") as cb, \
         tempfile.TemporaryDirectory(prefix="fp-rust-") as rparent:
        rb = os.path.join(rparent, "target")
        cmake_configure(root, cb)
        cpp_build(cb, jobs, FOOTPRINT_TARGET)
        out["cpp_dynamic_std"] = section_sizes(os.path.join(cb, FOOTPRINT_TARGET))

        # The same sources and flags, with the standard library linked in.
        # Built directly rather than through a cmake option, because adding one
        # would put a configuration in the build system that no reported arm uses.
        cpp = os.path.join(root, "cpp")
        exe = os.path.join(cb, "conformance_runner_static")
        subprocess.run(
            ["g++", f"-std={CXX_STD}", CXX_OPT, "-DNDEBUG",
             "-I", os.path.join(cpp, "include"),
             os.path.join(cpp, "tools/conformance_runner.cpp"),
             os.path.join(cpp, "src/shard_core.cpp"),
             os.path.join(cpp, "src/service.cpp"),
             "-static-libstdc++", "-static-libgcc", "-lpthread", "-o", exe],
            check=True, capture_output=True)
        out["cpp_static_std"] = section_sizes(exe)
        out["cpp_static_locale"] = locale_share(exe)

        cargo(root, ["build", "--release", "--bin", FOOTPRINT_TARGET], jobs, rb)
        out["rust_static_std"] = section_sizes(
            os.path.join(rb, "release", FOOTPRINT_TARGET))

        env = dict(os.environ, RUSTFLAGS="-C prefer-dynamic")
        cargo(root, ["build", "--release", "--bin", FOOTPRINT_TARGET], jobs,
              rb + "-dyn", env=env)
        out["rust_dynamic_std"] = section_sizes(
            os.path.join(rb + "-dyn", "release", FOOTPRINT_TARGET))

    # What each dynamically linked binary leaves outside itself. Without these
    # the dynamic rows would invite the reading that the standard library is
    # free, and the two libraries are not the same size, so which policy looks
    # cheaper depends on whether the host already carries the library.
    out["shared_std"] = {
        "libstdcxx": shared_lib_size("libstdc++.so.6"),
        "libstd_rust": rust_libstd_size(),
    }
    return out


# The facets libstdc++'s locale machinery references, which a static link pulls
# in as a set rather than as the parts a program uses. Named explicitly because
# the footprint ordering below reverses on them, and an unexplained reversal is
# an invitation to disbelieve the whole row.
LOCALE_SYMS = re.compile(
    r"locale|iostream|ios_base|num_put|num_get|money_|time_get|time_put|"
    r"codecvt|ctype|messages_")


def locale_share(path):
    """The share of a binary's sized symbols that is locale and stream machinery.

    Measured rather than argued: `conformance_runner` parses and prints, so a
    static libstdc++ link brings the whole facet table with it, including the
    money, date and wide-character facets the program never instantiates.
    """
    out = subprocess.run(["nm", "-S", "-C", path], capture_output=True,
                         text=True).stdout
    total = matched = 0
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        try:
            size = int(parts[1], 16)
        except ValueError:
            continue
        total += size
        if LOCALE_SYMS.search(line):
            matched += size
    if total == 0:
        return None
    return {"total": total, "locale": matched,
            "percent": 100.0 * matched / total}


def shared_lib_size(soname):
    """On-disk size of a system shared object, resolved the way the loader would."""
    out = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if soname in line and "=>" in line:
            path = line.split("=>")[-1].strip()
            if os.path.exists(path):
                return {"path": path, "bytes": os.path.getsize(os.path.realpath(path))}
    return None


def rust_libstd_size():
    """On-disk size of the shared libstd a prefer-dynamic build resolves."""
    libdir = subprocess.run(["rustc", "--print", "target-libdir"],
                            capture_output=True, text=True, check=True).stdout.strip()
    hits = sorted(glob.glob(os.path.join(libdir, "libstd-*.so")))
    if not hits:
        return None
    return {"path": hits[0], "bytes": os.path.getsize(hits[0])}


# ---------------------------------------------------------------------------
# Supply chain
# ---------------------------------------------------------------------------

# Counts `unsafe` where it weakens a guarantee: a block, an fn, an impl, or a
# trait. `unsafe` inside a string or a comment does not, so line comments are
# stripped first. The figure is a magnitude and is reported as one: it is not an
# audit, and a crate that concentrates its `unsafe` in one large block scores
# lower than one that spreads the same work over many small ones.
UNSAFE_RE = re.compile(r"\bunsafe\s*(\{|fn\b|impl\b|trait\b|extern\b)")


def crates_for(root, args, with_dev, ships_only=False):
    """The transitive crates a configuration resolves, from Cargo.lock.

    cargo metadata rather than a Cargo.toml read, so the answer includes the
    transitive tree and matches what cargo would actually build.

    Dev-dependencies are taken at the root only, because that is what cargo
    builds: a dependency's own dev-dependencies never enter the graph. Counting
    them transitively would inflate the harness figure with crates no build of
    this repository ever compiles.

    `ships_only` drops build-dependencies. The two counts answer different
    questions and RQ4 asks both: a build-dependency contributes no instruction to
    the artefact but does execute on the build machine, which is the supply-chain
    exposure the runtime figure misses.
    """
    out = subprocess.run(
        ["cargo", "metadata", "--format-version", "1", "--filter-platform",
         host_triple()] + args,
        cwd=os.path.join(root, "rust"), capture_output=True, text=True,
        check=True).stdout
    meta = json.loads(out)
    resolve = {n["id"]: n for n in meta["resolve"]["nodes"]}
    packages = {p["id"]: p for p in meta["packages"]}
    root_id = meta["resolve"]["root"]

    # cargo reports a normal dependency with a null kind, so it is normalised
    # here; matching on the raw value silently accepts nothing.
    def kinds_of(dep):
        return {d["kind"] or "normal" for d in dep["dep_kinds"]}

    base = {"normal"} if ships_only else {"normal", "build"}
    seen, stack = set(), [(root_id, True)]
    while stack:
        cur, is_root = stack.pop()
        wanted = base | ({"dev"} if is_root and with_dev else set())
        for dep in resolve.get(cur, {"deps": []})["deps"]:
            if not kinds_of(dep) & wanted:
                continue
            if dep["pkg"] not in seen:
                seen.add(dep["pkg"])
                stack.append((dep["pkg"], False))
    return sorted(packages[i]["name"] + " " + packages[i]["version"] for i in seen), \
        {i: packages[i] for i in seen}


def host_triple():
    out = subprocess.run(["rustc", "-vV"], capture_output=True, text=True,
                         check=True).stdout
    for line in out.splitlines():
        if line.startswith("host:"):
            return line.split()[1]
    raise SystemExit("adoption_cost.py: rustc -vV reported no host triple")


def count_unsafe(pkgs):
    """`unsafe` occurrences across the resolved sources of a set of packages."""
    total, files, missing = 0, 0, []
    for pid, pkg in pkgs.items():
        src = os.path.dirname(pkg["manifest_path"])
        if not os.path.isdir(src):
            missing.append(pkg["name"])
            continue
        for dirpath, _, names in os.walk(src):
            for name in names:
                if not name.endswith(".rs"):
                    continue
                files += 1
                with open(os.path.join(dirpath, name), encoding="utf-8",
                          errors="replace") as fh:
                    body = "\n".join(
                        ln.split("//")[0] for ln in fh.read().splitlines())
                total += len(UNSAFE_RE.findall(body))
    return {"unsafe": total, "files": files, "missing_sources": missing}


def measure_supply_chain(root):
    out = {}
    # The three configurations the study actually builds, in the order a reader
    # meets them: the component compared in Chapter 7, the same component with
    # the matched allocator linked, and the benchmark harness that produced the
    # campaign.
    configs = {
        "core": (["--no-default-features"], False),
        "jemalloc": (["--features", "jemalloc"], False),
        "harness": ([], True),
    }
    for label, (cargo_args, with_dev) in configs.items():
        names, pkgs = crates_for(root, cargo_args, with_dev)
        ships, _ = crates_for(root, cargo_args, with_dev, ships_only=True)
        rec = {"crates": len(names), "names": names,
               "shipping_crates": len(ships),
               "build_only_crates": len(names) - len(ships)}
        rec.update(count_unsafe(pkgs))
        out[label] = rec

    # The compared core's own `unsafe`, for the same rule applied to first-party
    # code. Zero here is what makes the dependency figure meaningful: a core with
    # no dependencies and no `unsafe` has no unaudited surface at all.
    core_src = os.path.join(root, "rust/src")
    total = 0
    for dirpath, _, names in os.walk(core_src):
        for name in names:
            if name.endswith(".rs"):
                with open(os.path.join(dirpath, name), encoding="utf-8") as fh:
                    body = "\n".join(
                        ln.split("//")[0] for ln in fh.read().splitlines())
                total += len(UNSAFE_RE.findall(body))
    out["first_party_unsafe"] = total
    return out


# ---------------------------------------------------------------------------
# Reduction and output
# ---------------------------------------------------------------------------

def med(samples, key, field):
    return statistics.median(s[key][field] for s in samples)


def spread(samples, key, field):
    vals = sorted(s[key][field] for s in samples)
    return vals[0], vals[-1]


def fmt_s(v):
    return f"{v:.1f}" if v >= 1 else f"{v:.2f}"


def fmt_kb(v):
    return f"{v / 1024:.0f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true",
                    help="run the builds (host-sensitive); otherwise regenerate "
                         "from the newest record in bench/results/")
    ap.add_argument("--repeats", type=int, default=15,
                    help="interleaved repeats of the build-time measurement")
    ap.add_argument("--warmup", type=int, default=1,
                    help="repeats run and discarded before recording, so the "
                         "page cache is warm for the ones that count")
    ap.add_argument("--jobs", type=int, default=0,
                    help="parallel jobs for both build systems (default: all CPUs)")
    ap.add_argument("--outdir", default="../figures")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    outdir = args.outdir if os.path.isabs(args.outdir) else os.path.abspath(
        os.path.join(here, args.outdir))
    os.makedirs(outdir, exist_ok=True)
    results = os.path.join(here, "results")

    for tool in ("cmake", "ninja", "cargo", "g++", "size", "strip", "ldd"):
        if shutil.which(tool) is None:
            raise SystemExit(f"adoption_cost.py: {tool} not on PATH")

    if args.measure:
        jobs = args.jobs or os.cpu_count() or 1
        print(f"== measuring build time, {args.repeats} interleaved repeats "
              f"after {args.warmup} discarded, -j{jobs} ==")
        samples = measure_build_times(root, args.repeats, jobs, args.warmup)
        record = {
            "jobs": jobs,
            "repeats": args.repeats,
            "warmup": args.warmup,
            "host": {
                "cpus": os.cpu_count(),
                "gxx": subprocess.run(["g++", "-dumpversion"], text=True,
                                      capture_output=True).stdout.strip(),
                "rustc": subprocess.run(["rustc", "--version"], text=True,
                                        capture_output=True).stdout.strip(),
            },
            "build_time": samples,
        }
        os.makedirs(results, exist_ok=True)
        path = os.path.join(results,
                            f"adoption-{time.strftime('%Y%m%d-%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)
        print("wrote", os.path.relpath(path, here))
    else:
        found = sorted(glob.glob(os.path.join(results, "adoption-*.json")))
        if not found:
            print("adoption_cost.py: no adoption-*.json record in bench/results/; "
                  "run with --measure", file=sys.stderr)
            return 1
        path = found[-1]
        with open(path, encoding="utf-8") as fh:
            record = json.load(fh)
        print(f"regenerating from {os.path.relpath(path, here)} "
              f"({record['repeats']} repeats, -j{record['jobs']})")

    samples = record["build_time"]
    # Both of these are recomputed on every run rather than read from the
    # record, because both are deterministic given the toolchain: the footprint
    # is the same four binaries every time and the supply chain comes from
    # Cargo.lock. Only build time is host-sensitive, so only build time is
    # recorded and replayed.
    print("== measuring static footprint under both linkage policies ==")
    fp = measure_footprint(root, args.jobs or os.cpu_count() or 1)
    chain = measure_supply_chain(root)

    # -- build-time reductions ---------------------------------------------
    lib_cpp_w = med(samples, "cpp_lib_clean", "wall")
    lib_rust_w = med(samples, "rust_lib_clean", "wall")
    lib_cpp_c = med(samples, "cpp_lib_clean", "cpu")
    lib_rust_c = med(samples, "rust_lib_clean", "cpu")
    all_cpp_w = med(samples, "cpp_all_clean", "wall")
    all_rust_w = med(samples, "rust_all_clean", "wall")
    all_cpp_c = med(samples, "cpp_all_clean", "cpu")
    all_rust_c = med(samples, "rust_all_clean", "cpu")
    fp_rust_c = med(samples, "rust_all_firstparty", "cpu")
    fp_rust_w = med(samples, "rust_all_firstparty", "wall")
    inc_tu = med(samples, "cpp_inc_tu", "wall")
    inc_hdr = med(samples, "cpp_inc_header", "wall")
    inc_rust = med(samples, "rust_inc", "wall")
    configure = med(samples, "cpp_configure", "wall")

    rows = [
        ("\\multicolumn{3}{@{}l}{\\emph{Clean build, core library only "
         "(first-party source on both sides)}}", "", ""),
        ("\\quad Wall clock (s)", fmt_s(lib_cpp_w), fmt_s(lib_rust_w)),
        ("\\quad CPU time (s)", fmt_s(lib_cpp_c), fmt_s(lib_rust_c)),
        ("\\multicolumn{3}{@{}l}{\\emph{Clean build, every default target}}", "", ""),
        ("\\quad Wall clock (s)", fmt_s(all_cpp_w), fmt_s(all_rust_w)),
        ("\\quad CPU time (s)", fmt_s(all_cpp_c), fmt_s(all_rust_c)),
        ("\\quad CPU time, first-party only (s)", fmt_s(all_cpp_c),
         fmt_s(fp_rust_c)),
        ("\\multicolumn{3}{@{}l}{\\emph{Incremental rebuild after one edit}}",
         "", ""),
        ("\\quad Source file changed (s)", fmt_s(inc_tu), fmt_s(inc_rust)),
        ("\\quad Core header changed (s)", fmt_s(inc_hdr), fmt_s(inc_rust)),
        ("\\multicolumn{3}{@{}l}{\\emph{Static footprint, \\texttt{"
         + FOOTPRINT_TARGET.replace("_", "\\_") + "} (KiB)}}", "", ""),
        ("\\quad Shipped, each toolchain's default linkage",
         fmt_kb(fp["cpp_dynamic_std"]["bytes"]),
         fmt_kb(fp["rust_static_std"]["bytes"])),
        ("\\quad Matched: standard library linked statically",
         fmt_kb(fp["cpp_static_std"]["bytes"]),
         fmt_kb(fp["rust_static_std"]["bytes"])),
        ("\\quad Matched: standard library resolved dynamically",
         fmt_kb(fp["cpp_dynamic_std"]["bytes"]),
         fmt_kb(fp["rust_dynamic_std"]["bytes"])),
        ("\\quad Shared standard library left on the host",
         fmt_kb(fp["shared_std"]["libstdcxx"]["bytes"]),
         fmt_kb(fp["shared_std"]["libstd_rust"]["bytes"])),
        ("\\multicolumn{3}{@{}l}{\\emph{Third-party code resolved}}", "", ""),
        ("\\quad Transitive crates, compared component", "0",
         f"{chain['core']['crates']}"),
        ("\\quad Transitive crates, matched-allocator arm", "0",
         f"{chain['jemalloc']['crates']}"),
        ("\\quad Transitive crates, benchmark harness", "0",
         f"{chain['harness']['crates']}"),
        ("\\quad \\texttt{unsafe} sites in that third-party code", "---",
         f"{chain['harness']['unsafe']}"),
    ]
    # A section-heading row is a single \multicolumn spanning the table, so it
    # must not carry the two value columns as well; emitting them would add
    # cells past the column specification and LaTeX would refuse the row.
    def render(a, b, c):
        return a if (b == "" and c == "") else f"{a} & {b} & {c}"

    tab = os.path.join(outdir, "tab_adoption.tex")
    with open(tab, "w", encoding="utf-8") as fh:
        fh.write(" \\\\\n".join(render(*r) for r in rows) + "\n")

    macros = {
        "AdoptRepeats": record["repeats"],
        "AdoptJobs": record["jobs"],
        # Core library, the matched scope.
        "BuildLibCppWall": fmt_s(lib_cpp_w),
        "BuildLibRustWall": fmt_s(lib_rust_w),
        "BuildLibCppCpu": fmt_s(lib_cpp_c),
        "BuildLibRustCpu": fmt_s(lib_rust_c),
        "BuildLibWallRatio": f"{lib_cpp_w / lib_rust_w:.1f}",
        "BuildLibCpuRatio": f"{lib_rust_c / lib_cpp_c:.1f}",
        "BuildLibWallFaster": "Rust" if lib_rust_w < lib_cpp_w else "C++",
        "BuildLibCpuCheaper": "C++" if lib_cpp_c < lib_rust_c else "Rust",
        # Full build.
        "BuildAllCppWall": fmt_s(all_cpp_w),
        "BuildAllRustWall": fmt_s(all_rust_w),
        "BuildAllCppCpu": fmt_s(all_cpp_c),
        "BuildAllRustCpu": fmt_s(all_rust_c),
        "BuildAllCpuRatio": f"{all_rust_c / all_cpp_c:.1f}",
        "BuildAllFirstPartyCpu": fmt_s(fp_rust_c),
        "BuildAllFirstPartyWall": fmt_s(fp_rust_w),
        "BuildDepShareCpu": f"{100 * (1 - fp_rust_c / all_rust_c):.0f}",
        "BuildAllFirstPartyCpuRatio": f"{fp_rust_c / all_cpp_c:.1f}",
        # Incremental.
        "BuildIncCppTu": fmt_s(inc_tu),
        "BuildIncCppHeader": fmt_s(inc_hdr),
        "BuildIncRust": fmt_s(inc_rust),
        "BuildIncTuRatio": f"{inc_rust / inc_tu:.1f}",
        "BuildIncHeaderRatio": f"{inc_hdr / inc_rust:.1f}",
        "BuildConfigure": fmt_s(configure),
        # Footprint, in KiB, and the ratios at matched policy.
        "FootTarget": FOOTPRINT_TARGET.replace("_", "\\_"),
        "FootCppShipped": fmt_kb(fp["cpp_dynamic_std"]["bytes"]),
        "FootRustShipped": fmt_kb(fp["rust_static_std"]["bytes"]),
        "FootShippedRatio":
            f"{fp['rust_static_std']['bytes'] / fp['cpp_dynamic_std']['bytes']:.1f}",
        "FootCppStatic": fmt_kb(fp["cpp_static_std"]["bytes"]),
        "FootRustStatic": fmt_kb(fp["rust_static_std"]["bytes"]),
        "FootStaticRatio":
            f"{fp['rust_static_std']['bytes'] / fp['cpp_static_std']['bytes']:.1f}",
        "FootCppDynamic": fmt_kb(fp["cpp_dynamic_std"]["bytes"]),
        "FootRustDynamic": fmt_kb(fp["rust_dynamic_std"]["bytes"]),
        "FootDynamicRatio":
            f"{fp['rust_dynamic_std']['bytes'] / fp['cpp_dynamic_std']['bytes']:.1f}",
        # The share of each self-contained binary that is its standard library,
        # which is what the two matched rows disagree about.
        "FootRustStdShare": f"{100 * (1 - (fp['rust_dynamic_std']['bytes'] / fp['rust_static_std']['bytes'])):.0f}",
        "FootCppStdShare": f"{100 * (1 - (fp['cpp_dynamic_std']['bytes'] / fp['cpp_static_std']['bytes'])):.0f}",
        "FootSharedCpp": fmt_kb(fp["shared_std"]["libstdcxx"]["bytes"]),
        "FootSharedRust": fmt_kb(fp["shared_std"]["libstd_rust"]["bytes"]),
        # Named so the prose can say which way the ordering goes at each matched
        # policy without either name being typed in by hand.
        "FootStaticSmaller":
            "Rust" if fp["rust_static_std"]["bytes"] < fp["cpp_static_std"]["bytes"] else "C++",
        "FootDynamicSmaller":
            "Rust" if fp["rust_dynamic_std"]["bytes"] < fp["cpp_dynamic_std"]["bytes"] else "C++",
        "FootStaticRatioAbs":
            f"{max(fp['rust_static_std']['bytes'], fp['cpp_static_std']['bytes']) / min(fp['rust_static_std']['bytes'], fp['cpp_static_std']['bytes']):.1f}",
        "FootCppLocaleShare": f"{fp['cpp_static_locale']['percent']:.0f}",
        # Supply chain.
        "DepsCore": chain["core"]["crates"],
        "DepsJemalloc": chain["jemalloc"]["crates"],
        "DepsHarness": chain["harness"]["crates"],
        "DepsUnsafeJemalloc": chain["jemalloc"]["unsafe"],
        "DepsUnsafeHarness": chain["harness"]["unsafe"],
        "CoreUnsafe": chain["first_party_unsafe"],
        # Of the allocator arm's crates, the ones that reach the artefact against
        # the ones that only run while it is built.
        "DepsJemallocShipping": chain["jemalloc"]["shipping_crates"],
        "DepsJemallocBuildOnly": chain["jemalloc"]["build_only_crates"],
        "DepsHarnessShipping": chain["harness"]["shipping_crates"],
        "DepsHarnessBuildOnly": chain["harness"]["build_only_crates"],
    }
    gen = os.path.join(outdir, "gen_adoption.tex")
    with open(gen, "w", encoding="utf-8") as fh:
        fh.write("% Generated by bench/adoption_cost.py -- do not edit by hand.\n")
        for k, v in macros.items():
            fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

    print()
    print(f"core library clean : C++ {fmt_s(lib_cpp_w)} s wall / "
          f"{fmt_s(lib_cpp_c)} s CPU, Rust {fmt_s(lib_rust_w)} / {fmt_s(lib_rust_c)}")
    print(f"all targets clean  : C++ {fmt_s(all_cpp_w)} / {fmt_s(all_cpp_c)}, "
          f"Rust {fmt_s(all_rust_w)} / {fmt_s(all_rust_c)} "
          f"({macros['BuildDepShareCpu']}% of Rust CPU is dependencies)")
    print(f"incremental        : C++ {fmt_s(inc_tu)} s (source) / "
          f"{fmt_s(inc_hdr)} s (header), Rust {fmt_s(inc_rust)} s")
    print(f"footprint (KiB)    : shipped C++ {macros['FootCppShipped']} vs Rust "
          f"{macros['FootRustShipped']} ({macros['FootShippedRatio']}x); at matched "
          f"static linkage {macros['FootStaticRatio']}x, dynamic "
          f"{macros['FootDynamicRatio']}x")
    print(f"supply chain       : crates {chain['core']['crates']} core / "
          f"{chain['jemalloc']['crates']} jemalloc / {chain['harness']['crates']} "
          f"harness; {chain['harness']['unsafe']} unsafe sites in the harness tree, "
          f"{chain['first_party_unsafe']} in the core")
    for p in (tab, gen):
        print("wrote", os.path.relpath(p, here))
    return 0


if __name__ == "__main__":
    sys.exit(main())
