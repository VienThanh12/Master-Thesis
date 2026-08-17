//! Shuttle model of the lock-order deadlock (`faults/rust/deadlock.rs`).
//!
//! Where loom enumerates interleavings exhaustively, Shuttle samples them with
//! PCT (probabilistic concurrency testing), which trades loom's completeness
//! for the ability to run models loom could not finish. Running both is the
//! point: they answer "can this defect be reached" with different guarantees,
//! and the boundary classes are small enough that the exhaustive answer is also
//! available for comparison.
//!
//! Expected outcome: Shuttle reports a deadlock and the process exits non-zero.

use shuttle::sync::{Arc, Mutex};
use shuttle::thread;

use uecm_model_checking::CLEAN_MARKER;

const ITERATIONS: usize = 1_000;
const PCT_DEPTH: usize = 3;

fn main() {
    shuttle::check_pct(
        || {
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
        },
        ITERATIONS,
        PCT_DEPTH,
    );

    println!("{CLEAN_MARKER} shuttle_deadlock");
}
