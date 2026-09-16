# Chapter 6 — Queue and messages

**Open:** `cpp/include/uecm/message.hpp`, then `cpp/include/uecm/bounded_queue.hpp`.

You now know what an operation is. This chapter is how an operation travels
from a caller thread to the worker that is allowed to run it.

## The claim this layer makes

Spec §7: callers submit messages, they never touch context state. Each
request carries a one-shot completion. The queue is bounded, blocking,
multi-producer / single-consumer, FIFO. C++ has no standard blocking MPSC
queue and no oneshot channel, so this layer is where the language idiom
shows. Spec §12 records the choices: tagged struct plus `std::promise`,
and a hand-written mutex queue.

## `message.hpp`

`OpKind` is every operation of §6, plus `Count`, plus `Stop`. `Stop` is not
an API op. It is the sentinel `shutdown()` enqueues so a worker can leave
its loop after draining earlier requests.

`Response` is a `std::variant` of the four result shapes:

- `OpResult<void>` for most mutating ops
- `OpResult<SignalingAck>`
- `OpResult<UeContextView>`
- `OpResult<uint64_t>` for count

Rust does not need this. Each request variant there carries a typed oneshot
of the precise result. C++ needs a single move-only `Request` type because
the queue is `BoundedQueue<Request>`. The variant lives on the way back.

`Request` is a tagged struct: one `kind`, every argument field sitting
alongside, and a `std::promise<Response> completion`. Unused argument
fields stay defaulted. That is uglier than a variant-of-payloads and is
the recorded C++ choice: `std::promise` is move-only, and keeping `Request`
itself a single move-only type is simpler than a variant that also has to
move a promise.

`Request` is therefore move-only. You will see `std::move(req)` at every
enqueue.

## The completion handshake

In `Service::submit` (next chapter) the caller does:

1. Fill a `Request`.
2. `auto fut = req.completion.get_future()` **before** the move.
3. Push the request (moves the promise to the worker).
4. `return fut.get()` (blocks until the worker `set_value`).

If you get the future **after** the move, you have moved from the promise
and the handshake is broken. Look for that ordering when you read
`service.cpp`. It is easy to "clean up" and get wrong.

If a worker dies without `set_value`, `fut.get()` throws. That is "worker
died", treated as an invariant violation, not an `OpError`.

## `bounded_queue.hpp`

A template over `T` with:

- `push(T)`: block while `size() >= capacity`, then push, notify not-empty.
- `pop()`: block while empty, then take `front`, pop, notify not-full.

Two condition variables (`not_full_`, `not_empty_`) plus one mutex. The
measured storage is `std::queue<T>` (deque-backed). The `#ifdef
UECM_RING_QUEUE` swaps in a preallocated ring. Ignore it for now. Same
locking either way. That is the point of the probe: change storage, not
synchronisation.

Capacity 0 is clamped to 1. A zero-capacity queue would be a rendezvous,
which is what Rust's `sync_channel(0)` is. The compared campaign uses 1024,
so the clamp does not move reported numbers. It is the one accidental
library mismatch if someone ever configures 0. Logged, not hidden.

`push` and `pop` unlock before `notify_one`. That is the usual pattern
(do not wake a waiter who then cannot take the mutex). Correctness does
not depend on it.

## What this queue does not do

- It does not drop work when full. It blocks. That is the overload story
  the tail-latency study exercises.
- It does not steal across shards. A full shard stays full.
- It is not lock-free. The interesting comparison is ownership transfer of
  requests, not a novel concurrent queue.

## A check

In `bounded_queue.hpp`, write down (on paper) what happens if five
producers call `push` on a queue of capacity 1 whose consumer is asleep.
Who waits on which condition variable? When the consumer `pop`s once, who
runs next? You do not need to know which producer wins (the mutex decides).
You need to know that **nothing is dropped** and that `pop` unblocks
exactly one waiter on `not_full_`.

Then glance at `cpp/tests/test_concurrency.cpp`, function
`backpressure_loses_nothing`. That is this paragraph as a test: capacity 1,
six producers, every create/setup/signal must still complete.

## Do not

Do not open `ring_queue.hpp` except to read the comment that says it is not
the compared arm. Do not replace `std::promise` with a shared
`std::optional<Response>` plus a condition variable "to simplify". Spec §7
wants a 1:1 handoff, not a shared mutable buffer.
