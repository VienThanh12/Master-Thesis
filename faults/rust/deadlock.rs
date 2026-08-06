// Rust counterpart to cpp/deadlock.cpp (lock-order inversion).
//
// Boundary case: this one COMPILES. Ownership and borrowing say nothing about the
// order in which locks are acquired, so safe Rust accepts the inversion and the
// program hangs exactly as the C++ version does. `Mutex` guards are ordinary values
// whose lifetimes the borrow checker tracks perfectly -- and that is beside the point.
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

struct UeContext {
    messages_handled: u64,
}

// Move accounting from `a` to `b`, holding both context locks.
fn handover(a: &Mutex<UeContext>, b: &Mutex<UeContext>) {
    for _ in 0..1000 {
        let mut ga = a.lock().unwrap();
        // Widen the window so the inversion is hit rather than being raced past.
        thread::sleep(Duration::from_micros(200));
        let mut gb = b.lock().unwrap();
        ga.messages_handled += 1;
        gb.messages_handled += 1;
    }
}

fn main() {
    let src = Arc::new(Mutex::new(UeContext { messages_handled: 0 }));
    let dst = Arc::new(Mutex::new(UeContext { messages_handled: 0 }));

    let (s1, d1) = (Arc::clone(&src), Arc::clone(&dst));
    let (s2, d2) = (Arc::clone(&src), Arc::clone(&dst));

    let t1 = thread::spawn(move || handover(&s1, &d1));
    let t2 = thread::spawn(move || handover(&d2, &s2)); // inverted lock order
    t1.join().unwrap();
    t2.join().unwrap();

    println!(
        "handovers done: src={} dst={}",
        src.lock().unwrap().messages_handled,
        dst.lock().unwrap().messages_handled
    );
}
