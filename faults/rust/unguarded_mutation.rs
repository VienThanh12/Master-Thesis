// Rust counterpart to cpp/unguarded_mutation.cpp (unguarded shared mutation).
// To share one counter across threads, the closures must capture `&mut counter`.
// A mutable borrow cannot be shared across threads and cannot escape into a
// `'static` closure, so the unsynchronized shared mutation is rejected at compile
// time. (Sharing safely would require Arc<Mutex<..>> or an atomic.)
use std::thread;

fn main() {
    let mut counter: u64 = 0;
    let shared = &mut counter;

    let mut handles = Vec::new();
    for _ in 0..4 {
        handles.push(thread::spawn(|| {
            for _ in 0..250000 {
                *shared += 1; // aliased &mut shared across threads -> rejected
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    println!("counter={}", counter);
}
