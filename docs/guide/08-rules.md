# 08 Rules of the house

This is a short working copy of the load-bearing rules. The full text,
including grade history, is [`AGENT.md`](../../AGENT.md). If this page and
that file disagree, **`AGENT.md` wins**.

## Before any thesis, plan, benchmark, or artefact edit

Read `AGENT.md`. Then judge the change against the grade criteria. The bar is
submission quality.

## Document roles (do not mix)

- `Thesis_Plan_v2` and `Thesis_v3` are supervisor-facing and reviewed.
- `Ha_Vien_Mastersthesis_2026` is the canonical full draft and still needs
  review. The submission filename is not a review stamp.
- `Ha_Vien_Mastersthesis_2026_short` is a compression pass, not a deliverable.
- Do not expand `Thesis_v3.tex` chapters 2-8 beyond five argument paragraphs.
- Do not replace Chapter 1 of the skeleton with a shorter stub.

## Sync when claims or numbers move

**Claims, RQs, methodology, contributions:** update the skeleton if the
supervisor should see it, the plan if status or timeline moved, and the full
draft for the long argument. Rebuild the affected PDFs.

**Measured numbers:** `bench/refresh_thesis.sh`. Never hand-edit
`figures/gen_*.tex`. Re-read every prose site that cites those macros. Rebuild
`Thesis_v3.tex` yourself. The refresh script does not.

## Non-negotiable claims

1. Frozen spec + parity suite. Interleaved design + Holm-corrected paired tests.
2. RQ2 catalogue is 7 in-guarantee + 7 boundary. Both tables are generated.
   `seam_double_free` is `double_free` through `unsafe`, not a new class.
3. Never quote the TSan deadlock rate from memory. Read `taxonomy.csv`.
4. Measurement host is **bare metal** as of 27 August 2026. Far tail below
   saturation is resolved there and favours Rust. Guest retained only for
   host compare. **Never add `isolcpus`.**
5. Do not claim guest and reported campaigns share a toolchain (`\GuestGpp`
   15.1.1 vs `\MainGpp` 15.2.1). Quote the macros.
6. Far tail is **pooled**, never a median of per-run p99.99. No fallback to
   the per-run field. That column is outside the Holm family.
7. Saturation is not a shared knee. Quote `\TrackingLoadRust` and
   `\TrackingLoadCpp`, not `\SatKnee`, for where a variant stops coping.
8. Peak RSS: language effect on all three hosts, allocator effect
   host-dependent. Never write that the allocator effect is the larger one
   without naming a host. Do not claim hugepage causation.
9. End-to-end sweep ≈ handoff cost. Do not bound a language effect from it.
10. Rust: data races and aliasing at compile time. **Not** race conditions or
    deadlocks.
11. RQ4: never quote the shipped binary-size ratio alone. Never quote full
    build time without the dependency decomposition. C++ `unsafe` cell stays
    `---`. Build-time absolutes describe a machine. The paired ratio travels.
12. Quote numbers via `figures/gen_macros.tex` macros. Never transcribe them.

## What agents must not do

- Treat the full-draft PDF as supervisor-approved.
- Hand-edit generated files under `figures/` (except you do not: diagrams
  live in `diagrams/`).
- Transcribe measured numbers into `build_deck.py`.
- Leave an em dash or a semicolon where a reader can see one.
- Claim testbed-grade tails from a virtualised host.
- Remove boundary defect classes to tidy the narrative.
- Move document sources or prose screens out of the root.
- Commit secrets, Nokia-internal identifiers, or confidential traces.
- Create git commits unless the author explicitly asks.

## After a substantive change

Parity and tests as in `AGENT.md` §5 (`spec/conformance/run.sh`, C++/Rust
tests, `faults/run_faults.sh`, and the rest that the change actually touches).
Rebuild the affected PDFs. Zero LaTeX errors, no undefined refs.

`ffi/build.sh` and `adoption_cost.py --measure` overwrite tracked evidence.
Do not run them as smoke tests on a noisy laptop without restoring the JSON.
