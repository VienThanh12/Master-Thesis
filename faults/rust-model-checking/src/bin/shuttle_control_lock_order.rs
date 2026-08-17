//! Positive control for `shuttle_deadlock`: the same handover with a consistent
//! lock order.
//!
//! Expected outcome: clean. Distinguishes "Shuttle found the inversion" from
//! "Shuttle reports on anything with two locks in it".

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
                // src before dst, the same way round as t1.
                let mut a = s2.lock().unwrap();
                let mut b = d2.lock().unwrap();
                *a += 1;
                *b += 1;
            });

            t1.join().unwrap();
            t2.join().unwrap();

            assert_eq!(*src.lock().unwrap(), 2);
            assert_eq!(*dst.lock().unwrap(), 2);
        },
        ITERATIONS,
        PCT_DEPTH,
    );

    println!("{CLEAN_MARKER} shuttle_control_lock_order");
}
