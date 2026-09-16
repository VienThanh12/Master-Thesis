# Chapter 7 — Service, the threaded wrapper

**Open:** `cpp/include/uecm/service.hpp`, then `cpp/src/service.cpp`.

## The claim this layer makes

`Service` is N copies of chapter 5, each behind a chapter 6 queue, plus
lifecycle. The typed methods you would call from a test or the benchmark
are thin: fill a `Request`, `submit`, unwrap the variant. All domain
behaviour still lives in `ShardCore`.

## The inner `Shard`

```text
struct Shard {
  BoundedQueue<Request> queue;
  unique_ptr<ShardCore> core;
  thread worker;
};
```

`Service` holds `vector<unique_ptr<Shard>>`. Unique pointers so the objects
sit still while threads capture references to them. Copy and assignment of
`Service` are deleted. A destructor calls `shutdown()`.

`n_shards == 0` becomes 1 in the constructor. That protects routing. It
does not protect the free function `shard_index`.

## Lifecycle

`start()`:

1. Refuse if already running (idempotent).
2. Build N shards (each constructs its queue and `ShardCore`, which
   reserves the map).
3. Set `running_ = true`.
4. Spawn one `std::thread` per shard, each running `worker_loop`.

`running_` is set **before** the spawn loop. If `std::thread` construction
threw mid-spawn, ops could be accepted against a shard with no consumer.
Unrealistic on the measurement host. Rust sets `running` only after the
spawn loop. Logged as a nit.

`shutdown()`:

1. Refuse if not running (idempotent).
2. Enqueue `OpKind::Stop` on every shard. FIFO means in-flight requests
   drain first.
3. Join every worker.
4. Clear `running_`, destroy the shards (and their queues).

Sequential misuse (call an op before `start` or after `shutdown`) throws
`std::logic_error`. That path is tested.

**Concurrent `shutdown()` while another thread is still submitting is a
data race** on the plain `bool running_`, and can enqueue work after `Stop`
or touch a destroyed queue. Rust `shutdown` takes `&mut self`, so that
aliasing does not compile. Benches join producers before shutdown. The
parity suite never concurrent-shutdowns. Leave it as a language difference
unless you are changing the compared concurrency model. See
`docs/CODE_REVIEW.md` finding 3.

## The worker

`worker_loop` is an infinite `pop` / `switch (kind)` / `set_value`. `Stop`
returns from the function, which ends the thread. Every other arm calls the
matching `ShardCore` method and wraps the result in the `Response` variant.

There is no default arm. A new `OpKind` that you forget to handle is a
compile error if you add it to the enum and the switch is exhaustive on
this compiler's warnings. Treat a new op as a four-file change: spec,
`message.hpp`, this switch, the typed method.

## `submit`

```text
if (!running_) throw logic_error
req.kind = kind
req.ue_id = ue_id
fut = req.completion.get_future()     // before the move
s = shard_index(ue_id, cfg_.n_shards)
shards_[s]->queue.push(move(req))
return fut.get()
```

Routing uses the **clamped** `cfg_.n_shards`. The typed methods then
`std::get<TheRightAlternative>(…)` the variant. A mismatch between `kind`
and the alternative the worker stored is `std::bad_variant_access`. That
would be an internal bug, not an `OpError`.

`count()` does not go through `submit`. It loops shards 0 .. N-1, enqueues
a `Count` request on each, and sums. Ids are not involved, so
`shard_index` cannot help. Under concurrent mutation the sum is not a
point-in-time snapshot. Spec §6.7.

## The typed API

Ten methods, one per §6 operation. Each is four to eight lines. Read one
mutating method and `lookup`. You have read them all. `handle_signaling` is
the one that carries a payload field onto the request.

## A check

```bash
cmake --build cpp/build --target test_service test_concurrency
./cpp/build/test_service
./cpp/build/test_concurrency
```

Then pick `create_context` in `service.cpp` and write the thread story:

1. Caller thread fills `Request`, takes the future, computes the shard,
   blocks in `push` or in `fut.get`.
2. Worker thread wakes, `pop`s, runs `ShardCore::create_context`,
   `set_value`.
3. Caller thread returns `OpResult<void>` to its own caller.

If you can tell that story for `lookup` as well (same handoff, const method
on the core, by-value view), the library is in your head.

## Do not

Do not add a lock around `running_` as a casual patch. Shared mutable
state is what the model is designed not to have on the compared arm. Do
not make `count()` atomic across shards. Do not skip `test_concurrency`
because `test_service` already "uses threads". `test_service` is the
functional path plus a load smoke test. FIFO, 1:1 completion, and capacity-1
backpressure live in `test_concurrency`.
