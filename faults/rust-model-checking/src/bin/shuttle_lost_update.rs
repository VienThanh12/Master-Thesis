//! Shuttle model of the lost update (`faults/rust/lost_update.rs`).
//!
//! The lock is released between the read and the write, so two threads can read
//! the same value and one increment is discarded. Synchronised throughout, so
//! there is no data race and nothing for the type system or a race detector to
//! report; the atomicity of the composition is what is broken.
//!
//! Expected outcome: the assertion fails under a schedule Shuttle samples, and
//! the process exits non-zero with a replay string.
//!
//! One iteration per thread, against 20 000 in the runnable version, for the
//! same reason as the loom model: the checker needs the interleaving to be
//! reachable, not probable.

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
        },
        ITERATIONS,
        PCT_DEPTH,
    );

    println!("{CLEAN_MARKER} shuttle_lost_update");
}
