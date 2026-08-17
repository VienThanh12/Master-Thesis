//! Loom model of the lock-order deadlock (`faults/rust/deadlock.rs`).
//!
//! One thread takes src then dst; the other takes dst then src. Ownership
//! tracks aliasing, not acquisition order, so safe Rust compiles the inversion
//! and the program hangs. Loom enumerates the interleavings permitted by the
//! C11 model and reaches the one where each thread holds one lock and waits for
//! the other.
//!
//! Expected outcome: loom reports a deadlock and the process exits non-zero.
//! The `thread::sleep` the runnable version uses to widen the window is absent:
//! loom controls the schedule, so a sleep would only slow it down.

use loom::sync::{Arc, Mutex};
use loom::thread;

use uecm_model_checking::CLEAN_MARKER;

fn main() {
    loom::model(|| {
        let src = Arc::new(Mutex::new(0u64));
        let dst = Arc::new(Mutex::new(0u64));

        let (s1, d1) = (Arc::clone(&src), Arc::clone(&dst));
        let t1 = thread::spawn(move || {
            let mut a = s1.lock().unwrap();
            let mut b = d1.lock().unwrap();
            *a += 1;
            *b += 1;
        });

        let (s2, d2) = (Arc::clone(&src), Arc::clone(&dst));
        let t2 = thread::spawn(move || {
            // Inverted acquisition order: this is the whole defect.
            let mut b = d2.lock().unwrap();
            let mut a = s2.lock().unwrap();
            *b += 1;
            *a += 1;
        });

        t1.join().unwrap();
        t2.join().unwrap();
    });

    println!("{CLEAN_MARKER} loom_deadlock");
}
