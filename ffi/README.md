# FFI migration prototype (RQ4)

This directory implements the RQ4 study: *what are the practical implications
(effort, FFI interoperability, and risk) of adopting Rust incrementally within an
existing C++ RAN software ecosystem?*

It models the realistic incremental-adoption direction, **an existing C++ host
keeps a Rust component behind a C ABI**, and measures the concrete cost of the
interop seam.

## Layout

```
ffi/
  rust-uecm-ffi/            # Rust crate: thin C-ABI seam over the uecm::Service
    Cargo.toml              #   path-depends on ../../rust (the core lib, unmodified)
    src/lib.rs              #   #[no_mangle] extern "C" wrappers + opaque handle
    include/uecm_ffi.h      #   hand-written C header (the migration contract)
  cpp-host/
    main.cpp                # C++ program that only sees uecm_ffi.h + a void* handle
  build.sh                  # build Rust lib -> compile/link C++ host -> run + metrics
```

## Design decisions (and why they matter for the study)

- **The core Rust library is not touched.** All FFI lives in a *separate* crate
  (`rust-uecm-ffi`) that path-depends on `../../rust`. Incremental adoption should
  not require rewriting or annotating the component being adopted.
- **Opaque handle.** C++ only ever holds a `UecmService*`; it cannot reach into
  Rust-owned state, so the shared-nothing invariant survives the boundary.
- **Scalars only cross the seam.** Arguments and results are plain integers /
  out-pointers, so there is no serialisation/marshalling cost and no shared
  ownership of complex objects across the boundary.
- **`unsafe` is confined to the seam.** The core library remains `unsafe`-free;
  the raw-pointer handling required by the C ABI is isolated to
  `rust-uecm-ffi/src/lib.rs`, all under one documented safety contract. This is
  the FFI *safety boundary*: safety is re-established at the seam and guaranteed
  again inside.
- **Thread-safe handle.** The service is internally thread-per-shard; because
  every entry point is a submit + blocking completion, several C++ threads may
  share one handle. The host demonstrates this with a 4-thread load.

## Running

```bash
./build.sh          # needs: cargo, g++ (C++17), a Linux toolchain
```

`build.sh` builds the Rust `staticlib`+`cdylib`, links the C++ host against the
`cdylib`, runs it (functional lifecycle checks + timings), and prints the
interop-cost metrics.

## Result (this testbed)

`g++ 13.3` / `rustc 1.96`, `-O2` / release `opt-level=2`:

- **Functional parity across the seam:** the full UE lifecycle (create → setup →
  signal → add-DRB → lookup → release) works through the C ABI, and the error
  model is transported faithfully (e.g. a duplicate `setup_connection` returns
  `InvalidState`).
- **Seam size:** 11 C-ABI entry points; ~223 LOC of Rust wrapper + ~66 LOC of C
  header. No generated bindings, no third-party FFI dependency.
- **Safety boundary:** `unsafe` occurrences: **0 in the core library**, confined
  to the seam crate. The C++ side sees only an opaque handle.
- **Raw FFI crossing cost:** sub-nanosecond per call (`uecm_abi_noop`, ~0.7–1.3
  ns/call), i.e. a normal indirect function call; the boundary itself is
  effectively free.
- **End-to-end op latency** (`handle_signaling` through the seam) is tens of
  microseconds, but this is the service's cross-thread submit+complete round-trip
  that a *native* caller pays identically; it is architectural, not FFI-induced.

**Takeaway for RQ4:** for a component with a small, scalar-typed API, introducing
Rust behind a C ABI is cheap and low-risk: the boundary adds no measurable
per-call overhead, the wrapper is small, and `unsafe` stays localised to the seam
while the component's internal safety guarantees are preserved. The main
engineering cost is designing a C-compatible API surface (opaque handle + scalar
ops + a status convention) rather than any per-call tax. The reverse direction
(Rust calling into C++) is symmetric but requires a C-ABI wrapper on the C++ side
and re-introduces `unsafe` on the Rust caller.
