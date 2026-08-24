// Rust counterpart to cpp/use_after_move.cpp (use-after-move).
//
// Moving the context into the map ends the caller's ownership of it, so the
// acknowledgement cannot be built from the moved-from binding. Expected: E0382.
//
// The contrast this case carries is not that Rust rejects the program, which is
// true of the whole in-guarantee group. It is that the C++ version has no
// runtime symptom for a sanitizer to find: a moved-from value is valid but
// unspecified, so the only evidence that anything went wrong is an empty IMSI
// in a log nobody reads.
use std::collections::HashMap;

struct UeContext {
    imsi: String,
    drb_count: u32,
}

fn main() {
    let mut store: HashMap<u64, UeContext> = HashMap::new();
    let ctx = UeContext {
        imsi: "244091234567890".to_string(),
        drb_count: 3,
    };

    store.insert(1001, ctx); // ownership of `ctx` ends here

    // Borrowing `ctx` after the move -> rejected.
    println!("admitted UE '{}' with {} bearers", ctx.imsi, ctx.drb_count);
}
