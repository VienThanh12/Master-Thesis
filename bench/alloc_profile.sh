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
# Offered rate per producer. Left unset the benchmark runs closed loop, which on
# a fast host lands past the saturation plateau: the 26 Aug 2026 profile did that
# and came back at 455 kops/s, a regime where its peak RSS ordering is the
# reverse of the campaign's, so it could attribute nothing. Peak RSS is reported
# below saturation, so the profile has to be taken there too. 8000 per producer
# is one of the swept levels at either shard count.
rate=8000
# Sampling interval as a power of two bytes. jemalloc's default (lg_prof_sample:19,
# every 512 KiB) would put only a handful of samples inside a 2.1 MiB difference;
# 4 KiB resolves it while keeping the dump small.
lg_sample=12
# Bytes of allocation activity between heap dumps, as a power of two. This is the
# difference between a profile that answers the question and one that comes back
# empty: see the note above run_profile. 16 MiB gives a few dozen dumps across a
# default run, which is enough to catch the peak without filling the directory.
lg_interval=24
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
    --rate)       rate="$2"; shift 2;;
    --seed)       seed="$2"; shift 2;;
    --lg-sample)  lg_sample="$2"; shift 2;;
    --lg-interval) lg_interval="$2"; shift 2;;
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
cpp_alloc="the campaign's own arm (system libjemalloc.so.2, no frame pointers)"

# A dedicated profiling build tree, for two reasons that both have to hold at
# once, and neither of which may touch the arm the campaign measures.
#
# Frame pointers. jemalloc walks the stack with __builtin_return_address unless it
# was configured against libunwind, so at -O2 with frame pointers omitted the walk
# stops inside the allocator: every sample attributes to jemalloc's own
# prof_backtrace_impl and not one application site appears. Both arms get frame
# pointers here (-fno-omit-frame-pointer, and -C force-frame-pointers=yes on the
# Rust side) so the two remain one instrument.
#
# A prof-enabled allocator. A jemalloc built without --enable-prof cannot be
# profiled at all: the binary answers `Invalid conf pair: prof:true` and no dump
# lands. Distribution packages frequently omit the flag and the EPEL package this
# project's measurement host links is one of them, so on that host the C++ arm has
# nothing to profile with. UECM_JEMALLOC_PROF_LIB names a prof-enabled build to
# link by absolute path instead; docker/Dockerfile sets it to a build made from
# the same jemalloc source the Rust arm links, so the two profiles come from one
# allocator version as well as one instrument. Unset, this tree still gets frame
# pointers and links whatever the system provides.
#
# Neither change belongs in a timed build, which is why this tree exists: frame
# pointers cost a register and the prof allocator is a different build of the
# allocator. Nothing from this script may be quoted as latency, throughput or
# peak RSS.
# The flag has to land after -O2, which re-enables frame-pointer omission on
# x86-64, so it goes into CMAKE_CXX_FLAGS_RELEASE (kept otherwise identical to
# what CMakeLists.txt sets) and not into CMAKE_CXX_FLAGS, which is prepended.
cpp_prof_args=(-DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -fno-omit-frame-pointer")
if [ -n "${UECM_JEMALLOC_PROF_LIB:-}" ] && [ -e "${UECM_JEMALLOC_PROF_LIB}" ]; then
  cpp_prof_args+=(-DJEMALLOC_LIB="$UECM_JEMALLOC_PROF_LIB")
fi
if cmake -S "$cpp" -B "$cpp/build-jemalloc-prof" -G Ninja -DCMAKE_BUILD_TYPE=Release \
     -DUECM_USE_JEMALLOC=ON -DUECM_BUILD_TESTS=OFF "${cpp_prof_args[@]}" >/dev/null 2>&1 \
   && cmake --build "$cpp/build-jemalloc-prof" --target bench >/dev/null 2>&1; then
  cpp_bin="$cpp/build-jemalloc-prof/bench"
  if [ -n "${UECM_JEMALLOC_PROF_LIB:-}" ]; then
    cpp_alloc="$UECM_JEMALLOC_PROF_LIB (prof-enabled build, frame pointers, profiling only)"
  else
    cpp_alloc="system libjemalloc.so.2, frame pointers (profiling only)"
  fi
else
  echo "  WARN: the profiling build tree failed to configure or build;"
  echo "        falling back to the campaign's arm, whose backtraces stop in the allocator."
fi

# The Rust arm needs the profiling build of the allocator; the plain `jemalloc`
# feature links a jemalloc without prof compiled in.
rust_bin="$here/.bin/rust-jemalloc-prof"
mkdir -p "$here/.bin"
rust_built=0
if RUSTFLAGS="-C force-frame-pointers=yes" \
   cargo build --release --manifest-path "$rust/Cargo.toml" --example bench \
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
printf '  %-34s %s\n' "C++ allocator under profile:" "$cpp_alloc"
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

# Which allocator each arm was profiled with, kept beside the dumps. A profile
# read a month later cannot otherwise say whether the C++ side used the
# distribution build or a prof-enabled one, and the answer changes what a
# difference between the two arms means.
{
  echo "cpp:  $cpp_alloc"
  echo "      binary $cpp_bin"
  echo "rust: tikv-jemalloc-sys, --features jemalloc-prof (source build)"
  echo "      binary $rust_bin"
} > "$outdir/allocators.txt"

# prof_active:true starts sampling immediately so the preload phase is included:
# the difference under investigation is fixed rather than per-operation, so it may
# well be allocated before the measured phase begins.
#
# lg_prof_interval is what makes the profile non-empty, and the reason is worth
# stating because the obvious configuration silently produces nothing. A dump
# taken at exit (prof_final) is taken after main has returned, when the contexts
# and the shard queues have already been dropped: measured here, the C++ arm's
# exit dump held 92 kB and the Rust arm's held 640 bytes, against a live heap of
# 2.3 MB mid-run and a peak RSS of tens of MB. Interval dumps see the heap while
# it is populated. prof_final stays on because a dump that costs nothing to keep
# is worth keeping.
conf_common="prof:true,prof_active:true,prof_final:true,lg_prof_sample:$lg_sample,lg_prof_interval:$lg_interval"

bench_args=(--workload mixed --shards "$shards" --producers "$producers"
            --rate "$rate"
            --active-ues "$active_ues" --ops "$ops" --warmup "$warmup"
            --seed "$seed" --json)

echo
echo "== profiling (sample every $((1 << lg_sample)) B, dump every $((1 << (lg_interval - 20))) MiB allocated) =="

run_profile() {  # run_profile <lang> <env-var> <binary>
  local lang="$1" var="$2" bin="$3"
  local prefix="$outdir/$lang"
  echo "  $lang ..."
  # Note the `key:value` separator: jemalloc's conf string is colon-separated
  # pairs, and `prof_prefix=...` is rejected as a malformed conf string, silently
  # leaving the dump in the current directory under jemalloc's default name.
  env "$var=$conf_common,prof_prefix:$prefix" "$bin" "${bench_args[@]}" \
    > "$outdir/$lang.bench.json" 2> "$outdir/$lang.stderr"

  # jemalloc writes <prefix>.<pid>.<seq>.i<n>.heap every lg_prof_interval bytes of
  # allocation activity, and <prefix>.<pid>.<seq>.f.heap at exit. Picking the last
  # file would pick the exit dump, which is the empty one. The dump wanted is the
  # one whose live byte count is highest, since that is the state ru_maxrss
  # records. Each dump's second line totals live objects and bytes across threads:
  #   t*: <curobjs>: <curbytes> [<accumobjs>: <accumbytes>]
  local dumps peak_file="" peak_bytes=-1 b n=0
  dumps="$(ls -1 "$prefix".*.heap 2>/dev/null)"
  if [ -z "$dumps" ]; then
    echo "    WARN: no heap dump produced; see $outdir/$lang.stderr"
    return 1
  fi
  : > "$outdir/$lang.trajectory.tsv"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    b="$(awk '/^[[:space:]]*t\*:/ { v=$3; gsub(/[^0-9]/, "", v); print v; exit }' "$f")"
    b="${b:-0}"
    n=$(( n + 1 ))
    printf '%s\t%s\n' "$(basename "$f")" "$b" >> "$outdir/$lang.trajectory.tsv"
    if [ "$b" -gt "$peak_bytes" ]; then peak_bytes="$b"; peak_file="$f"; fi
  done <<EOF
$dumps
EOF
  cp "$peak_file" "$outdir/$lang.heap"
  # The rest of the series keeps: it costs kilobytes, it shows the heap's
  # trajectory rather than one point on it, and a testbed visit does not come back.
  mkdir -p "$outdir/$lang.dumps"
  while IFS= read -r f; do
    [ -n "$f" ] && mv "$f" "$outdir/$lang.dumps/"
  done <<EOF
$dumps
EOF
  printf '    peak live heap %s B in %s (%d dumps)\n' \
    "$peak_bytes" "$(basename "$peak_file")" "$n"
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
echo "  <lang>.trajectory.tsv live bytes in every dump, in order"
echo "  <lang>.dumps/         the rest of the series, including the empty exit dump"
echo "  allocators.txt        which allocator build each arm was profiled with"
echo
echo "Reminder: profiling perturbs the allocation path. These runs are for"
echo "attribution only and must not be quoted as latency or throughput."
case "$cpp_alloc" in
  *prof-enabled*)
    echo "The C++ arm here links a prof-enabled build of the allocator, not the"
    echo "distribution build the campaign links. Same source and version as the"
    echo "Rust arm, which is what makes the two profiles differenceable, and one"
    echo "more reason these runs are attribution only.";;
esac
