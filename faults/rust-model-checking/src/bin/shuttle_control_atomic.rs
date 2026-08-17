//! Positive control for `shuttle_lost_update`: the whole read-modify-write held
//! inside one critical section.
//!
//! Expected outcome: clean. This is the one-line fix, and no sampled schedule
//! loses an increment once it is applied.

use shuttle::sync::{Arc, Mutex};
use shuttle::thread;

use uecm_model_checking::CLEAN_MARKER;

const ITERATIONS: usize = 1_000;
const PCT_DEPTH: usize = 3;

fn main() {
    shuttle::check_pct(
        || {
            let ctx = Arc::new(Mutex::new(0u64));

            let a = Arc::clone(&ctx);
            let t1 = thread::spawn(move || {
                let mut g = a.lock().unwrap(); // read and write under one guard
                *g += 1;
            });

            let b = Arc::clone(&ctx);
            let t2 = thread::spawn(move || {
                let mut g = b.lock().unwrap();
                *g += 1;
            });

            t1.join().unwrap();
            t2.join().unwrap();

            let got = *ctx.lock().unwrap();
            assert_eq!(got, 2, "atomic increment lost an update: got {got}");
        },
        ITERATIONS,
        PCT_DEPTH,
    );

    println!("{CLEAN_MARKER} shuttle_control_atomic");
}
