#!/usr/bin/env bash
# Run the measurement campaign inside the pinned container, with the flags a
# latency measurement needs and without the ones that would quietly ruin it.
#
# READ THIS FIRST. A container is not a testbed. It shares the host kernel, so
# the scheduler, the clocksource, the frequency governor and the hypervisor are
# whatever the host's are. Running this on the KVM guest leaves the far tail
# below saturation exactly as unresolved as bench/TESTBED.md says, and running it
# under WSL2 is still WSL2. What the container fixes is the toolchain and the two
# missing tools (jeprof, perf), which is worth having, and it makes a borrowed
# bare-metal box a one-command target.
#
# THE FLAGS THAT MATTER, and why they are not options:
#   --cpuset-cpus, never --cpus.  --cpus is a CFS quota. A throttled period is a
#       stall of milliseconds and it lands in p99.9, so a quota would manufacture
#       exactly the tail the campaign is trying to measure. --cpuset-cpus pins
#       without capping.
#   seccomp off by default.  The default profile puts a BPF filter in front of
#       every syscall, and the handoff under measurement is futex-heavy. It costs
#       both languages the same, so the comparison survives it, but the absolute
#       numbers move. --seccomp on restores the default profile if that trade is
#       preferred.
#   no memory limit.  Peak RSS is a reported result (RQ3); a limit would make it
#       a measurement of reclaim.
#   --network none.  Nothing here needs the network, the crate graph is prefetched
#       into the image, and a background download during a run is noise.
#   separate build mounts.  A CMake cache stores the absolute path of its
#       compiler, so sharing cpp/build with the host makes CMake refuse to build
#       once the container's toolset compiler appears. Container builds go to
#       docker/.scratch instead, and host builds are left alone.
#
# Usage:
#   docker/run.sh build [--no-cache]
#   docker/run.sh check
#   docker/run.sh campaign --repeats 20 --duration 3
#   docker/run.sh counters --repeats 10
#   docker/run.sh alloc-profile --check
#   docker/run.sh env
#   docker/run.sh shell
#   docker/run.sh exec -- <command...>
#
# Options (before the subcommand):
#   --cpuset LIST     cores to give the container (default: all but 0-1)
#   --image NAME:TAG  image to use (default derived from the pinned toolchain)
#   --seccomp on|off  syscall filter (default off)
#   --network         allow network access (default none)
#   --no-pin          do not pass --pin to campaign.sh/counters.sh
#   --no-log          do not tee the run into bench/results/
#   --smoke           write results to docker/.scratch instead of bench/results
#   --dry-run         print the docker command and exit
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
scratch="$here/.scratch"

# Kept in step with docker/Dockerfile's ARG defaults. They are in the tag so that
# bumping the toolchain cannot reuse an image built from the previous one.
GCC_TOOLSET=15
RUST_VERSION=1.97.1
CMAKE_VERSION=3.30.2
image="uecm-bench:el8-gcc${GCC_TOOLSET}-rust${RUST_VERSION}"

RED=$'\033[31m'; GREEN=$'\033[32m'; YEL=$'\033[33m'; RST=$'\033[0m'
die()  { printf '%serror%s: %s\n' "$RED" "$RST" "$*" >&2; exit 2; }
note() { printf '%s\n' "$*"; }
warn() { printf '%swarning%s: %s\n' "$YEL" "$RST" "$*"; }

cpuset=""
seccomp="off"
network="none"
auto_pin=1
do_log=1
smoke=0
dry_run=0
no_cache=""

while [ $# -gt 0 ]; do
  case "$1" in
    --cpuset)   cpuset="$2"; shift 2;;
    --image)    image="$2"; shift 2;;
    --seccomp)  seccomp="$2"; shift 2;;
    --network)  network="bridge"; shift;;
    --no-pin)   auto_pin=0; shift;;
    --no-log)   do_log=0; shift;;
    --smoke)    smoke=1; shift;;
    --dry-run)  dry_run=1; shift;;
    --no-cache) no_cache="--no-cache"; shift;;
    -h|--help)  sed -n '2,60p' "$0"; exit 0;;
    --)         shift; break;;
    -*)         die "unknown option: $1 (see --help)";;
    *)          break;;
  esac
done

[ $# -gt 0 ] || die "no subcommand (see --help)"
subcmd="$1"; shift

command -v docker >/dev/null 2>&1 || die "docker not found on PATH"
docker info >/dev/null 2>&1 || die "cannot talk to the docker daemon (permissions? is it running?)"

# --- Image ------------------------------------------------------------------ #
build_image() {
  note "== building $image =="
  # The build context is the repository root because two of its files belong in
  # the image (bench/requirements.txt and the locked crate graph), and
  # .dockerignore keeps everything else out of the context.
  docker build $no_cache -f "$here/Dockerfile" -t "$image" \
    --build-arg "GCC_TOOLSET=$GCC_TOOLSET" \
    --build-arg "RUST_VERSION=$RUST_VERSION" \
    --build-arg "CMAKE_VERSION=$CMAKE_VERSION" \
    "$root" || die "image build failed"
}

if [ "$subcmd" = "build" ]; then
  build_image
  note
  note "next: docker/run.sh check"
  exit 0
fi

if ! docker image inspect "$image" >/dev/null 2>&1; then
  if [ "$dry_run" = "1" ]; then
    warn "image $image is not built yet; printing the command anyway."
  else
    note "image $image not present; building it once."
    build_image
  fi
fi

# --- Cores ------------------------------------------------------------------ #
ncpu="$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc)"
if [ -z "$cpuset" ]; then
  # Leave cores 0 and 1 to the rest of the system, which is the split
  # TESTBED.md's own example uses. Below four cores there is nothing to leave.
  if [ "$ncpu" -ge 4 ]; then cpuset="2-$((ncpu - 1))"; else cpuset="0-$((ncpu - 1))"; fi
fi
# A core index the host does not have makes docker fail with a message about
# cpusets that does not mention the campaign, so it is caught here instead.
highest="$(printf '%s' "$cpuset" | tr ',-' '\n\n' | sort -n | tail -1)"
if [ -n "$highest" ] && [ "$highest" -ge "$ncpu" ] 2>/dev/null; then
  die "--cpuset $cpuset asks for core $highest but this host has $ncpu (0-$((ncpu - 1)))"
fi

# --- Host honesty check ----------------------------------------------------- #
# Printed before every measurement subcommand, because the container makes it
# easy to forget which host is underneath.
host_virt="unknown"
if command -v systemd-detect-virt >/dev/null 2>&1; then
  host_virt="$(systemd-detect-virt --vm 2>/dev/null || echo none)"
elif command -v lscpu >/dev/null 2>&1; then
  host_virt="$(lscpu | sed -n 's/^Hypervisor vendor: *//p')"
  [ -z "$host_virt" ] && host_virt="none"
fi
case "$subcmd" in
  campaign|counters|alloc-profile|budget)
    if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
      warn "the host kernel is WSL2. This run is a smoke test, not testbed-grade data."
      warn "The container cannot change that: it shares this kernel."
    elif [ "$host_virt" != "none" ] && [ "$host_virt" != "unknown" ]; then
      warn "the host is a $host_virt guest. The far tail below saturation stays"
      warn "unresolved here, exactly as bench/TESTBED.md states. Resource results,"
      warn "the overload divergence, counters and allocation profiles are fine."
    fi;;
esac

# --- Mounts ----------------------------------------------------------------- #
# Created from the host so they are owned by the invoking user; a directory
# created by the daemon would be root-owned and unwritable under --user.
mkdir -p "$scratch/cpp-build" "$scratch/cpp-build-jemalloc" "$scratch/cpp-build-jemalloc-prof" \
         "$scratch/rust-target" "$scratch/bench-bin" "$root/bench/results"

# A smoke run must not be able to become the thesis's data source. Both
# bench/plot_figures.py and build_deck.py take the *newest* campaign-*.jsonl in
# bench/results when no campaign is named, so a two-repeat run left in that
# directory is one bench/refresh_thesis.sh away from regenerating every quoted
# number from it. In smoke mode the results directory is a scratch mount, so the
# question does not arise.
stamp="$(date +%Y%m%d-%H%M%S)"

results_dir="$root/bench/results"
if [ "$smoke" = "1" ]; then
  results_dir="$scratch/smoke-results"
  mkdir -p "$results_dir"
  warn "smoke mode: results go to docker/.scratch/smoke-results, not bench/results."
  warn "Nothing written by this run can reach the thesis."
fi

args=(
  --rm
  # Named so a long campaign can be found and stopped without hunting through
  # `docker ps`, and so two of them cannot be started by accident.
  --name "uecm-$subcmd-$stamp"
  --user "$(id -u):$(id -g)"
  --cpuset-cpus "$cpuset"
  --network "$network"
  --cap-add SYS_NICE
  --cap-add PERFMON
  --ulimit rtprio=99
  --ulimit nofile=8192
  --tmpfs /tmp:rw,nosuid,nodev,size=1g,mode=1777
  # Mounted at the host's own path so that anything recording an absolute path
  # (a jemalloc dump's binary, a log line) still resolves on the host afterwards.
  -v "$root:$root"
  -v "$scratch/cpp-build:$root/cpp/build"
  -v "$scratch/cpp-build-jemalloc:$root/cpp/build-jemalloc"
  -v "$scratch/cpp-build-jemalloc-prof:$root/cpp/build-jemalloc-prof"
  -v "$scratch/rust-target:$root/rust/target"
  -v "$scratch/bench-bin:$root/bench/.bin"
  -w "$root"
)
if [ "$smoke" = "1" ]; then args+=(-v "$results_dir:$root/bench/results"); fi

# The container has no timezone and stamps its filenames in UTC, while a host run
# stamps them in local time. build_deck.py pairs a campaign with the environment
# capture written at or before it by comparing those stamps as strings, so mixing
# the two clocks on one day can pair a campaign with the wrong capture. Handing
# the host's zone in keeps one clock.
tz=""
if [ -r /etc/timezone ]; then tz="$(cat /etc/timezone)"
elif [ -L /etc/localtime ]; then tz="$(readlink -f /etc/localtime | sed 's#.*/zoneinfo/##')"
fi
[ -n "$tz" ] && args+=(-e "TZ=$tz")
if [ "$seccomp" = "off" ]; then
  args+=(--security-opt seccomp=unconfined)
  if [ "$(cat /sys/module/apparmor/parameters/enabled 2>/dev/null || echo N)" = "Y" ]; then
    args+=(--security-opt apparmor=unconfined)
  fi
fi
if [ -t 0 ] && [ -t 1 ]; then args+=(-it); fi

# --- Command ---------------------------------------------------------------- #
logfile=""
case "$subcmd" in
  check)  cmd=(preflight.sh); do_log=0;;
  env)    cmd=(bench/capture_env.sh); do_log=0;;
  shell)  cmd=(bash); do_log=0;;
  exec)   [ "${1:-}" = "--" ] && shift
          [ $# -gt 0 ] || die "exec needs a command"
          cmd=("$@"); do_log=0;;
  campaign|counters)
    script="bench/${subcmd}.sh"
    cmd=("$script" "$@")
    if [ "$auto_pin" = "1" ] && ! printf '%s\n' "$@" | grep -qx -- '--pin'; then
      cmd+=(--pin "$cpuset")
    fi
    logfile="$results_dir/container-$subcmd-$stamp.log";;
  alloc-profile)
    cmd=(bench/alloc_profile.sh "$@")
    logfile="$results_dir/container-alloc-profile-$stamp.log";;
  budget)
    cmd=(bench/latency_budget.sh "$@")
    logfile="$results_dir/container-budget-$stamp.log";;
  *) die "unknown subcommand: $subcmd (see --help)";;
esac

if [ "$dry_run" = "1" ]; then
  printf 'docker run'
  printf ' %q' "${args[@]}" "$image" "${cmd[@]}"
  printf '\n'
  exit 0
fi

# --- Provenance ------------------------------------------------------------- #
# The campaign's own environment record (bench/capture_env.sh) reports the image
# manifest and the container's limits from the inside. This records the outside:
# which image, which cores, which flags. Both are needed to reconstruct a run.
if [ "$do_log" = "1" ]; then
  prov="$results_dir/container-$stamp.txt"
  {
    echo "# Container run record ($stamp)"
    echo
    echo "image:        $image"
    echo "image id:     $(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null)"
    echo "host kernel:  $(uname -sr)"
    echo "host virt:    $host_virt"
    echo "host cores:   $ncpu"
    echo "cpuset:       $cpuset"
    echo "seccomp:      $seccomp"
    echo "network:      $network"
    echo
    echo "## image manifest"
    docker run --rm --entrypoint cat "$image" /etc/uecm-image.txt 2>/dev/null | sed 's/^/  /'
    echo
    echo "## docker command"
    printf '  docker run'; printf ' %q' "${args[@]}" "$image" "${cmd[@]}"; printf '\n'
  } > "$prov"
  note "== container run record: $prov =="
fi

note "== $image on cores $cpuset (seccomp $seccomp, network $network) =="
note

if [ "$do_log" = "1" ] && [ -n "$logfile" ]; then
  docker run "${args[@]}" "$image" "${cmd[@]}" 2>&1 | tee "$logfile"
  status=${PIPESTATUS[0]}
  note
  note "log: $logfile"
else
  docker run "${args[@]}" "$image" "${cmd[@]}"
  status=$?
fi
exit "$status"
