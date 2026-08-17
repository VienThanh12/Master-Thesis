// Rust counterpart to cpp/leak_cycle.cpp (leak through a reference cycle).
//
// Boundary case: this COMPILES and leaks exactly as the C++ version does.
// Reference counting cannot collect a cycle in either language, and leaking is
// safe in Rust by explicit design -- `mem::forget` is a safe function, and the
// standard library documents `Rc` cycles as a leak the programmer must avoid
// with `Weak`. Ownership tracks *when* a value is dropped, not *whether* the
// graph of owners is acyclic.
//
// This is the cleanest boundary in the catalogue because both languages fail
// identically, and it is the one where the tooling comparison goes the other
// way: LeakSanitizer reports the C++ version, while a stock `cargo build` and
// `cargo test` say nothing at all. Rust's guarantee does not cover leaks and
// neither does its default toolchain.
use std::cell::RefCell;
use std::rc::Rc;

struct UeContext {
    ue_id: u64,
    messages_handled: u64,
    // Owning back-pointer to the handover peer: this is what closes the cycle.
    // `Weak<RefCell<UeContext>>` here would be the fix, and is the same fix as
    // `std::weak_ptr` on the C++ side.
    peer: Option<Rc<RefCell<UeContext>>>,
}

fn main() {
    {
        let src = Rc::new(RefCell::new(UeContext {
            ue_id: 1001,
            messages_handled: 0,
            peer: None,
        }));
        let dst = Rc::new(RefCell::new(UeContext {
            ue_id: 1002,
            messages_handled: 0,
            peer: None,
        }));

        // Handover pairs the two contexts in both directions.
        src.borrow_mut().peer = Some(Rc::clone(&dst));
        dst.borrow_mut().peer = Some(Rc::clone(&src));

        src.borrow_mut().messages_handled = 7;
        dst.borrow_mut().messages_handled = 9;

        println!(
            "paired {} <-> {} (strong_count src={} dst={})",
            src.borrow().ue_id,
            dst.borrow().ue_id,
            Rc::strong_count(&src),
            Rc::strong_count(&dst)
        );
    }
    // Both roots are gone. Each context is still held by the other, so both
    // counts remain at one, neither is dropped, and the memory is unreachable
    // and live. The process exits successfully and reports nothing.
    println!("scope exited; contexts were never dropped");
}
