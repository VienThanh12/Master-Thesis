// Matched-design probe, C++ side. PROBE ONLY, never a reported arm.
// Twin of rust/examples/matched.rs. See docs/OVERLOAD_MECHANISM.md §4.16.
//
// Past saturation the two services differ in how their standard libraries hand a
// request to a worker and the reply back. This probe runs the same mini-service in both
// languages around the real ShardCore: one worker thread per shard, a fixed ring queue
// behind a three-state futex mutex, one reply slot per sender, and every wait and wake
// through the futex system call with the same arguments, issued only when a thread
// sleeps. Algorithm, memory layout and system calls match, so what differs is each
// language's own code: ShardCore, the dispatch, and the loops.
//
// --design stock runs the same harness loop through the reported Service instead, so
// within one binary the two modes differ only in the handoff. Senders send back to back,
// which is the overload state of the campaign. --self-test runs one sender through both
// designs and checks that every operation gets the same result.

#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <linux/futex.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

#include "uecm/hash.hpp"
#include "uecm/service.hpp"
#include "uecm/shard_core.hpp"
#include "workload.hpp"

#ifndef UECM_ALLOC_NAME
#define UECM_ALLOC_NAME "system"
#endif

using namespace uecm;
using bench::WKind;
using bench::WOp;
using bench::Workload;
using clock_type = std::chrono::steady_clock;

namespace {

constexpr std::size_t kQueueCapacity = 1024;

// --- Futex -----------------------------------------------------------------------------

void futex_wait(std::atomic<std::uint32_t>& word, std::uint32_t expected) {
  syscall(SYS_futex, reinterpret_cast<std::uint32_t*>(&word), FUTEX_WAIT | FUTEX_PRIVATE_FLAG,
          expected, nullptr, nullptr, 0u);
}

void futex_wake_one(std::atomic<std::uint32_t>& word) {
  syscall(SYS_futex, reinterpret_cast<std::uint32_t*>(&word), FUTEX_WAKE | FUTEX_PRIVATE_FLAG,
          1u, nullptr, nullptr, 0u);
}

// Three-state futex mutex: 0 unlocked, 1 locked, 2 locked with possible waiters.
class FutexMutex {
 public:
  void lock() {
    std::uint32_t c = 0;
    if (state_.compare_exchange_strong(c, 1, std::memory_order_acquire, std::memory_order_relaxed))
      return;
    if (c != 2) c = state_.exchange(2, std::memory_order_acquire);
    while (c != 0) {
      futex_wait(state_, 2);
      c = state_.exchange(2, std::memory_order_acquire);
    }
  }

  void unlock() {
    if (state_.exchange(0, std::memory_order_release) == 2) futex_wake_one(state_);
  }

 private:
  std::atomic<std::uint32_t> state_{0};
};

// --- Request, queue, reply -----------------------------------------------------------------

enum class Kind : std::uint8_t {
  Create,
  Setup,
  Signal,
  AddDrb,
  BeginReconf,
  CompleteReconf,
  AbortReconf,
  Release,
  Stop,
};

// One tagged struct carries every operation, in the Rust field order.
struct Request {
  Kind kind = Kind::Stop;
  std::uint32_t reply = 0;
  UeId ue_id = 0;
  CreateParams create{};
  SignalingMsg signaling{};
  DrbEntry drb{};
  ReconfigParams reconfig{};
};

// Bounded queue: a fixed ring under the futex mutex. A pusher wakes the worker only if it
// is asleep, and a popper wakes a pusher only if one is asleep on a full ring.
class Queue {
 public:
  Queue() : buf_(kQueueCapacity) {}

  void push(const Request& r) {
    mutex_.lock();
    for (;;) {
      if (len_ < kQueueCapacity) {
        buf_[tail_] = r;
        if (++tail_ == kQueueCapacity) tail_ = 0;
        ++len_;
        const bool wake = consumer_sleeping_;
        if (wake) {
          consumer_sleeping_ = false;
          items_.fetch_add(1, std::memory_order_relaxed);
        }
        mutex_.unlock();
        if (wake) futex_wake_one(items_);
        return;
      }
      ++producers_sleeping_;
      const std::uint32_t seq = space_.load(std::memory_order_relaxed);
      mutex_.unlock();
      futex_wait(space_, seq);
      mutex_.lock();
      --producers_sleeping_;
    }
  }

  Request pop() {
    mutex_.lock();
    for (;;) {
      if (len_ > 0) {
        const Request r = buf_[head_];
        if (++head_ == kQueueCapacity) head_ = 0;
        --len_;
        const bool wake = producers_sleeping_ > 0;
        if (wake) space_.fetch_add(1, std::memory_order_relaxed);
        mutex_.unlock();
        if (wake) futex_wake_one(space_);
        return r;
      }
      consumer_sleeping_ = true;
      const std::uint32_t seq = items_.load(std::memory_order_relaxed);
      mutex_.unlock();
      futex_wait(items_, seq);
      mutex_.lock();
    }
  }

 private:
  FutexMutex mutex_;
  std::vector<Request> buf_;
  std::size_t head_ = 0;
  std::size_t tail_ = 0;
  std::size_t len_ = 0;
  bool consumer_sleeping_ = false;
  std::uint32_t producers_sleeping_ = 0;
  std::atomic<std::uint32_t> items_{0};
  std::atomic<std::uint32_t> space_{0};
};

constexpr std::uint32_t kEmpty = 0;
constexpr std::uint32_t kWaiting = 1;
constexpr std::uint32_t kReady = 2;

// One per sender, reused for every request it sends. The worker wakes the sender only if
// the sender is asleep.
struct alignas(64) ReplySlot {
  std::atomic<std::uint32_t> state{kEmpty};
  std::atomic<std::uint32_t> ok{0};
};

// --- The two designs -----------------------------------------------------------------------

struct Stock {
  Service svc;
  explicit Stock(const Config& cfg) : svc(cfg) {}

  bool exec(std::size_t, const Request& r) {
    switch (r.kind) {
      case Kind::Create: return svc.create_context(r.ue_id, r.create).has_value();
      case Kind::Setup: return svc.setup_connection(r.ue_id).has_value();
      case Kind::Signal: return svc.handle_signaling(r.ue_id, r.signaling).has_value();
      case Kind::AddDrb: return svc.add_drb(r.ue_id, r.drb).has_value();
      case Kind::BeginReconf: return svc.begin_reconfigure(r.ue_id, r.reconfig).has_value();
      case Kind::CompleteReconf: return svc.complete_reconfigure(r.ue_id).has_value();
      case Kind::AbortReconf: return svc.abort_reconfigure(r.ue_id).has_value();
      case Kind::Release: return svc.release_context(r.ue_id).has_value();
      case Kind::Stop: return false;
    }
    return false;
  }
};

struct Matched {
  std::uint64_t n_shards;
  std::vector<Queue> queues;
  std::vector<ReplySlot> slots;
  Matched(std::uint64_t shards, std::uint64_t producers)
      : n_shards(shards), queues(shards), slots(producers) {}

  bool exec(std::size_t sender, const Request& r) {
    queues[shard_index(r.ue_id, n_shards)].push(r);
    ReplySlot& slot = slots[sender];
    std::uint32_t expected = kEmpty;
    if (slot.state.compare_exchange_strong(expected, kWaiting, std::memory_order_acquire,
                                           std::memory_order_acquire)) {
      for (;;) {
        futex_wait(slot.state, kWaiting);
        if (slot.state.load(std::memory_order_acquire) == kReady) break;
      }
    }
    const bool ok = slot.ok.load(std::memory_order_relaxed) != 0;
    slot.state.store(kEmpty, std::memory_order_relaxed);
    return ok;
  }
};

void worker(Queue& queue, std::vector<ReplySlot>& slots, const Config& cfg,
            std::atomic<std::uint64_t>& seq) {
  ShardCore core(cfg, seq);
  for (;;) {
    const Request r = queue.pop();
    bool ok = false;
    switch (r.kind) {
      case Kind::Create: ok = core.create_context(r.ue_id, r.create).has_value(); break;
      case Kind::Setup: ok = core.setup_connection(r.ue_id).has_value(); break;
      case Kind::Signal: ok = core.handle_signaling(r.ue_id, r.signaling).has_value(); break;
      case Kind::AddDrb: ok = core.add_drb(r.ue_id, r.drb).has_value(); break;
      case Kind::BeginReconf: ok = core.begin_reconfigure(r.ue_id, r.reconfig).has_value(); break;
      case Kind::CompleteReconf: ok = core.complete_reconfigure(r.ue_id).has_value(); break;
      case Kind::AbortReconf: ok = core.abort_reconfigure(r.ue_id).has_value(); break;
      case Kind::Release: ok = core.release_context(r.ue_id).has_value(); break;
      case Kind::Stop: return;
    }
    ReplySlot& slot = slots[r.reply];
    slot.ok.store(ok ? 1 : 0, std::memory_order_relaxed);
    if (slot.state.exchange(kReady, std::memory_order_release) == kWaiting)
      futex_wake_one(slot.state);
  }
}

// --- Harness -------------------------------------------------------------------------------

struct Args {
  std::string design = "matched";
  std::uint64_t shards = 7;
  std::uint64_t producers = 7;
  std::uint64_t active_ues = 5000;
  double duration_s = 3.0;
  double warmup_s = 1.0;
  std::uint64_t seed = 42;
  bool self_test = false;
  bool json = false;
};

Args parse(int argc, char** argv) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    const std::string k = argv[i];
    auto val = [&]() -> const char* { return (i + 1 < argc) ? argv[++i] : "0"; };
    if (k == "--design") a.design = val();
    else if (k == "--shards") a.shards = std::strtoull(val(), nullptr, 10);
    else if (k == "--producers") a.producers = std::strtoull(val(), nullptr, 10);
    else if (k == "--active-ues") a.active_ues = std::strtoull(val(), nullptr, 10);
    else if (k == "--duration-s") a.duration_s = std::strtod(val(), nullptr);
    else if (k == "--warmup-s") a.warmup_s = std::strtod(val(), nullptr);
    else if (k == "--seed") a.seed = std::strtoull(val(), nullptr, 10);
    else if (k == "--self-test") a.self_test = true;
    else if (k == "--json") a.json = true;
    else { std::fprintf(stderr, "unknown arg: %s\n", k.c_str()); std::exit(2); }
  }
  if (a.design != "matched" && a.design != "stock") {
    std::fprintf(stderr, "--design must be matched or stock\n");
    std::exit(2);
  }
  if (a.shards == 0 || a.producers == 0) {
    std::fprintf(stderr, "--shards and --producers must be positive\n");
    std::exit(2);
  }
  return a;
}

// (user CPU s, sys CPU s) for the whole process.
std::pair<double, double> cpu_times() {
  rusage ru{};
  getrusage(RUSAGE_SELF, &ru);
  return {ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6,
          ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6};
}

// The same mapping from a generated operation to its arguments as bench.cpp.
Request request_for(const WOp& op, UeId id, std::uint32_t reply) {
  Request r;
  r.reply = reply;
  r.ue_id = id;
  switch (op.kind) {
    case WKind::Create:
      r.kind = Kind::Create;
      r.create.serving_cell_id = static_cast<std::uint32_t>(op.slot);
      break;
    case WKind::Setup: r.kind = Kind::Setup; break;
    case WKind::Signal:
      r.kind = Kind::Signal;
      r.signaling.kind = 1;
      r.signaling.payload_len = 4;
      break;
    case WKind::AddDrb:
      r.kind = Kind::AddDrb;
      r.drb = DrbEntry{op.drb_id, 0, static_cast<std::uint32_t>(op.slot)};
      break;
    case WKind::BeginReconf:
      r.kind = Kind::BeginReconf;
      r.reconfig.target_cell_id = static_cast<std::uint32_t>(op.slot + 1);
      break;
    case WKind::CompleteReconf: r.kind = Kind::CompleteReconf; break;
    case WKind::AbortReconf: r.kind = Kind::AbortReconf; break;
    case WKind::Release: r.kind = Kind::Release; break;
  }
  return r;
}

struct SenderOut {
  std::uint64_t ops = 0;
  std::uint64_t errors = 0;
};

struct Drive {
  std::vector<SenderOut> outs;
  std::pair<double, double> cpu0, cpu1;
};

// Senders send back to back. Operations that finish inside [t0, t1] are counted, and
// process CPU is read at t0 and t1.
template <class B>
Drive drive(B& b, const Args& a) {
  const auto start = clock_type::now();
  const auto t0 = start + std::chrono::duration_cast<clock_type::duration>(
                              std::chrono::duration<double>(a.warmup_s));
  const auto t1 = t0 + std::chrono::duration_cast<clock_type::duration>(
                           std::chrono::duration<double>(a.duration_s));
  Drive d;
  d.outs.resize(a.producers);
  std::vector<std::thread> ts;
  for (std::uint64_t p = 0; p < a.producers; ++p) {
    ts.emplace_back([&, p]() {
      Workload wl(a.active_ues, a.seed + p);
      const std::uint64_t base = p * 100000000ULL + 1;
      SenderOut out;
      for (;;) {
        const WOp op = wl.next();
        const bool ok = b.exec(p, request_for(op, base + op.slot, static_cast<std::uint32_t>(p)));
        const auto done = clock_type::now();
        if (done >= t1) break;
        if (done >= t0) {
          ++out.ops;
          if (!ok) ++out.errors;
        }
      }
      d.outs[p] = out;
    });
  }
  std::this_thread::sleep_until(t0);
  d.cpu0 = cpu_times();
  std::this_thread::sleep_until(t1);
  d.cpu1 = cpu_times();
  for (auto& t : ts) t.join();
  return d;
}

// Runs f with the matched mini-service up, then stops its workers.
template <class F>
auto with_matched(const Args& a, F f) {
  Matched m(a.shards, a.producers);
  Config cfg;
  cfg.n_shards = a.shards;
  std::atomic<std::uint64_t> seq{0};
  std::vector<std::thread> workers;
  for (std::uint64_t s = 0; s < a.shards; ++s)
    workers.emplace_back([&, s]() { worker(m.queues[s], m.slots, cfg, seq); });
  auto result = f(m);
  for (auto& q : m.queues) q.push(Request{});
  for (auto& t : workers) t.join();
  return result;
}

template <class F>
auto with_stock(const Args& a, F f) {
  Config cfg;
  cfg.n_shards = a.shards;
  Stock stock(cfg);
  stock.svc.start();
  auto result = f(stock);
  stock.svc.shutdown();
  return result;
}

struct Sequence {
  std::uint64_t ok = 0;
  std::uint64_t err = 0;
  std::array<std::uint64_t, 8> kinds{};
  bool operator==(const Sequence&) const = default;
};

// One sender, n generated operations: ok count, error count, per-kind ok counts.
template <class B>
Sequence sequence(B& b, const Args& a, std::uint64_t n) {
  Workload wl(a.active_ues, a.seed);
  Sequence s;
  for (std::uint64_t i = 0; i < n; ++i) {
    const WOp op = wl.next();
    if (b.exec(0, request_for(op, 1 + op.slot, 0))) {
      ++s.ok;
      ++s.kinds[static_cast<std::size_t>(op.kind)];
    } else {
      ++s.err;
    }
  }
  return s;
}

void print_sequence(const char* name, const Sequence& s) {
  std::printf("%s ok %llu err %llu kinds [", name, (unsigned long long)s.ok,
              (unsigned long long)s.err);
  for (std::size_t i = 0; i < s.kinds.size(); ++i)
    std::printf("%s%llu", i ? ", " : "", (unsigned long long)s.kinds[i]);
  std::printf("]");
}

}  // namespace

int main(int argc, char** argv) {
  const Args a = parse(argc, argv);
  if (a.self_test) {
    const std::uint64_t n = 20000;
    const Sequence s = with_stock(a, [&](Stock& b) { return sequence(b, a, n); });
    const Sequence m = with_matched(a, [&](Matched& b) { return sequence(b, a, n); });
    std::printf("self-test cpp: ");
    print_sequence("stock", s);
    std::printf(" | ");
    print_sequence("matched", m);
    std::printf("\n");
    return s == m ? 0 : 1;
  }
  const Drive d = a.design == "matched"
                      ? with_matched(a, [&](Matched& b) { return drive(b, a); })
                      : with_stock(a, [&](Stock& b) { return drive(b, a); });
  std::uint64_t ops = 0, errors = 0;
  for (const auto& o : d.outs) {
    ops += o.ops;
    errors += o.errors;
  }
  const double user = d.cpu1.first - d.cpu0.first;
  const double sys = d.cpu1.second - d.cpu0.second;
  const double ops_per_s = ops / a.duration_s;
  const double cpu_us_per_op = ops > 0 ? (user + sys) / ops * 1e6 : 0.0;
  const double us_per_op_per_sender = ops > 0 ? a.producers * a.duration_s / ops * 1e6 : 0.0;
  if (a.json) {
    std::printf(
        "{\"schema\":\"matched\",\"lang\":\"cpp\",\"alloc\":\"%s\",\"design\":\"%s\","
        "\"shards\":%llu,\"producers\":%llu,\"active_ues\":%llu,\"seed\":%llu,\"duration_s\":%.3f,"
        "\"warmup_s\":%.3f,\"ops\":%llu,\"errors\":%llu,\"ops_per_s\":%.1f,"
        "\"us_per_op_per_sender\":%.4f,\"cpu_user_s\":%.4f,\"cpu_sys_s\":%.4f,"
        "\"cpu_us_per_op\":%.4f}\n",
        UECM_ALLOC_NAME, a.design.c_str(), (unsigned long long)a.shards,
        (unsigned long long)a.producers, (unsigned long long)a.active_ues,
        (unsigned long long)a.seed, a.duration_s, a.warmup_s, (unsigned long long)ops,
        (unsigned long long)errors, ops_per_s, us_per_op_per_sender, user, sys, cpu_us_per_op);
  } else {
    std::printf(
        "UECM matched probe [cpp, alloc=%s, design=%s] ops/s=%.0f us/op/sender=%.3f "
        "cpu us/op=%.3f errors=%llu\n",
        UECM_ALLOC_NAME, a.design.c_str(), ops_per_s, us_per_op_per_sender, cpu_us_per_op,
        (unsigned long long)errors);
  }
  return 0;
}
