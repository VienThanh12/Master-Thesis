//! Positive control for `loom_deadlock`: the same handover with a consistent
//! lock order.
//!
//! Expected outcome: clean. Without this, a loom setup that reported on
//! everything would be indistinguishable from one that found the inversion.
//! Same role as `faults/cpp/deadlock_control.cpp` on the C++ side, inverted:
//! there the control proves the detector fires, here it proves it does not fire
//! spuriously.

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
    });

    println!("{CLEAN_MARKER} loom_control_lock_order");
}
