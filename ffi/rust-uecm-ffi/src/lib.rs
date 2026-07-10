//! RQ4 FFI seam: a C-ABI wrapper over the Rust `uecm` service.
//!
//! This crate demonstrates *incremental adoption* — dropping a Rust component
//! into a C++ codebase behind a C ABI. Key properties for the migration study:
//!
//! * The core Rust library (`../../rust`) is **not modified** to be callable from
//!   C++; all interop lives here, in a separate crate.
//! * `unsafe` is confined to this seam (raw-pointer handling at the boundary); the
//!   underlying service remains `unsafe`-free. This is the FFI safety boundary the
//!   thesis discusses: safety is *re-established* at the seam and guaranteed again
//!   inside.
//! * The handle is opaque to C++: the caller only ever holds a `UecmService*` and
//!   cannot reach into Rust-owned state, preserving the shared-nothing invariant.
//!
//! Status convention (mirrors spec §6.6): `0` = Ok; a positive value `1 + code`
//! encodes the `OpError` (NotFound=0 → 1, …, InvalidArgument=4 → 5); `-1` = null
//! handle / null out-pointer misuse from C++.
//!
//! # Safety contract (shared by all `unsafe extern "C"` entry points)
//! `h` must be a handle previously returned by [`uecm_service_create`] and not yet
//! destroyed, or null (null is checked and reported as `UECM_ERR_NULL`). Any
//! non-null `out_*` pointer must point to writable storage of the stated type.
//! This single contract, also stated in `uecm_ffi.h`, applies to every function
//! below, so we suppress the per-function lint rather than repeat it verbatim.
#![allow(clippy::missing_safety_doc)]

use uecm::{Config, CreateParams, DrbEntry, OpError, OpResult, Service, SignalingMsg};

/// Opaque handle wrapping the running service. C++ only sees a `UecmService*`.
pub struct UecmService {
    inner: Service,
}

pub const UECM_OK: i32 = 0;
pub const UECM_ERR_NULL: i32 = -1;

/// Map an `OpResult<T>` to the C status convention.
#[inline]
fn status<T>(r: OpResult<T>) -> i32 {
    match r {
        Ok(_) => UECM_OK,
        Err(e) => 1 + e as i32,
    }
}

/// Borrow the service from a raw handle, returning `None` for null.
///
/// # Safety
/// `h` must be a pointer previously returned by `uecm_service_create` and not yet
/// destroyed, or null.
#[inline]
unsafe fn as_service<'a>(h: *mut UecmService) -> Option<&'a UecmService> {
    if h.is_null() {
        None
    } else {
        Some(&*h)
    }
}

/// Create and start a service with `n_shards` workers and the given per-shard
/// queue capacity. Returns an owning handle; free it with `uecm_service_destroy`.
#[no_mangle]
pub extern "C" fn uecm_service_create(n_shards: u64, queue_capacity: u32) -> *mut UecmService {
    let cfg = Config {
        n_shards: if n_shards == 0 { 1 } else { n_shards },
        queue_capacity: queue_capacity as usize,
        ..Config::default()
    };
    let mut inner = Service::new(cfg);
    inner.start();
    Box::into_raw(Box::new(UecmService { inner }))
}

/// Stop workers and free the service. After this the handle is invalid.
///
/// # Safety
/// `h` must come from `uecm_service_create` and must not be used afterwards.
#[no_mangle]
pub unsafe extern "C" fn uecm_service_destroy(h: *mut UecmService) {
    if !h.is_null() {
        drop(Box::from_raw(h)); // Service::drop() shuts the workers down
    }
}

#[no_mangle]
pub unsafe extern "C" fn uecm_create_context(
    h: *mut UecmService,
    ue_id: u64,
    serving_cell_id: u32,
) -> i32 {
    match as_service(h) {
        None => UECM_ERR_NULL,
        Some(s) => status(s.inner.create_context(
            ue_id,
            CreateParams {
                serving_cell_id,
                security_key: [0u8; 32],
            },
        )),
    }
}

#[no_mangle]
pub unsafe extern "C" fn uecm_setup_connection(h: *mut UecmService, ue_id: u64) -> i32 {
    match as_service(h) {
        None => UECM_ERR_NULL,
        Some(s) => status(s.inner.setup_connection(ue_id)),
    }
}

/// Apply one signaling message. On success writes the updated message count to
/// `out_new_count` (if non-null).
#[no_mangle]
pub unsafe extern "C" fn uecm_handle_signaling(
    h: *mut UecmService,
    ue_id: u64,
    kind: u8,
    payload_len: u16,
    out_new_count: *mut u64,
) -> i32 {
    let s = match as_service(h) {
        None => return UECM_ERR_NULL,
        Some(s) => s,
    };
    let msg = SignalingMsg {
        kind,
        payload_len,
        payload: [0u8; 64],
    };
    match s.inner.handle_signaling(ue_id, msg) {
        Ok(ack) => {
            if !out_new_count.is_null() {
                *out_new_count = ack.new_messages_handled;
            }
            UECM_OK
        }
        Err(e) => 1 + e as i32,
    }
}

#[no_mangle]
pub unsafe extern "C" fn uecm_add_drb(
    h: *mut UecmService,
    ue_id: u64,
    drb_id: u8,
    qos_flow_id: u8,
    teid: u32,
) -> i32 {
    match as_service(h) {
        None => UECM_ERR_NULL,
        Some(s) => status(s.inner.add_drb(
            ue_id,
            DrbEntry {
                drb_id,
                qos_flow_id,
                teid,
            },
        )),
    }
}

#[no_mangle]
pub unsafe extern "C" fn uecm_release_context(h: *mut UecmService, ue_id: u64) -> i32 {
    match as_service(h) {
        None => UECM_ERR_NULL,
        Some(s) => status(s.inner.release_context(ue_id)),
    }
}

/// Look up a context; on success writes its state (as the `UeState` u8) and its
/// `messages_handled` counter to the out-pointers (if non-null).
#[no_mangle]
pub unsafe extern "C" fn uecm_lookup(
    h: *mut UecmService,
    ue_id: u64,
    out_state: *mut u8,
    out_messages_handled: *mut u64,
) -> i32 {
    let s = match as_service(h) {
        None => return UECM_ERR_NULL,
        Some(s) => s,
    };
    match s.inner.lookup(ue_id) {
        Ok(view) => {
            if !out_state.is_null() {
                *out_state = view.state as u8;
            }
            if !out_messages_handled.is_null() {
                *out_messages_handled = view.messages_handled;
            }
            UECM_OK
        }
        Err(e) => 1 + e as i32,
    }
}

/// Total live contexts across all shards.
#[no_mangle]
pub unsafe extern "C" fn uecm_count(h: *mut UecmService) -> u64 {
    match as_service(h) {
        None => 0,
        Some(s) => s.inner.count(),
    }
}

/// Minimal boundary-cost probe: does nothing but cross the C ABI and return.
/// Used by the host to measure the *raw* FFI crossing cost in isolation, separate
/// from the service's cross-thread op round-trip. Takes/returns a scalar so the
/// call cannot be optimised away by the caller.
#[no_mangle]
pub extern "C" fn uecm_abi_noop(x: u64) -> u64 {
    x.wrapping_add(1)
}

/// Human-readable name for a status code (for diagnostics on the C++ side).
#[no_mangle]
pub extern "C" fn uecm_status_str(code: i32) -> *const std::os::raw::c_char {
    let s: &'static str = match code {
        UECM_OK => "Ok\0",
        UECM_ERR_NULL => "NullHandle\0",
        c if (1..=5).contains(&c) => match c - 1 {
            x if x == OpError::NotFound as i32 => "NotFound\0",
            x if x == OpError::AlreadyExists as i32 => "AlreadyExists\0",
            x if x == OpError::InvalidState as i32 => "InvalidState\0",
            x if x == OpError::CapacityExceeded as i32 => "CapacityExceeded\0",
            _ => "InvalidArgument\0",
        },
        _ => "Unknown\0",
    };
    s.as_ptr() as *const std::os::raw::c_char
}
