// Control for rust/seam_double_free.rs: the same seam, released once.
//
// The defect case is only informative if the checker stays quiet on the correct
// version of the same program. Without this control, "Miri reported the double
// release" and "Miri reports anything that goes through Box::from_raw" would be
// the same observation. Same reason faults/cpp/deadlock_control.cpp exists.
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
/// been released. Here it does.
unsafe fn ue_context_release(handle: *mut UeContext) {
    drop(Box::from_raw(handle));
}

fn main() {
    let handle = ue_context_create(1001);

    // The host holds the handle for the lifetime of the UE and releases it once.
    unsafe {
        (*handle).messages_handled += 1;
    }
    unsafe { ue_context_release(handle) };

    println!("released once");
}
