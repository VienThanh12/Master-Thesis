# 03 Evidence

The thesis is not only a `.tex` file. Claims have to match the artefact in
`spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, and `ffi/`. This page maps those
trees. Run instructions live in each directory's own `README.md`.

## `spec/` — fairness baseline

| Path | Role |
| --- | --- |
| `spec/SPECIFICATION.md` | Language-neutral specification of the UECM service. Both implementations must conform. Forced-idiom divergences are logged. Still v0.1 pending supervisor freeze. |
| `spec/conformance/model.py` | Independent Python reference model. **Never** derive its expectations from `cpp/` or `rust/`. |
| `spec/conformance/genvec.py` | Generated-vector campaign. |
| `spec/conformance/vectors/` | Hand-written parity vectors. |
| `spec/conformance/run.sh` | Three phases: oracle, hand-written vectors, generated vectors, both languages, transcripts diffed line by line. |
| `spec/conformance/results/` | Last campaign summary (`summary.json`). |

```bash
spec/conformance/run.sh
spec/conformance/run.sh --random 60 --ops 2000   # full generated campaign, ~9 min
```

## `cpp/` — C++23 core

Mirrors `rust/` module for module. Public headers under `include/uecm/`,
implementation in `src/`, parity runner in `tools/`, benchmark driver in
`bench/`, tests in `tests/` (each file a standalone `main()`, registered in
`CMakeLists.txt`).

| Extra script | Role |
| --- | --- |
| `cpp/sanitise.sh` | Whole suite under ASan+UBSan / TSan / UBSan. |
| `cpp/coverage.sh` | gcov line coverage of the parity suite. |

Pinned: C++23 (`std::expected`), matched `-O2`, SplitMix64 shard selection,
FNV-1a key hashing, jemalloc as a campaign arm (`-DUECM_USE_JEMALLOC=ON`).

Details: [`cpp/README.md`](../../cpp/README.md).

## `rust/` — Rust core

Same service, same concurrency model (thread-per-shard, bounded MPSC, one-shot
completions), `opt-level = 2` to match C++ `-O2`. Tests in `rust/tests/`
mirror `cpp/tests/` case for case.

| Extra script | Role |
| --- | --- |
| `rust/miri.sh` | Needs nightly + miri. |
| `rust/coverage.sh` | Needs `cargo-llvm-cov`. |
| `rust/examples/bench.rs` | Campaign driver, counterpart of `cpp/bench/bench.cpp`. |

The core library stays `unsafe`-free. FFI `unsafe` lives in `ffi/rust-uecm-ffi/`.

Details: [`rust/README.md`](../../rust/README.md).

## `bench/` — RQ1, RQ3, and most of RQ4's numbers

| Script | Role |
| --- | --- |
| `campaign.sh` | Full measurement campaign (repeats, interleaving, bootstrap CI). |
| `canonical_repeat.sh` | Pre-campaign hygiene. `check-spread` refuses a one-core pin. |
| `run_bench.sh` | Shorter comparison run. |
| `load_sweep.sh` | Load sweep helper. |
| `latency_budget.sh` | Split end-to-end time into work vs cross-thread handoff. |
| `queue_contention.sh`, `queue_probes.sh` | Isolate the handoff primitives. |
| `counters.sh` | Hardware counters. Needs a PMU. Refuses on WSL2. |
| `alloc_profile.sh` | Attribute peak RSS to allocation sites. Testbed only. |
| `steal_probe.sh` | CPU steal probe. |
| `setup_testbed.sh` | Install toolchain, apply CPU hygiene, verify. |
| `capture_env.sh` | Write the environment capture that host macros are built from. |
| `pool_hist.py` | Pool per-run HDR buckets. **This** is what the far-tail column reads. |
| `aggregate.py` | Campaign aggregation. |
| `plot_figures.py` | Figures, tables, and `figures/gen_macros.tex`. Pins `REPR_LOAD_OPS = 56000`. |
| `plot_campaign.py`, `plot_sweep.py` | Extra plots. |
| `baremetal_facts.py` | `\Bm*` macros → `figures/gen_baremetal.tex`. |
| `guest_facts.py` | `\Guest*` macros → `figures/gen_guest.tex`. |
| `artefact_facts.py` | Measurements no campaign log holds (parity size, seam size, taxonomy outcomes) → `gen_artefacts.tex`. |
| `complexity.py` | LoC / lizard proxies → `tab_complexity.tex`, `tab_loc.tex`, `gen_complexity.tex`. |
| `adoption_cost.py` | RQ4 build time, footprint, third-party surface. Without `--measure`, build time is replayed. |
| `parse_jeprof.py`, `parse_perf.py` | Parsers for heap dumps and `perf`. |
| `refresh_thesis.sh` | Regenerates the generated layer and rebuilds the full-draft PDF and the deck. |
| `TESTBED.md` | Bare-metal protocol. The only route to testbed-grade tails. |
| `requirements.txt` | Python plotting deps. |

Result directories: see [04 Campaigns](04-campaigns.md).

Details: [`bench/README.md`](../../bench/README.md).

## `faults/` — RQ2 catalogue

Fourteen defect classes: **seven in-guarantee** (safe Rust must refuse to
compile) and **seven boundary** (it compiles, and the study measures what
catches them later). A catalogue of only in-guarantee classes would not be
falsifiable.

| Script | Role |
| --- | --- |
| `run_faults.sh` | Build/run the catalogue. About 4 minutes. Two boundary cases hang by construction. Outcomes are categorical: safe to run on a laptop. |
| `run_model_checking.sh` | Loom and Shuttle on lock-order deadlock and lost update, plus quiet controls. |
| `run_miri.sh` | Miri on `seam_double_free` and its control. |

Sources: `faults/cpp/*.cpp` and `faults/rust/*.rs`, plus
`faults/rust-model-checking/` for Loom/Shuttle.

Tracked results: `faults/results/taxonomy.csv` (and `.md`), `model_checking.csv`,
`miri.csv`. `figures/tab_taxonomy.tex` is generated from `taxonomy.csv`. To add
a class, add it in `faults/run_faults.sh` (and `build_deck.py`'s `DEFECTS`),
do not type a table row.

**Load-bearing quirks** (from `AGENT.md` §3):

- `seam_double_free` is `double_free` rewritten through `unsafe`, not a new
  class. Keep the C++ half unchanged so only the Rust column moves.
- Never quote the TSan deadlock detection rate from memory. Read
  `taxonomy.csv`. It has been 4, 5, 7, and 9 of 12.
- Two boundary classes came back with the C++ tooling ahead (reference-cycle
  leak, release-build overflow). Keep them.
- `use_after_move` is the only in-guarantee class no C++ sanitiser reports.
- `thread_unsafe_sharing` is an `E0277` (`Send`/`Sync`) rejection, not the
  borrow checker.

Details: [`faults/README.md`](../../faults/README.md).

## `ffi/` — RQ4 seam

A C++ host talks to the unmodified Rust core through a thin C ABI crate.

| Path | Role |
| --- | --- |
| `ffi/rust-uecm-ffi/` | `#[no_mangle]` wrappers, `include/uecm_ffi.h`. |
| `ffi/cpp-host/` | C++ program that only sees the header and an opaque handle. |
| `ffi/build.sh` | Build, link, run, write `ffi/results/metrics.json` and `op_cost.jsonl`. |
| `ffi/results/` | Tracked evidence the RQ4 table and `\Ffi*` macros read. |

**`ffi/build.sh` is a measurement, not a smoke test.** It overwrites the tracked
JSON with whatever host it ran on. After a build-only check:

```bash
git checkout -- ffi/results/metrics.json ffi/results/op_cost.jsonl
```

Details: [`ffi/README.md`](../../ffi/README.md).
