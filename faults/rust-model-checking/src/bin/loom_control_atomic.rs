//! Positive control for `loom_lost_update`: the whole read-modify-write held
//! inside one critical section.
//!
//! Expected outcome: clean. This is the one-line fix for the defect, and no
//! interleaving loses an increment once it is applied, which is what makes the
//! defect run's report attributable to the defect rather than to the model.

use loom::sync::{Arc, Mutex};
use loom::thread;

use uecm_model_checking::CLEAN_MARKER;

fn main() {
    loom::model(|| {
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
    });

    println!("{CLEAN_MARKER} loom_control_atomic");
}
