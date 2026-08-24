// Rust counterpart to cpp/thread_unsafe_sharing.cpp.
//
// Rc is the single-threaded refcounted handle, and it is `!Send` and `!Sync`,
// so the closure that captures it cannot be moved into a thread. Expected:
// E0277.
//
// This case tests a different mechanism from the rest of the in-guarantee
// group. The other four are rejected by the borrow checker, which reasons about
// one function's aliasing. Here the rejection comes from the marker traits: the
// thread-affinity rule that the C++ version could only write in a comment is
// part of the handle's type, and `thread::spawn` requires it in its signature.
// The compiler is not analysing the body at all, it is checking a bound.
use std::cell::RefCell;
use std::rc::Rc;
use std::thread;

const WORKERS: usize = 4;
const OPS_PER_WORKER: usize = 20_000;

struct UeContext {
    imsi: String,
    messages_handled: u64,
}

fn main() {
    let handle = Rc::new(RefCell::new(UeContext {
        imsi: "244091234567890".to_string(),
        messages_handled: 0,
    }));

    let mut workers = Vec::new();
    for _ in 0..WORKERS {
        let shared = Rc::clone(&handle); // cloning the handle is fine
        workers.push(thread::spawn(move || {
            // Moving it into another thread is not.
            for _ in 0..OPS_PER_WORKER {
                shared.borrow_mut().messages_handled += 1;
            }
        }));
    }
    for w in workers {
        w.join().unwrap();
    }

    println!(
        "UE '{}' handled {}",
        handle.borrow().imsi,
        handle.borrow().messages_handled
    );
}
