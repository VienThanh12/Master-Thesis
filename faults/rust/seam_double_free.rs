// Boundary case, Rust half: the double-free of rust/double_free.rs, rewritten
// through the `unsafe` a C ABI requires.
//
// Boundary case: this COMPILES and fails exactly as the C++ version does.
//
// rust/double_free.rs is a compile error because ownership tracks the Box and
// the second drop is a use of a moved value. A seam cannot keep that: the host
// is a C++ program, so the component must hand out a raw pointer, and
// `Box::into_raw` is precisely the operation that ends the compiler's knowledge
// of the value. From there `Box::from_raw` asserts ownership of whatever address
// it is given, and asserting it twice frees the storage twice.
//
// So this row does not report a new defect class. It reports where the same
// class moves to. The guarantee is not a property of the language alone but of
// the language plus the boundary the component is deployed behind, which is the
// boundary the migration prototype of RQ4 is built on.
struct UeContext {
    ue_id: u64,
    messages_handled: u64,
}

fn ue_context_create(ue_id: u64) -> *mut UeContext {
    Box::into_raw(Box::new(UeContext {
        ue_id,
        messages_handled: 0,
    }))
}

/// # Safety
/// The caller must pass a pointer from `ue_context_create` that has not already
/// been released. Nothing checks this, which is the defect: the obligation moved
/// from the compiler to the reviewer, and the reviewer is a comment.
unsafe fn ue_context_release(handle: *mut UeContext) {
    drop(Box::from_raw(handle));
}

fn main() {
    let handle = ue_context_create(1001);

    unsafe { ue_context_release(handle) };
    println!("released once");

    unsafe { ue_context_release(handle) }; // retransmitted release
    println!("released twice");
}
