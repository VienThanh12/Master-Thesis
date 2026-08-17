//! Report the in-memory size and layout of the compared record types.
//!
//! The counterpart of `cpp/tools/layout_probe.cpp`. Section 6.2.1 and
//! Section 6.4.5 of the thesis quote these sizes as measured values, so they are
//! measured here and reach the prose through generated macros. Both probes are
//! driven by `bench/artefact_facts.py`.
//!
//! Rust does not guarantee the layout of a `repr(Rust)` type, which is exactly
//! the property under discussion: the compiler reorders fields and the thesis
//! reports the result rather than pinning it.

use std::mem::{align_of, size_of};

use uecm::message::Request;
use uecm::types::{DrbEntry, SignalingMsg, UeContext, UeContextView};

fn main() {
    println!("ue_context_bytes={}", size_of::<UeContext>());
    println!("ue_context_align={}", align_of::<UeContext>());
    println!("ue_context_view_bytes={}", size_of::<UeContextView>());
    println!("request_bytes={}", size_of::<Request>());
    println!("signaling_msg_bytes={}", size_of::<SignalingMsg>());
    println!("drb_entry_bytes={}", size_of::<DrbEntry>());
}
