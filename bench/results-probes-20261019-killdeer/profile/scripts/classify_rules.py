"""Shared rules for classify.py and debug_owner.py. Disposable diagnostic."""
import re


def has(s, *needles):
    return any(n in s for n in needles)


ALLOC = ("malloc", "free", "calloc", "realloc", "memalign", "aligned_alloc", "_int_", "unlink_chunk",
         "tcache", "cfree", "sysmalloc", "je_", "jemalloc", "__rdl_alloc", "__rdl_dealloc",
         "__rdl_realloc", "__rust_alloc", "__rust_dealloc", "__rust_realloc", "14aligned_malloc",
         "11GlobalAlloc", "operator new", "operator delete", "_Znwm", "_ZdlPv")
# Thin wrappers whose only job is the system call: their samples are the cost of entering
# and leaving the kernel, so they count as kernel time.
SYSCALL_WRAPPERS = ("syscall (", "__lll_unlock_wake", "__lll_lock_wait", "futex_wait (inlined)",
                    "futex_wake (inlined)", "5futex10futex_wait", "5futex10futex_wake",
                    "futex::futex_wait", "futex::futex_wake", "__futex_abstimed_wait", "do_futex_wait")
# In the C++ build only the shard queue takes a mutex or waits on a condition variable, and only
# std::promise::set_value calls pthread_once (through std::call_once). Names appear both v0-mangled
# (as perf prints them) and demangled (as addr2line prints them).
REPLY = ("10Completion", "18completion_channel", "message::Completion", "completion_channel",
         "std::promise", "std::future", "__basic_future", "__future_base", "_State_baseV2",
         "__atomic_futex_unsigned", "std::call_once", "__once_proxy", "TimedResponse", "pthread_once")
QUEUE = ("7Request", "11mutex_queue", "message::Request", "mutex_queue", "BoundedQueue", "RingBuffer",
         "std::deque<uecm::Request", "_Deque_base<uecm::Request", "std::queue<uecm::Request",
         "pthread_mutex", "pthread_cond", "__gthread_mutex", "condition_variable",
         "__lll_unlock_wake (", "__lll_lock_wait (")
# Waker::try_select picks a waiting thread to wake. Context::try_select runs on the waiting side.
WAKE = ("futex_wake", "try_to_wake_up", "wake_up_q", "wake_q_add", "6unpark", "::unpark",
        "9SyncWaker6notify", "SyncWaker>::notify", "5Waker6notify", "Waker>::notify",
        "5Waker10try_select", "Waker>::try_select", "pthread_cond_signal", "notify_one", "notify_all",
        "_M_futex_notify_all")
WAIT = ("futex_wait", "__schedule", "schedule (", "4park", "thread::park", "Parker>::park",
        "10wait_until", "::wait_until", "8register", "Waker>::register", "pthread_cond_wait",
        "_M_futex_wait_until", "_M_load_when_equal")
CORE = ("9ShardCore", "10shard_core", "ShardCore", "FlatMap")
HARNESS = ("5bench", "12hdrhistogram", "hdrhistogram::", "8workload", "8Workload", "10SplitMix64",
           "Instant3now", "Timespec3now", "Instant>::now", "Timespec>::now", "clock_gettime", "[vdso]",
           "nanosleep", "sleep_until", "sleep_for", "main::{lambda", "bench::", "HdrHistogram",
           "Workload", "SplitMix64", "exec_op", "steady_clock::now")
GLUE = ("7Service", "11worker_loop", "9completed", "uecm::Service::", "uecm::service::")


def owner_of(text):
    for name, needles in (("reply handle", REPLY), ("shard queue", QUEUE), ("UE operation", CORE),
                          ("harness", HARNESS), ("service dispatch", GLUE)):
        if has(text, *needles):
            return name
    return None


def role_hint(texts):
    """Role evidence from a sample's frames, or None. Workers own the core and receive requests;
    senders run the harness, create replies and send requests."""
    joined = " ".join(texts)
    if has(joined, "11worker_loop", "worker_loop", "9ShardCore", "ShardCore"):
        return "worker"
    if has(joined, "5bench", "main::{lambda", "12hdrhistogram", "hdrhistogram::", "bench::",
           "18completion_channel", "completion_channel", "_completion", "Service::submit_async", "_async"):
        return "sender"
    return None


def parse(stream):
    sample = None
    for raw in stream:
        line = raw.rstrip("\n")
        if not line.strip():
            if sample:
                yield sample
            sample = None
            continue
        if not line.startswith("\t"):
            if sample:
                yield sample
            m = re.match(r"\s*(\d+)\s+([\d.]+):\s+(\d+)", line)
            sample = {"tid": int(m.group(1)), "time": float(m.group(2)),
                      "period": int(m.group(3)), "frames": []} if m else None
            continue
        if sample is None:
            continue
        body = line.strip()
        addr_s, _, rest = body.partition(" ")
        sym, _, dso = rest.rpartition(" (")
        try:
            addr = int(addr_s, 16)
        except ValueError:
            continue
        sample["frames"].append((addr, sym, dso.rstrip(")")))
    if sample:
        yield sample
