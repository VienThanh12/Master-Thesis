// Rust counterpart to cpp/forgotten_guard.cpp (a lock never released).
//
// Boundary case: this COMPILES and stops exactly as the C++ version does.
//
// Rust removes the *ordinary* form of this bug. The guard unlocks when it is
// dropped, so the early return that strands the C++ lock cannot strand this one,
// and there is no hand-written unlock to forget. What it does not remove is the
// bug itself, because a guard is a value and a value can be leaked. `mem::forget`
// is a safe function, and it stands here for any path that moves a guard
// somewhere outliving the procedure that took it.
//
// The row this produces is the liveness counterpart to the reference-cycle leak.
// There a leak costs memory, here it costs the context: ownership decides when a
// value is dropped, not whether it must be.
use std::mem;
use std::sync::{Arc, Mutex};
use std::thread;

struct UeContext {
    ue_id: u64,
    bearers: u64,
}

fn setup_bearer(ctx: &Mutex<UeContext>, teid: u64) -> bool {
    let mut guard = ctx.lock().unwrap();
    if teid == 0 {
        println!("rejecting bearer with zero TEID");
        mem::forget(guard); // the guard never drops, so the lock never releases
        return false;
    }
    guard.bearers += 1;
    true
}

fn main() {
    let ctx = Arc::new(Mutex::new(UeContext {
        ue_id: 1001,
        bearers: 0,
    }));

    setup_bearer(&ctx, 0);
    println!("context locked and not released; next worker will block");

    // Another shard worker touches the same context.
    let shared = Arc::clone(&ctx);
    let worker = thread::spawn(move || setup_bearer(&shared, 4711));
    worker.join().unwrap(); // never returns

    println!("bearers={}", ctx.lock().unwrap().bearers);
}
