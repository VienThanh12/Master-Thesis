# Repository encyclopedia

This guide explains **every top-level artefact in `thesis.local`**: what it is,
what it is allowed to claim, and where the detailed instructions live. It does
not replace those instructions.

Three documents already own parts of this story. Use them for the job they
were written for.

| Document | Job |
| --- | --- |
| [`../../README.md`](../../README.md) | What the thesis studies, how to build and run, status table. |
| [`../../AGENT.md`](../../AGENT.md) | Document roles, grade criteria, non-negotiable claims, verification after an edit. **Read this before changing anything.** |
| This guide | A file-by-file map, including hidden tools and generated files the README only lists. |

If two pages disagree, **`AGENT.md` wins** on claims, document status, and
what an agent must not do. The component `README.md` in `spec/`, `cpp/`,
`rust/`, `bench/`, `faults/`, `ffi/`, and `docker/` wins on how to run that
component.

## Pages

| Page | Covers |
| --- | --- |
| [01 Map](01-map.md) | Every top-level file and directory, including hidden ones. |
| [02 Documents](02-documents.md) | The PDFs and `.tex` sources, their status, how to rebuild each. |
| [03 Evidence](03-evidence.md) | `spec/`, `cpp/`, `rust/`, `bench/`, `faults/`, `ffi/`: the artefact the thesis is built on. |
| [04 Campaigns](04-campaigns.md) | Which measurement log is canonical, which prefixes must never mix, the invalid `isolcpus` campaign. |
| [05 Generated layer](05-generated.md) | `figures/`, `diagrams/`, macros, `bench/refresh_thesis.sh`. Never hand-edit generated files. |
| [06 Prose screens](06-prose.md) | `.aitells.py`, `.vocab.py`, `.b2.py`, `.readability.py`, `.acronyms.py`, `.chapter_readability.py`, diagram and slide gates. How Flesch is computed. |
| [07 Tooling](07-tooling.md) | LaTeX, Docker, the slide deck, citation audit, short-cut compression, Cursor rules and skills, PDF helpers. |
| [08 Rules of the house](08-rules.md) | Non-negotiable claims in short form, and the edit/sync rule. |

## What this thesis is

A University of Helsinki master's thesis by **Ha Vien**, Software study track,
Nokia internship. Title: *Performance, Safety, and Engineering Trade-offs of
Rust and C++ in Nokia RAN Control-Plane Systems*.

It compares two language-equivalent implementations of a **UE Context
Management (UECM)** service, modelled on a Nokia gNB-CU-CP component, along
four research questions.

| RQ | Question | Evidence |
| --- | --- | --- |
| RQ1 | Latency predictability under load and overload | `bench/` |
| RQ2 | Which C++ defect classes safe Rust eliminates, and where the guarantee stops | `faults/` |
| RQ3 | Throughput, CPU, and memory overhead of Rust's safety model | `bench/` |
| RQ4 | Incremental adoption cost of Rust inside a C++ codebase | `ffi/`, `bench/adoption_cost.py` |

The fairness control is a frozen, language-neutral specification in
`spec/SPECIFICATION.md`. Both cores must conform to it. Forced idiomatic
divergence is logged, not hidden.
