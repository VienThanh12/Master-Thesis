#!/usr/bin/env bash
# Allocation profile per variant, to attribute the peak-RSS difference (RQ3).
#
# Section 7.5.4 establishes that the 2.1-2.5 MiB peak-RSS difference between the
# languages is real, Holm-significant, reproduces under both allocators, and is
# *fixed* rather than per-context: the measured UeContext layout difference
# accounts for roughly 40 kB at 5000 active UEs, three orders of magnitude short of
# the gap. What it cannot say is where the memory goes. This does: a heap profile
# names the allocation sites, which is what turns "unexplained" into a cause.
#
# ONE TOOL, BOTH LANGUAGES. The profile comes from jemalloc's own `prof`, run
# against the two jemalloc arms that already exist (-DUECM_USE_JEMALLOC=ON and
# --features jemalloc). Profiling C++ with heaptrack and Rust with dhat would
# produce two numbers measured by different instruments with different sampling and
# different notions of a call site, and the whole point is a comparison. This
# mirrors the choice already made for the complexity proxies, where one tool
# (lizard) measures both languages. Where jemalloc prof is unavailable the script
# says so and names the per-language fallback, with the caveat that the fallback is
# not a matched pair.
#
# NOT A TIMING RUN. Sampled backtraces on the allocation path change what the
# allocator costs, so nothing from here belongs in a latency or throughput table.
# The output is attribution only.
#
# WHERE THIS RUNS. It needs a jemalloc built with --enable-prof. Distribution
# builds frequently omit it, and the Rust side needs the opt-in `jemalloc-prof`
# feature. Both are checked before anything is measured, because a profile that
# silently produced nothing would be indistinguishable from a heap with no
# allocations in it. Like the hardware counters, plan on collecting this during the
# testbed visit.
#
# Usage:
#   bench/alloc_profile.sh                  # profile both jemalloc arms
#   bench/alloc_profile.sh --check          # report tool availability only
#   bench/alloc_profile.sh --lg-sample 12 --active-ues 5000
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
cpp="$root/cpp"
rust="$root/rust"

# Defaults match the campaign, so the profile describes the configuration whose
# peak RSS is being explained.
shards=8
producers=8
active_ues=5000
ops=200000
warmup=20000
seed=42
# Sampling interval as a power of two bytes. jemalloc's default (lg_prof_sample:19,
# every 512 KiB) would put only a handful of samples inside a 2.1 MiB difference;
# 4 KiB resolves it while keeping the dump small.
lg_sample=12
check_only=0
# Collect the raw heap dumps even when jeprof is missing. The testbed visit happens
# once; a dump kept now can be symbolised later against the same binary, whereas a
# dump not taken is gone. Off by default so the normal path still insists on a
# complete, symbolised, matched profile.
raw_ok=0

while [ $# -gt 0 ]; do
  case "$1" in
    --shards)     shards="$2"; shift 2;;
    --producers)  producers="$2"; shift 2;;
    --active-ues) active_ues="$2"; shift 2;;
    --ops)        ops="$2"; shift 2;;
    --warmup)     warmup="$2"; shift 2;;
    --seed)       seed="$2"; shift 2;;
    --lg-sample)  lg_sample="$2"; shift 2;;
    --check)      check_only=1; shift;;
    --raw-ok)     raw_ok=1; shift;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

stamp="$(date +%Y%m%d-%H%M%S)"
outdir="$here/results/alloc_profile-$stamp"

# --- Tool discovery ---------------------------------------------------------- #
jeprof=""
for cand in jeprof jemalloc-prof pprof; do
  if command -v "$cand" >/dev/null 2>&1; then jeprof="$cand"; break; fi
done
have_heaptrack=0; command -v heaptrack >/dev/null 2>&1 && have_heaptrack=1
have_valgrind=0; command -v valgrind  >/dev/null 2>&1 && have_valgrind=1

report_fallbacks() {
  echo
  echo "Fallbacks, in order of preference:"
  echo "  1. Install a prof-enabled jemalloc and rerun this script. That keeps the"
  echo "     comparison matched, which is the only reason the profile is worth"
  echo "     quoting next to a language claim."
  echo "       RHEL/Rocky:    sudo dnf install jemalloc-devel   (ships jeprof)"
  echo "       Debian/Ubuntu: libjemalloc-dev provides jeprof; verify prof support"
  echo "                      with the runtime check this script performs."
  echo "  2. Per-language tools, reported with an explicit caveat:"
  if [ "$have_heaptrack" = "1" ]; then
    echo "       C++:  heaptrack (found)          heaptrack cpp/build-jemalloc/bench ..."
  else
    echo "       C++:  heaptrack (not installed)  sudo apt install heaptrack"
  fi
  if [ "$have_valgrind" = "1" ]; then
    echo "       C++:  valgrind massif (found)    valgrind --tool=massif ..."
  else
    echo "       C++:  valgrind massif (not installed)"
  fi
  echo "       Rust: dhat via the dhat-rs crate, or a heaptrack run on the same binary."
  echo "     These do NOT form a matched pair: heaptrack wraps the allocator while"
  echo "     dhat replaces it, they sample differently, and they attribute to"
  echo "     different notions of a call site. If the thesis quotes numbers from"
  echo "     this path, it has to say that the two sides were measured by different"
  echo "     instruments and must not be differenced."
}

# Does the jemalloc this binary links actually support prof?
#
# Asked functionally: run the real benchmark binary with profiling on and check
# that a heap dump lands. Matching on jemalloc's diagnostics instead would be
# fragile -- a build without --enable-prof says "Invalid conf pair: prof:true"
# while a syntax error says "Malformed conf string", and treating the absence of
# one particular wording as success is how a false positive gets discovered on the
# testbed instead of here. Testing with a binary that does not link jemalloc at all
# would prove nothing, so the arm's own binary is used.
supports_prof() {  # supports_prof <env-var-name> <binary>
  local var="$1" bin="$2" prefix dump
  [ -x "$bin" ] || return 1
  prefix="$(mktemp -u "${TMPDIR:-/tmp}/uecm-profcheck-XXXXXX")"
  env "$var=prof:true,prof_active:true,prof_final:true,prof_prefix:$prefix" \
    "$bin" --workload signal --shards 1 --producers 1 --preload 64 --ops 64 \
    --warmup 0 --json >/dev/null 2>&1
  dump="$(ls -1 "$prefix".*.heap 2>/dev/null | head -1)"
  rm -f "$prefix".*.heap
  [ -n "$dump" ]
}

echo "== building the jemalloc arms =="
cmake -S "$cpp" -B "$cpp/build-jemalloc" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF >/dev/null 2>&1
cmake --build "$cpp/build-jemalloc" --target bench >/dev/null 2>&1
cpp_bin="$cpp/build-jemalloc/bench"

# The Rust arm needs the profiling build of the allocator; the plain `jemalloc`
# feature links a jemalloc without prof compiled in.
rust_bin="$here/.bin/rust-jemalloc-prof"
mkdir -p "$here/.bin"
rust_built=0
if cargo build --release --manifest-path "$rust/Cargo.toml" --example bench \
     --features jemalloc-prof >/dev/null 2>&1; then
  cp "$rust/target/release/examples/bench" "$rust_bin"
  rust_built=1
fi

cpp_ok=0; rust_ok=0
supports_prof MALLOC_CONF "$cpp_bin" && cpp_ok=1
if [ "$rust_built" = "1" ]; then
  supports_prof _RJEM_MALLOC_CONF "$rust_bin" && rust_ok=1
fi

echo
echo "== tool check =="
printf '  %-34s %s\n' "C++ jemalloc prof support:" \
  "$([ "$cpp_ok" = 1 ] && echo yes || echo NO)"
printf '  %-34s %s\n' "Rust jemalloc-prof build:" \
  "$([ "$rust_built" = 1 ] && echo yes || echo NO)"
printf '  %-34s %s\n' "Rust jemalloc prof support:" \
  "$([ "$rust_ok" = 1 ] && echo yes || echo NO)"
printf '  %-34s %s\n' "jeprof (symbolisation):" \
  "$([ -n "$jeprof" ] && echo "$jeprof" || echo NO)"

if [ "$check_only" = "1" ]; then
  if [ "$cpp_ok" = 1 ] && [ "$rust_ok" = 1 ] && [ -n "$jeprof" ]; then
    echo
    echo "READY: both arms can be profiled with the same tool."
  elif [ "$cpp_ok" = 1 ] && [ "$rust_ok" = 1 ]; then
    echo
    echo "PARTIAL: both arms profile, but jeprof is missing to symbolise the dumps."
    echo "  Run with --raw-ok to collect the raw dumps anyway and symbolise them"
    echo "  later against the same binaries."
    report_fallbacks
  else
    report_fallbacks
  fi
  exit 0
fi

# Both arms must profile. One language's heap cannot attribute a difference
# between two, which is the entire question.
if [ "$cpp_ok" != 1 ] || [ "$rust_ok" != 1 ]; then
  echo
  echo "ERROR: cannot produce a matched profile on this host."
  echo "  Refusing to profile only one language: a heap profile of one arm cannot"
  echo "  attribute a *difference* between two."
  report_fallbacks
  exit 1
fi
if [ -z "$jeprof" ] && [ "$raw_ok" != "1" ]; then
  echo
  echo "ERROR: jeprof not found, so the dumps could not be symbolised."
  echo "  Both arms *can* be profiled here. If this is the testbed visit and jeprof"
  echo "  cannot be installed, rerun with --raw-ok: the raw dumps keep, and can be"
  echo "  symbolised later against the same binaries, whereas an untaken dump cannot."
  report_fallbacks
  exit 1
fi

mkdir -p "$outdir"

# prof_final dumps the live heap at exit, which is the state peak RSS is about.
# prof_active:true starts sampling immediately so the preload phase is included --
# the difference under investigation is fixed rather than per-operation, so it may
# well be allocated before the measured phase begins.
conf_common="prof:true,prof_active:true,prof_final:true,lg_prof_sample:$lg_sample"

bench_args=(--workload mixed --shards "$shards" --producers "$producers"
            --active-ues "$active_ues" --ops "$ops" --warmup "$warmup"
            --seed "$seed" --json)

echo
echo "== profiling (lg_prof_sample:$lg_sample => every $((1 << lg_sample)) bytes) =="

run_profile() {  # run_profile <lang> <env-var> <binary>
  local lang="$1" var="$2" bin="$3"
  local prefix="$outdir/$lang"
  echo "  $lang ..."
  # Note the `key:value` separator: jemalloc's conf string is colon-separated
  # pairs, and `prof_prefix=...` is rejected as a malformed conf string, silently
  # leaving the dump in the current directory under jemalloc's default name.
  env "$var=$conf_common,prof_prefix:$prefix" "$bin" "${bench_args[@]}" \
    > "$outdir/$lang.bench.json" 2> "$outdir/$lang.stderr"
  # jemalloc names the final dump <prefix>.<pid>.<seq>.f.heap.
  local heap
  heap="$(ls -1 "$prefix".*.heap 2>/dev/null | tail -1)"
  if [ -z "$heap" ]; then
    echo "    WARN: no heap dump produced; see $outdir/$lang.stderr"
    return 1
  fi
  mv "$heap" "$outdir/$lang.heap"
  cp "$bin" "$outdir/$lang.binary"   # keep it: symbolisation needs this exact build
  if [ -z "$jeprof" ]; then
    return 0                          # --raw-ok: dump kept, symbolise later
  fi
  # Text profile sorted by bytes still live at exit, which is the quantity peak RSS
  # reflects.
  "$jeprof" --text --show_bytes "$bin" "$outdir/$lang.heap" \
    > "$outdir/$lang.jeprof.txt" 2>"$outdir/$lang.jeprof.err" || {
      echo "    WARN: jeprof failed; see $outdir/$lang.jeprof.err"
      return 1
    }
  return 0
}

cpp_done=0; rust_done=0
run_profile cpp  MALLOC_CONF       "$cpp_bin"  && cpp_done=1
run_profile rust _RJEM_MALLOC_CONF "$rust_bin" && rust_done=1

if [ "$cpp_done" != 1 ] || [ "$rust_done" != 1 ]; then
  echo
  echo "ERROR: at least one arm produced no usable profile; not writing a summary."
  exit 1
fi

if [ -z "$jeprof" ]; then
  echo
  echo "wrote $outdir/ (raw dumps only, --raw-ok)"
  echo "  <lang>.heap    raw jemalloc dump"
  echo "  <lang>.binary  the exact build it came from"
  echo "Symbolise later with:"
  echo "  jeprof --text --show_bytes $outdir/cpp.binary  $outdir/cpp.heap"
  echo "  jeprof --text --show_bytes $outdir/rust.binary $outdir/rust.heap"
  exit 0
fi

# --- Summary ----------------------------------------------------------------- #
# Parsing lives in bench/parse_jeprof.py so it can be exercised without jeprof
# installed (`parse_jeprof.py --self-test`), for the same reason as the counters:
# this data is collected once, on a host that may not be revisited.
python3 "$here/parse_jeprof.py" summarise "$outdir"

echo
echo "wrote $outdir/"
echo "  summary.json          top sites per language + the RSS delta"
echo "  <lang>.jeprof.txt     full symbolised profile"
echo "  <lang>.heap           raw jemalloc dump (re-symbolise with $jeprof)"
echo "  <lang>.binary         the exact build the dump came from"
echo
echo "Reminder: profiling perturbs the allocation path. These runs are for"
echo "attribution only and must not be quoted as latency or throughput."
