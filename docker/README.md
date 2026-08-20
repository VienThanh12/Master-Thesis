# Containerised measurement campaign

One command runs the RQ1/RQ3 campaign in a container whose toolchain matches the
host the reported numbers came from:

```bash
docker/run.sh build          # once, ~4 min
docker/run.sh check          # readiness, GREEN/RED
docker/run.sh campaign --repeats 20 --duration 3
```

## Read this before you quote anything from it

**A container is not a testbed.** It shares the host kernel. The scheduler, the
clocksource, the frequency governor, the hugepage policy and the hypervisor are
whatever the host's are, and none of them change when the campaign moves inside.
Running this on the KVM guest leaves the far tail below saturation exactly as
unresolved as `bench/TESTBED.md` says it is. Running it under WSL2 is still WSL2,
and `docker/run.sh` says so before every measurement subcommand.

What the container does buy is worth having, and it is three things.

1. **The toolchain stops being a property of whichever box was free.** Every
   version is pinned in `docker/Dockerfile` and recorded at image-build time in
   `/etc/uecm-image.txt`, which `bench/capture_env.sh` copies into the campaign's
   own environment record. A result produced here carries the compiler that
   produced it.
2. **It carries what the measurement host is missing.** `jeprof` symbolises the
   heap dumps `bench/alloc_profile.sh` takes, and the peak-RSS attribution has
   been waiting on it. `perf` is what `bench/counters.sh` needs. The image also
   builds a prof-enabled jemalloc, because the distribution package on both this
   image and the measurement host is built without `--enable-prof` and cannot be
   profiled at all: see the note below.
3. **A borrowed bare-metal box becomes a one-command target.** Install Docker,
   clone, `docker/run.sh campaign`. The compiler is the same one the numbers
   already in the thesis were built with, so the bare-metal campaign changes the
   host and nothing else.

## Toolchain parity with the host of record

The campaign the thesis reports ran on the KVM Xeon guest recorded in
`bench/results/env-20260812-154523.txt`. The image reproduces it:

| | Host of record | Image |
| --- | --- | --- |
| Distribution | Rocky Linux 8.10 | Rocky Linux 8.10 |
| C++ | g++ (GCC) 15.1.1 | g++ (GCC) 15.2.1, `gcc-toolset-15` |
| Rust | rustc 1.97.1 | rustc 1.97.1 |
| cmake | 3.30.2 | 3.30.2 |
| jemalloc (C++ arm) | 5.2.1, distribution build | 5.2.1-3.el8, same EPEL build |

The GCC patch level is the one difference, and it is recorded on both sides
rather than smoothed over. The Rust arm builds its own jemalloc 5.3.1 from source
through `tikv-jemallocator` in both cases, which is the version confound
`docs/TODO.md` §3 already names.

## The flags, and why they are not options

`docker/run.sh` exists because the default way to give a container CPU is the
wrong way for this measurement.

- **`--cpuset-cpus`, never `--cpus`.** `--cpus` is a CFS bandwidth quota. When the
  container exhausts its slice the cgroup throttles it until the next period, and
  a throttled period is a stall of milliseconds that lands directly in p99.9. A
  quota would manufacture the exact tail the campaign is trying to measure.
  `--cpuset-cpus` pins without capping. `docker/run.sh check` fails if a quota is
  set, and `bench/capture_env.sh` records `cgroup cpu quota` with a `[QUOTA]`
  warning either way.
- **seccomp off by default.** The default profile puts a BPF filter in front of
  every syscall, and the handoff under measurement is futex-heavy, so the filter
  sits on the measured path. It costs both languages the same, so the paired
  comparison survives it, but absolute latencies move. `--seccomp on` restores the
  default profile, and the mode is recorded either way.
- **no memory limit.** Peak RSS is a reported result (RQ3). Under a limit it would
  measure reclaim as well as the program.
- **`--network none`.** The locked crate graph is prefetched into the image, so
  nothing needs the network, and a background download during a run is noise.
- **separate build trees.** A CMake cache stores the absolute path of its
  compiler, so a `cpp/build` configured on the host with `/usr/bin/g++` makes
  CMake refuse once the container's toolset compiler appears. Container builds go
  to `docker/.scratch/` and host builds are left alone.
- **the invoking user, not root.** Everything written into the bind-mounted
  repository is owned by you. The cost is that `--cap-add` no longer has an
  effect, since a non-root uid has an empty effective capability set: SCHED_FIFO
  is reached through `--ulimit rtprio=99` instead (tested by `check`), and `perf`
  self-monitors at `perf_event_paranoid` 2 or lower.
- **the host's timezone.** Container filenames would otherwise be stamped in UTC
  while host runs are stamped in local time, and `build_deck.py` pairs a campaign
  with an environment capture by comparing those stamps.

## Subcommands

```bash
docker/run.sh build [--no-cache]        # build the image
docker/run.sh check                     # readiness check inside the container
docker/run.sh campaign  <campaign.sh args>
docker/run.sh counters  <counters.sh args>
docker/run.sh alloc-profile <alloc_profile.sh args>
docker/run.sh budget    <latency_budget.sh args>
docker/run.sh env                       # capture_env.sh only
docker/run.sh shell                     # interactive
docker/run.sh exec -- <command>
```

Options go before the subcommand: `--cpuset LIST`, `--image NAME:TAG`,
`--seccomp on|off`, `--network`, `--no-pin`, `--no-log`, `--smoke`, `--dry-run`.

`campaign` and `counters` get `--pin` set to the same core list as the cpuset
unless you pass your own or `--no-pin`.

**`--smoke` sends results to `docker/.scratch/smoke-results` instead of
`bench/results`.** Use it for anything that is not meant to be evidence.
`bench/plot_figures.py` and `build_deck.py` both take the *newest*
`campaign-*.jsonl` in `bench/results` when no campaign is named, so a two-repeat
test run left in that directory is one `bench/refresh_thesis.sh` away from
regenerating every quoted number in the thesis from it.

## What a real run looks like

On a bare-metal box with 20 cores, following `bench/TESTBED.md` §2 for the
governor, turbo and SMT first (those are host settings, so they are applied on
the host, not in the container):

```bash
bench/setup_testbed.sh --no-install     # governor, turbo, SMT on the host
docker/run.sh build
docker/run.sh check                     # expect GREEN, or read the warnings
docker/run.sh campaign --cpuset 2-17 --repeats 20 --duration 3 --warmup-s 1 \
    --rates "1000 2000 4000 6000 8000 10000 12000 16000"
docker/run.sh counters --cpuset 2-17 --repeats 10
docker/run.sh alloc-profile --check     # then without --check
```

Then, on the host and not in the container:

```bash
python3 bench/pool_hist.py bench/results/campaign-<stamp>.hist.jsonl \
    --verify bench/results/campaign-<stamp>.jsonl
bench/refresh_thesis.sh
```

Two files per run record where the numbers came from:
`bench/results/env-<stamp>.txt` (from inside: image manifest, cgroup limits,
seccomp mode, hypervisor) and `bench/results/container-<stamp>.txt` (from
outside: image id, cpuset, the full `docker run` command line).

## The allocation profile, which the container is what fixed

Running `bench/alloc_profile.sh` in here found three defects that would have sent
the September visit home with an empty profile, and none of them were visible
without running it end to end. They are fixed, and recorded in `spec/SPECIFICATION.md`
§12 and `docs/TODO.md`.

- The distribution jemalloc is built without `--enable-prof`, on this image and on
  the measurement host. The C++ arm had nothing to profile with, and the script
  refuses to profile one arm alone, correctly, since one language's heap cannot
  attribute a difference between two. The image builds a prof-enabled jemalloc
  from the same source the Rust arm links, and only the profiling build tree links
  it, by absolute path. The campaign's own arm still links `/lib64/libjemalloc.so.2`.
- Backtraces at `-O2` stopped inside the allocator, so not a single application
  site appeared. The profiling tree keeps frame pointers on both sides.
- `prof_final` dumps the live heap at process *exit*, after the contexts and shard
  queues have been dropped. Measured: 92 kB for C++ and 640 bytes for Rust against
  2.3 MB live mid-run. The script now dumps on an allocation interval and keeps the
  dump with the highest live byte count, with the whole series beside it.

With those in place both arms attribute: C++ 61% cumulative to
`ShardCore::create_context` under `worker_loop`, Rust 65% under `Service::start`
with 8% in the `sync_channel<Request>` slot array.

One reading caveat: jemalloc 5.3 keeps its own frame at the leaf of every sampled
stack, so the flat column collapses onto `prof_backtrace_impl` and the cumulative
column is the one carrying the attribution. Totals are unaffected.
`bench/parse_jeprof.py` detects this and switches ranking.

## Has it been run?

Yes. `docker/VALIDATION.md` records a 200-run campaign through this harness on 20 August
2026, what it validated (including the first `tab_jitter.tex` and far-tail macros this
repository has produced, and a lossless HDR sidecar across all 200 runs), which reported
results reproduced in direction, and one that did not reproduce in magnitude. It was run
with `--smoke` on a WSL2 laptop, so it is a harness validation and not evidence, and the
artefacts are kept under `docker/validation/`.

## Limits worth knowing

- **`perf` is the EL8 build** (4.18) while the host kernel may be far newer.
  `perf stat` is tolerant of that, and `check` tests one real counter read rather
  than assuming. `bench/counters.sh --software` exercises the plumbing where there
  is no PMU at all.
- **SCHED_FIFO may be refused** by cgroup v2, which keeps real-time tasks out of
  non-root cgroups. `check` tests it. The documented campaign does not use `--rt`.
- **No hardware counters under a hypervisor that exposes no PMU.**
  `bench/counters.sh` refuses rather than reporting zeros, which is the correct
  behaviour and is not something the container can fix.
- **The image is not the reproduction package.** It pins the toolchain, not the
  repository. `docs/TODO.md` Phase 11 item 11 (a tagged, archived release with a
  DOI and a `REPRODUCE.md`) is the other half.
