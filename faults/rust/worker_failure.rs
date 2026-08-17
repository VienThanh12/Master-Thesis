// Rust counterpart to cpp/worker_failure.cpp (failure inside one shard
// worker).
//
// Boundary case: this COMPILES and the shard dies. Neither ownership nor
// Send/Sync has anything to say about what happens when a worker fails
// mid-procedure, and the specified model's implied availability property --
// that a shard is a failure domain (spec §7) -- is not enforced by either
// language.
//
// The two languages fail differently, and the difference is the finding rather
// than a win for either:
//
//   C++  an exception escaping a std::thread callable calls std::terminate.
//        One malformed message kills the process and every other shard's
//        contexts with it.
//
//   Rust the panic is confined to its own thread and the others keep running,
//        which is the better outcome. But the Mutex the panicking worker held
//        is now poisoned, so every later `lock().unwrap()` on that context
//        panics too. The failure is contained at the thread boundary and then
//        propagates along the data instead.
//
// So Rust converts a process-wide abort into a shard-wide outage plus a
// poisoned resource. That is a genuine improvement in blast radius and it is
// still an outage, and a migration plan that reads "memory-safe" as
// "fault-tolerant" will mis-budget for it. Recovering properly means handling
// `PoisonError` deliberately, which is a design decision the compiler will
// never prompt for -- `unwrap()` compiles.
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

const SHARDS: usize = 8;

struct UeContext {
    messages_handled: u64,
}

fn main() {
    let handled = Arc::new(AtomicU64::new(0));
    // One context shared with the supervisor, standing in for shard state that
    // outlives the worker.
    let shared = Arc::new(Mutex::new(UeContext {
        messages_handled: 0,
    }));

    let mut workers = Vec::new();
    for shard in 0..SHARDS {
        let handled = Arc::clone(&handled);
        let shared = Arc::clone(&shared);
        workers.push(thread::spawn(move || {
            for i in 0..100 {
                let mut ctx = shared.lock().unwrap();
                if shard == 3 && i == 10 {
                    // A malformed signalling message on one shard, panicking
                    // while the lock is held. This is what poisons it.
                    panic!("unparseable signalling PDU on shard 3");
                }
                ctx.messages_handled += 1;
                handled.fetch_add(1, Ordering::Relaxed);
            }
            println!("shard {shard} finished");
        }));
    }

    let mut panicked = 0;
    for (shard, w) in workers.into_iter().enumerate() {
        if w.join().is_err() {
            panicked += 1;
            println!("shard {shard} died");
        }
    }

    // The surviving workers did not survive either: the first of them to take
    // the poisoned lock unwrapped a PoisonError and panicked in turn.
    println!(
        "workers that died: {panicked}, mutex poisoned: {}",
        shared.is_poisoned()
    );

    if panicked > 0 || shared.is_poisoned() {
        std::process::exit(1);
    }
}
