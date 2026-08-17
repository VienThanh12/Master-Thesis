//! Loom model of the lost update (`faults/rust/lost_update.rs`).
//!
//! The lock is released between the read and the write, so both threads can
//! observe the same value and one increment is discarded. Every access is
//! synchronised, so there is no data race: nothing here violates Rust's
//! guarantee, and nothing a race detector looks for is present. What is broken
//! is the atomicity of the composition, which is a property of the algorithm.
//!
//! Expected outcome: the assertion fails under the interleaving loom finds, and
//! the process exits non-zero.
//!
//! One iteration per thread, against 20 000 in the runnable version. On
//! hardware the defect needs many iterations to become probable; loom needs it
//! only to be reachable.

use loom::sync::{Arc, Mutex};
use loom::thread;

use uecm_model_checking::CLEAN_MARKER;

fn main() {
    loom::model(|| {
        let ctx = Arc::new(Mutex::new(0u64));

        let a = Arc::clone(&ctx);
        let t1 = thread::spawn(move || {
            let seen = *a.lock().unwrap(); // read, guard dropped here
            *a.lock().unwrap() = seen + 1; // modify-write in a second section
        });

        let b = Arc::clone(&ctx);
        let t2 = thread::spawn(move || {
            let seen = *b.lock().unwrap();
            *b.lock().unwrap() = seen + 1;
        });

        t1.join().unwrap();
        t2.join().unwrap();

        let got = *ctx.lock().unwrap();
        assert_eq!(got, 2, "lost update: messages_handled={got}, expected 2");
    });

    println!("{CLEAN_MARKER} loom_lost_update");
}
