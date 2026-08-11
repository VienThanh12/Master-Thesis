# Citation sources cheat sheet

Quick reference for where `bibliography.bib` metadata comes from and how to verify new entries.
See also `LITERATURE_NOTES.md` for the August 2026 literature sweep and its verification convention.

## How this repo works

| Tool | Role |
|------|------|
| **Google Scholar** | Discovery only - find candidate papers |
| **ACM DL, IEEE Xplore, USENIX** | Discovery + sometimes the authoritative page |
| **`bibliography.bib`** | Hand-written BibTeX; **not** bulk-exported from Scholar |
| **Primary sources** | Where every field is checked before an entry is added |

Workflow for a new citation:

1. Find the work (Scholar, chaining, supervisor tip, …).
2. Open the **primary source** (see table below) - not Scholar's "Cite" button alone.
3. Copy metadata into `bibliography.bib` with a consistent cite key (`authorYYYYkeyword`).
4. Add `doi` and/or `url`; set `urldate` / `note = {Accessed …}` for web-only sources.
5. Run `bibtex` and confirm the key resolves in `thesis.tex`.

---

## Source taxonomy

```
Academic / peer-reviewed          Non-academic / primary documents
├── DOI → Crossref                ├── Official sites (3GPP, CISA, EUR-Lex)
├── Publisher pages (ACM, …)      ├── Standards drafts (WG21)
├── arXiv (preprints)             └── Blogs / talks
└── USENIX / LIPIcs / DataCite
```

---

## 1. DOI / Crossref - ACM, IEEE, Elsevier

**What:** A **DOI** (`10.1145/3158154`) is a permanent ID. **Crossref** is the registry where publishers deposit metadata. **ACM / IEEE / Elsevier** host the published paper.

**When:** Normal journal and conference papers after publication. This is the default for CS papers.

**Verify at:** `https://doi.org/<doi>` → publisher page for page numbers and venue spelling.

**BibTeX:** `@article`, `@inproceedings`

**Example** (`jung2018rustbelt`):

```bibtex
@article{jung2018rustbelt,
  author  = {Jung, Ralf and ...},
  title   = {{RustBelt}: Securing the Foundations of the {Rust} Programming Language},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {2}, number = {POPL}, pages = {66:1--66:34},
  year    = {2018},
  doi     = {10.1145/3158154},
  url     = {https://doi.org/10.1145/3158154}
}
```

---

## 2. arXiv - preprints

**What:** Authors upload drafts before or during peer review. Free, fast, not the final published record.

**When:**

- Paper has no published venue yet.
- You discovered it early and need the full text.

**Rule:** Once a DOI exists, cite the **published version**, not arXiv. `LITERATURE_NOTES.md` flags several papers where the preprint would have been the wrong cite.

| | arXiv | Published (DOI) |
|---|-------|-----------------|
| Peer review | Usually none yet | Yes |
| Version | Can change (v1, v2, …) | Final |
| Cite as | `arXiv:xxxx.xxxxx` | Journal/conference + DOI |

**Verify at:** `https://arxiv.org/abs/<id>` - check the comment field for acceptance notices.

**BibTeX:** `@article` with `eprint` / `archivePrefix = {arXiv}`, or switch to `@inproceedings` after publication.

---

## 3. Publisher pages - USENIX, LIPIcs, DataCite

**What:** Publishers and registries that do not always behave like ACM/IEEE on Crossref.

| Source | Hosts | DOI? |
|--------|-------|------|
| **USENIX** | NSDI, ATC, SOUPS, … | Often **no** DOI |
| **LIPIcs** | ECOOP, ECRTS, … | Yes, via LIPIcs/DataCite |
| **DataCite** | Datasets, some reports/proceedings | Yes |

**When:** Crossref lookup fails or returns incomplete metadata. Common for USENIX proceedings.

**Verify at:** Publisher site (`usenix.org`, `drops.dagstuhl.de`) + **DBLP** as a cross-check.

**Example** (`agache2020firecracker` - USENIX, URL only):

```bibtex
@inproceedings{agache2020firecracker,
  author    = {Agache, Alexandru and ...},
  title     = {Firecracker: Lightweight Virtualization for Serverless Applications},
  booktitle = {Proceedings of the 17th USENIX Symposium on Networked Systems
               Design and Implementation (NSDI)},
  pages     = {419--434},
  year      = {2020},
  publisher = {USENIX Association},
  url       = {https://www.usenix.org/conference/nsdi20/presentation/agache}
}
```

---

## 4. Official sites - 3GPP, CISA, EUR-Lex

**What:** Primary documents from standards bodies, governments, or regulators. The document **is** the evidence.

**When:** Citing a spec clause, regulatory mandate, or legal requirement - not a paper *about* them.

| Academic paper | Official site |
|----------------|---------------|
| Authors, journal, DOI | Institution, doc number, **version**, date |
| Peer-reviewed | Authoritative by **who issued it** |
| `@article` / `@inproceedings` | `@techreport` or `@misc` |

**Examples in this bib:**

| Key | Source |
|-----|--------|
| `3gpp38401` | 3GPP TS 38.401 (note the release version) |
| `cisa2023memorysafe` | US CISA roadmap |
| `eu2024cra` | EU Cyber Resilience Act (EUR-Lex) |

**Verify at:** The issuing organisation's site. **Version and date matter** - specs and regulations get amended.

---

## 5. Blogs / talks - grey literature

**What:** Industry blog posts, keynotes, slide decks. Not peer-reviewed.

**When:** The claim **is** a vendor's own statistic or policy announcement (e.g. "~70% of our CVEs are memory-safety issues").

**Examples:** `google2022android`, `msrc2019memory`, `vanderstoep2025android`

**Risk:** Editable, no methodology, no review. Fine for **motivation** and adoption context; weak for performance or experimental claims.

**BibTeX:** `@misc` with `howpublished`, `url`, and access date.

---

## 6. Standards drafts - WG21 (C++ committee)

**What:** Working papers for ISO C++ (`PxxxxRx`). Proposals in progress, **not** shipped ISO text.

**When:** Arguing that a language is **evolving** (e.g. C++ safety profiles) - not that a feature is already in a released standard.

| Published ISO standard | WG21 draft (`P3081R2`) |
|----------------------|-------------------------|
| Fixed text | Evolving; revision suffix matters |
| `@techreport` | `@misc` with `howpublished = {… WG21 document P…}` |

**Example** (`sutter2025profiles`):

```bibtex
@misc{sutter2025profiles,
  author       = {Sutter, Herb},
  title        = {Core Safety Profiles for {C++26}},
  howpublished = {ISO/IEC JTC1/SC22/WG21 document P3081R2},
  year         = {2025}, month = feb,
  url          = {https://isocpp.org/files/papers/P3081R2.pdf}
}
```

**Verify at:** `open-std.org` or `isocpp.org` - use the **paper number and revision** (R0, R1, R2).

---

## Where to verify (decision table)

| If the work is… | Look up metadata on… |
|-----------------|----------------------|
| ACM / IEEE / Elsevier paper | DOI / Crossref → publisher page |
| Only on arXiv | arXiv abstract (switch when published) |
| USENIX / LIPIcs / no DOI | Publisher site + DBLP |
| 3GPP spec, law, agency report | Official site (version number!) |
| Vendor claim or keynote | Original blog or talk URL |
| C++ committee proposal | open-std.org / isocpp.org (P-number + revision) |

---

## Verification labels (`LITERATURE_NOTES.md`)

When adding entries from a literature sweep, mark each source:

- **VERIFIED** - metadata read from a primary source; safe to cite.
- **PARTIAL** - source exists; at least one field still needs confirming (name the field).
- **NOT CITABLE** - found during search; listed so it is not re-found; do not cite.

Nothing in this repo's bibliography should be filled in from memory alone.

---

## Style notes for this thesis

- Bibliography style: **`IEEEtran`** (numbered, citation order).
- Cite keys: `authorYYYYkeyword` (e.g. `polese2023oran`, `skoudlil2025asyncrust`).
- Web-only `@misc` entries: include `url` and an access date in `note` or `urldate`.
- After editing `bibliography.bib`: `pdflatex` → `bibtex` → `pdflatex` × 2.
