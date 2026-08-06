// Rust counterpart to cpp/lost_update.cpp (lost update).
//
// Boundary case: this one COMPILES and produces the same wrong answer. Rust's
// guarantee is the absence of *data races* -- unsynchronised concurrent access to the
// same location. Here every access is synchronised through the `Mutex`, so the type
// system is satisfied; what is broken is the atomicity of the read-modify-write, which
// is a property of the algorithm rather than of the memory model. No borrow-checker
// rule and no sanitizer addresses it.
use std::sync::{Arc, Mutex};
use std::thread;

const ITERS: u64 = 20_000;

struct UeContext {
    messages_handled: u64,
}

fn bump(ctx: &Mutex<UeContext>) {
    for _ in 0..ITERS {
        let seen = {
            let g = ctx.lock().unwrap();
            g.messages_handled // read ... lock released at end of scope
        };
        {
            let mut g = ctx.lock().unwrap();
            g.messages_handled = seen + 1; // ... modify-write: update may be lost
        }
    }
}

fn main() {
    let ctx = Arc::new(Mutex::new(UeContext { messages_handled: 0 }));
    let a = Arc::clone(&ctx);
    let b = Arc::clone(&ctx);

    let t1 = thread::spawn(move || bump(&a));
    let t2 = thread::spawn(move || bump(&b));
    t1.join().unwrap();
    t2.join().unwrap();

    let got = ctx.lock().unwrap().messages_handled;
    let expected = 2 * ITERS;
    println!(
        "messages_handled={} expected={} lost={}",
        got,
        expected,
        expected - got
    );
    std::process::exit(if got == expected { 0 } else { 1 });
}
