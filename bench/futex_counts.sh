#!/usr/bin/env bash
# Kernel calls per request at the top load, by kind and outcome (RQ1 mechanism).
#
# PROBE ONLY. Not a throughput comparison and not in the Holm-tested family.
#
# Runs ON THE HOST as root, because bpftrace needs the kernel's tracepoints. Each
# measurement still runs in the campaign container through docker/run.sh, so the
# binaries come from the campaign toolchain. The counts come from a session of
# their own on purpose: tracing every futex call slows every arm, and on 30
# September counting context switches with perf hid the Rust lead.
#
# What it answers. Past saturation C++ spends more kernel time per call than Rust
# with the same number of thread switches, and giving Rust the C++ queue design
# removes Rust's lead. This counts what each design asks of the kernel for each
# finished request: futex waits that slept, waits that returned at once because
# the value had already changed, wakes that woke a thread, wakes that found
# nobody, and thread switches, blocked and preempted.
#
# Per request is the difference of two run lengths with the same warm-up, divided
# by the difference in finished calls, so start-up, preload and warm-up cancel.
#
# Arms, all on the system allocator so the allocator is held fixed:
#   cpp-deque     C++ as measured: one mutex, two condition variables, std::promise
#   cpp-ring      C++ with a fixed ring buffer under the same lock
#   rust-channel  Rust as measured: std sync_channel queue, std channel reply
#   rust-mutexq   Rust with the C++ queue design
#   rust-oneshot  Rust with a one-slot reply channel
#
# With --matched it counts the matched-design probe instead (bench/matched_probes.sh),
# whose senders send back to back, so --rate does not apply:
#   cpp-mstock    the probe running the reported C++ Service
#   rust-mstock   the probe running the reported Rust Service
#   cpp-matched   the same ring, futex mutex and reply slot in C++
#   rust-matched  the same ring, futex mutex and reply slot in Rust
#
# Usage (on the host, from the repository root):
#   bench/futex_counts.sh --pin 2-17 --rate 112000 --repeats 3 --out-dir bench/results-probes-<tag>
#   bench/futex_counts.sh --pin 2-17 --matched --repeats 3 --out-dir bench/results-probes-<tag>
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
pin="2-17"
rate=112000
repeats=3
short_s=3
long_s=6
out_dir="$here/results"
matched=0
while [ $# -gt 0 ]; do
  case "$1" in
    --pin) pin="$2"; shift 2;;
    --rate) rate="$2"; shift 2;;
    --repeats) repeats="$2"; shift 2;;
    --out-dir) out_dir="$2"; shift 2;;
    --matched) matched=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

die() { echo "futex_counts: $*" >&2; exit 1; }
[ -f /.dockerenv ] && die "run this on the host. It starts the container itself."
[ "$(id -u)" = 0 ] || die "run as root: bpftrace needs the kernel tracepoints"
command -v bpftrace >/dev/null 2>&1 || die "bpftrace not found"
mkdir -p "$out_dir"

in_container() { "$root/docker/run.sh" --cpuset "$pin" exec -- "$@"; }

if [ "$matched" = 1 ]; then
  arms=(cpp-mstock rust-mstock cpp-matched rust-matched)
  echo "== building the matched-design probe in the campaign container =="
  # One binary per arm name, because bpftrace tells the arms apart by thread name.
  in_container bash -c '
set -e
cmake -S cpp -B cpp/build-matched-system -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_MATCHED_PROBE=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build cpp/build-matched-system --target matched >/dev/null
mkdir -p bench/.bin
cp cpp/build-matched-system/matched bench/.bin/fc-cpp-mstock
cp cpp/build-matched-system/matched bench/.bin/fc-cpp-matched
cargo build --release --manifest-path rust/Cargo.toml --example matched --features matched-probe \
  >/dev/null 2>&1
cp rust/target/release/examples/matched bench/.bin/fc-rust-mstock
cp rust/target/release/examples/matched bench/.bin/fc-rust-matched' | grep -v '^==' || true
else
arms=(cpp-deque rust-channel rust-mutexq cpp-ring rust-oneshot)
echo "== building the five arms in the campaign container =="
in_container bash -c '
set -e
cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build cpp/build --target bench >/dev/null
cmake -S cpp -B cpp/build-ring -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DUECM_RING_QUEUE=ON -DUECM_BUILD_TESTS=OFF >/dev/null
cmake --build cpp/build-ring --target bench >/dev/null
mkdir -p bench/.bin
cp cpp/build/bench bench/.bin/fc-cpp-deque
cp cpp/build-ring/bench bench/.bin/fc-cpp-ring
for v in channel mutexq oneshot; do
  case "$v" in
    channel) f=();;
    mutexq) f=(--features mutex-queue);;
    oneshot) f=(--features sync-oneshot);;
  esac
  cargo build --release --manifest-path rust/Cargo.toml --example bench "${f[@]}" >/dev/null 2>&1
  cp rust/target/release/examples/bench "bench/.bin/fc-rust-$v"
done' | grep -v '^==' || true
fi
for a in "${arms[@]}"; do
  [ -x "$root/docker/.scratch/bench-bin/fc-$a" ] || [ -x "$here/.bin/fc-$a" ] \
    || die "build of fc-$a is missing"
done

# A wait returns 0 after sleeping, -EAGAIN when the word had already changed.
# A wake returns how many threads it woke. The op is kept per thread between
# entry and exit, offset by one so that FUTEX_WAIT (0) is not mistaken for unset.
read -r -d '' prog <<'BT' || true
tracepoint:syscalls:sys_enter_futex /comm == str($1)/ { @op[tid] = (args.op & 127) + 1; }
tracepoint:syscalls:sys_exit_futex /@op[tid] != 0/ {
  $o = @op[tid] - 1;
  delete(@op, tid);
  if (args.ret > 0) { @woke[$o] = count(); }
  else if (args.ret == 0) { @zero[$o] = count(); }
  else { @err[$o, 0 - args.ret] = count(); }
}
tracepoint:sched:sched_switch /args.prev_comm == str($1)/ {
  if (args.prev_state == 0) { @preempted = count(); } else { @blocked = count(); }
}
tracepoint:raw_syscalls:sys_enter /comm == str($1)/ { @sys[args.id] = count(); }
END { clear(@op); }
BT

stamp="$(date +%Y%m%d-%H%M%S)"
raw="$out_dir/futex_counts-$stamp.jsonl"
summary="$out_dir/futex_counts-$stamp.summary.txt"
: > "$raw"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

n_arms=${#arms[@]}
if [ "$matched" = 1 ]; then
  echo "== counting the matched-design probe, $repeats repeats, windows of ${short_s} s and ${long_s} s =="
else
  echo "== counting at $rate per producer, $repeats repeats, runs of ${short_s} s and ${long_s} s =="
fi
for rep in $(seq 1 "$repeats"); do
  start_at=$(( (rep - 1) % n_arms ))
  for k in $(seq 0 $(( n_arms - 1 ))); do
    arm="${arms[$(( (start_at + k) % n_arms ))]}"
    comm="fc-$arm"
    comm="${comm:0:15}"
    for len in "$short_s" "$long_s"; do
      bt="$tmp/bt.json"
      : > "$bt"
      bpftrace -f json -e "$prog" "$comm" > "$bt" 2> "$tmp/bt.err" &
      bpid=$!
      for _ in $(seq 1 150); do
        grep -q attached_probes "$bt" 2>/dev/null && break
        kill -0 "$bpid" 2>/dev/null || { cat "$tmp/bt.err" >&2; die "bpftrace exited"; }
        sleep 0.1
      done
      grep -q attached_probes "$bt" || die "bpftrace did not attach"
      if [ "$matched" = 1 ]; then
        design=matched
        [ "${arm#*-}" = mstock ] && design=stock
        line="$(in_container taskset -c "$pin" "bench/.bin/fc-$arm" --design "$design" \
          --shards 7 --producers 7 --active-ues 5000 --duration-s "$len" --warmup-s 1 \
          --seed $(( 42 + rep )) --json 2>/dev/null | grep '^{' | tail -1)"
      else
        line="$(in_container taskset -c "$pin" "bench/.bin/fc-$arm" --workload mixed \
          --shards 7 --producers 7 --active-ues 5000 --preload 5000 \
          --ops $(( rate * 30 )) --warmup "$rate" --seed $(( 42 + rep )) --rate "$rate" \
          --max-run-s "$len" --correction-when after --json 2>/dev/null | grep '^{' | tail -1)"
      fi
      kill -INT "$bpid"
      wait "$bpid" || true
      [ -n "$line" ] || die "no output from $arm"
      python3 - "$arm" "$rep" "$len" "$line" "$bt" >> "$raw" <<'PY'
import json, sys
arm, rep, length, line, bt = sys.argv[1:6]
maps = {}
for raw in open(bt):
    raw = raw.strip()
    if not raw:
        continue
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        continue
    if msg.get("type") == "map":
        maps.update(msg["data"])
print(json.dumps({"arm": arm, "repeat": int(rep), "max_run_s": int(length),
                  "bench": json.loads(line), "bpftrace": maps}))
PY
      printf '  rep %s %-13s %ss done\n' "$rep" "$arm" "$len"
    done
  done
done

python3 - "$raw" > "$summary" <<'PY'
import json, statistics, sys

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
WAIT_OPS, WAKE_OPS = {"0", "9"}, {"1", "10"}
NAMES = {"202": "futex", "35": "nanosleep", "230": "clock_nanosleep", "24": "sched_yield",
         "9": "mmap", "11": "munmap", "28": "madvise", "12": "brk", "1": "write",
         "0": "read", "98": "getrusage", "334": "rseq", "14": "rt_sigprocmask"}

def flat(m):
    """bpftrace prints scalar counts bare and keyed counts as an object."""
    return m if isinstance(m, dict) else {"": m}

def counts(r):
    bt = r["bpftrace"]
    woke = flat(bt.get("@woke", {}))
    zero = flat(bt.get("@zero", {}))
    err = flat(bt.get("@err", {}))
    c = {
        "wait slept": sum(v for k, v in zero.items() if k in WAIT_OPS),
        "wait returned at once": sum(v for k, v in err.items()
                                     if k.split(",")[0].strip("[ ") in WAIT_OPS
                                     and k.split(",")[1].strip("] ") == "11"),
        "wait other error": sum(v for k, v in err.items()
                                if k.split(",")[0].strip("[ ") in WAIT_OPS
                                and k.split(",")[1].strip("] ") != "11"),
        "wake woke a thread": sum(v for k, v in woke.items() if k in WAKE_OPS),
        "wake found nobody": sum(v for k, v in zero.items() if k in WAKE_OPS),
        "other futex ops": sum(v for k, v in list(woke.items()) + list(zero.items())
                               if k not in WAIT_OPS | WAKE_OPS),
        "blocked switches": flat(bt.get("@blocked", 0)).get("", 0),
        "preempted": flat(bt.get("@preempted", 0)).get("", 0),
    }
    sysc = flat(bt.get("@sys", {}))
    c["all syscalls"] = sum(sysc.values())
    for k, v in sysc.items():
        c["syscall " + NAMES.get(k, k)] = v
    b = r["bench"]
    c["kernel us"] = b["cpu_sys_s"] * 1e6
    c["user us"] = b["cpu_user_s"] * 1e6
    # The matched-design probe names its fields after its time window.
    return c, b.get("ops_total", b.get("ops")), b.get("throughput_ops_s", b.get("ops_per_s"))

per = {}
thr = {}
for (arm, rep) in sorted({(r["arm"], r["repeat"]) for r in rows}):
    pair = {r["max_run_s"]: r for r in rows if r["arm"] == arm and r["repeat"] == rep}
    if len(pair) != 2:
        continue
    (s, ls), (l, ll) = sorted(pair.items())
    cs, ops_s, _ = counts(ls)
    cl, ops_l, thr_l = counts(ll)
    d_ops = ops_l - ops_s
    if d_ops <= 0:
        continue
    keys = set(cs) | set(cl)
    per.setdefault(arm, []).append({k: (cl.get(k, 0) - cs.get(k, 0)) / d_ops for k in keys})
    thr.setdefault(arm, []).append(thr_l)

order = ["cpp-deque", "rust-channel", "rust-mutexq", "cpp-ring", "rust-oneshot",
         "cpp-mstock", "rust-mstock", "cpp-matched", "rust-matched"]
arms = [a for a in order if a in per]
print("Per finished request, median over repeats (difference of 6 s and 3 s runs).")
print("Tracing slows every arm, so the throughput column is not the comparison.")
print()
rows_out = ["kops/s while traced", "wait slept", "wait returned at once", "wait other error",
            "wake woke a thread", "wake found nobody", "other futex ops",
            "blocked switches", "preempted", "all syscalls", "kernel us", "user us"]
extra = sorted({k for a in arms for d in per[a] for k in d if k.startswith("syscall ")},
               key=lambda k: -statistics.median(d.get(k, 0) for a in arms for d in per[a]))
print(f"{'':<26}" + "".join(f"{a:>14}" for a in arms))
for name in rows_out + extra[:8]:
    cells = []
    for a in arms:
        if name == "kops/s while traced":
            cells.append(f"{statistics.median(thr[a]) / 1000:>14.1f}")
        else:
            cells.append(f"{statistics.median(d.get(name, 0) for d in per[a]):>14.3f}")
    print(f"{name:<26}" + "".join(cells))
print()
print(f"raw: {sys.argv[1]}")
PY
cat "$summary"
