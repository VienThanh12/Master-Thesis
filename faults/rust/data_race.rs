// Rust counterpart to cpp/data_race.cpp (data race).
// Two threads try to borrow the same `ctx` mutably. `thread::spawn` requires the
// closure to be `Send` and `'static`, and two live `&mut` borrows alias the same
// data; both are rejected at compile time (closure-may-outlive / E0499 / Send).
use std::thread;

struct UeContext {
    messages_handled: u64,
}

fn main() {
    let mut ctx = UeContext { messages_handled: 0 };

    let work = || {
        for _ in 0..200000 {
            ctx.messages_handled += 1; // borrows `ctx` mutably
        }
    };

    let a = thread::spawn(work); // borrow escapes to another thread -> rejected
    let b = thread::spawn(work); // second aliasing mutable borrow -> rejected
    a.join().unwrap();
    b.join().unwrap();
    println!("messages_handled={}", ctx.messages_handled);
}
