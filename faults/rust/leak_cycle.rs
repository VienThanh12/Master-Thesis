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
use std::cell::{Cell, RefCell};
use std::rc::Rc;

thread_local! {
    static DROPPED: Cell<u32> = Cell::new(0);
}

struct UeContext {
    ue_id: u64,
    messages_handled: u64,
    // Owning back-pointer to the handover peer: this is what closes the cycle.
    // `Weak<RefCell<UeContext>>` here would be the fix, and is the same fix as
    // `std::weak_ptr` on the C++ side.
    peer: Option<Rc<RefCell<UeContext>>>,
}

// The leak is counted rather than asserted. Nothing in the default toolchain
// reports it, so without a destructor that records itself the program would end
// successfully and the run would be indistinguishable from one that collected
// both contexts.
impl Drop for UeContext {
    fn drop(&mut self) {
        DROPPED.with(|d| d.set(d.get() + 1));
    }
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
    // and live.
    let dropped = DROPPED.with(|d| d.get());
    println!("scope exited; contexts dropped: {dropped} of 2");
    std::process::exit(if dropped == 2 { 0 } else { 1 });
}
