// Rust counterpart to cpp/double_free.cpp (double-free).
// There is no manual `free`; ownership means a value is dropped exactly once.
// Explicitly dropping twice is a use-after-move, rejected at compile time (E0382).
struct UeContext {
    ue_id: u64,
}

fn main() {
    let c = Box::new(UeContext { ue_id: 1001 });
    drop(c); // ownership of `c` moves into drop(); the Box is freed exactly once
    drop(c); // use of moved value -> rejected
}
