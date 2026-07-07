// Rust counterpart to cpp/uaf.cpp (use-after-free).
// The borrow checker forbids mutating the map (remove) while a reference `p` into
// it is still live, so the use-after-free cannot be written. Expected: E0499/E0502.
use std::collections::HashMap;

struct UeContext {
    messages_handled: u64,
}

fn main() {
    let mut ctxs: HashMap<u64, UeContext> = HashMap::new();
    ctxs.insert(1001, UeContext { messages_handled: 0 });

    let p = ctxs.get_mut(&1001).unwrap(); // mutable borrow of ctxs starts here
    ctxs.remove(&1001); // second borrow of ctxs while `p` is live -> rejected
    p.messages_handled += 1; // `p` used after, keeping the first borrow alive
    println!("messages_handled={}", p.messages_handled);
}
