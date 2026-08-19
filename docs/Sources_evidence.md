# Sources evidence — citation audit of `bibliography.bib`

Audit date: **15 August 2026**. Scope: all **80** entries in `bibliography.bib`, every one of them as
actually used in `Ha_Vien_Mastersthesis_2026.tex`, `Thesis_v1.tex`, and `Thesis_Plan_v2.tex`.

For every entry this file records three things:

1. **Metadata** — whether the bibliographic fields match the publisher's own record.
2. **Where it is cited** — file and line, with the claim the citation is carrying.
3. **Evidence** — the page, clause, or section of the source where that claim is stated, with the
   source's own words where the thesis leans on specific wording or numbers.

## Method

- Every DOI was resolved against **Crossref** (or **DataCite** for LIPIcs) and compared field by
  field: title, author list, year, volume, issue, page range, container title.
- Entries without a DOI were checked against the issuing body: the **3GPP specification archive**
  and the corresponding **ETSI** deliverable, **open-std.org** / **isocpp.org** for WG21 papers,
  the **USENIX** proceedings pages, **DBLP** for page ranges USENIX does not print, **DiVA** for
  the master's theses, **OpenLibrary** for the book, **PyPI/GitHub** for the software.
- Claim-level evidence was read out of the source document wherever the document could be
  retrieved: 3GPP/ETSI PDFs, arXiv and author copies, USENIX and LIPIcs PDFs, the WG21 PDFs,
  EUR-Lex, and the DiVA theses. Page numbers below are **PDF page numbers of the file named**,
  which is what you can check fastest; clause and section numbers are given as well.

> **Not yet audited here (17 August 2026).** The fourteen entries added after the third literature
> sweep — the four additional DiVA theses, `suchert2023stamp`, `gonzalez2023rustudp`,
> `pirelli2023safelowlevel`, `sundvisson2026drivers`, `okawa2024ruststudy`, `hughes2025gcrust`,
> `andersson2026stdmemsafety`, `li2026rustlinux`, `hong2025ctorust`, `zhuang2026flowprioritize`,
> `gjomemo2016mesc` —
> have Crossref- or DiVA-verified metadata (`LITERATURE_NOTES.md`, third sweep) but no
> entry-by-entry evidence section below yet. For the four theses the claims come from the
> repository abstract, evidence level **B**, not from the full text.

**Evidence level** used in each entry:

| Level | Meaning |
| --- | --- |
| **A** | The source was opened and the supporting passage located. Page/clause given. |
| **B** | Publisher-deposited record (Crossref abstract, official landing page) carries the claim; full text not opened. |
| **C** | Bibliographic metadata confirmed, but the passage sits behind a paywall and was not opened here. Spot-check with university access if the claim is load-bearing. |

Reproduce with the scripts in `.bibaudit/`: `cite_audit.py` (maps every key to the claims that
cite it), `bib_verify.py` (Crossref/DataCite field-by-field diff), `abstracts.py`, `oa_fetch.py`,
`oa_fetch2.py`, `fetch_sources.py`, `evidence.py`, `evidence2.py`, `meta_checks.py`,
`pdfgrep.py`.

## Overall result

- **80 entries, 80 cited** at the time of this audit. No orphan entries, no citation without an
  entry. The biber log reports 80 citekeys and logs no warnings or errors. *After the third
  literature sweep of 17 August 2026 the bibliography holds 98 active entries, all 98 cited, still
  with no orphans and no missing keys; the eighteen added since are listed in the note above and
  are not covered by the entry-by-entry evidence below.*
- **71 entries are clean as they stand.**
- **3 entries have a factual metadata error**: one missing author, one extra author, one wrong
  month.
- **5 more have a cosmetic or completeness nit** (author-field rendering, a one-month date slip, a
  missing series, a missing access date, one URL pointed at the wrong page).
- **4 places need a wording or citation-placement fix in the thesis prose**, one of which is
  serious: a passage inside quotation marks that does not appear in the cited source.

### Fix list, in priority order

**All were applied on 15 August 2026**, and the thesis PDF (143 pp.), `Thesis_v1.pdf`
(27 pp.) and `Thesis_Plan_v2.pdf` (5 pp.) were rebuilt: zero LaTeX errors, zero undefined
references or citations, no biber warnings. The entries below describe the state *before* the fix,
so that the reasoning stays auditable.

| # | Where | Problem | Fix |
| --- | --- | --- | --- |
| 1 | `Ha_Vien_Mastersthesis_2026.tex:3694–3697` (`karlback2021ran`) | Text inside quotation marks — "an effort … to utilize the different strengths of each language, and stay away from using exactly the same implementation" — **does not appear in the thesis it is attributed to**. The source says the same thing in different words, and the fragment "an effort was made" comes from a sentence about a different subject (their own inexperience). | Requote from §6.2.5, p. 74, or drop the quotation marks and paraphrase. Suggested wording in the entry below. |
| 2 | `bibliography.bib:381` (`agache2020firecracker`) | Author **Andreea Florescu** is missing. The USENIX proceedings page and the paper's own title page list eight authors; the entry has seven. | Insert `Florescu, Andreea` after `Brooker, Marc`. |
| 3 | `bibliography.bib:956` (`watson2025memorysafety`) | 22 authors listed; the CACM article has **21**. `Kern, Christoph` is an author of the extended Cambridge technical report (UCAM-CL-TR-996), not of the CACM paper. CACM also gives "Murali Vijayaraghavan", not "Muralidaran", and orders Chisnall before Chen, Richardson before Rebert. | Drop `Kern, Christoph`, use `Vijayaraghavan, Murali`, match CACM order. (Or cite the TR instead — but then the volume/issue/pages must go.) |
| 4 | `bibliography.bib:354` (`3gpp38913`) | Month given as March 2024. TR 38.913 v18.0.0 was posted **4 April 2024**; ETSI's mirror is dated 2024-05. | `month = apr`. |
| 5 | `Ha_Vien_Mastersthesis_2026.tex:805` (`xu2021rustcve`) | "every one of them involved `unsafe` code" is one degree stronger than the source, which says all bugs require unsafe **"except one compiler bug"**. | Add the exception, or write "all but one". |
| 6 | `Ha_Vien_Mastersthesis_2026.tex:350` (`eu2024cra`) | "reporting obligations applying from September 2026 and the remainder from December 2027" leaves out Chapter IV (notification of conformity assessment bodies), which applies from **11 June 2026**. | "…and most of the remainder from December 2027", or name the June 2026 date. |
| 7 | `Ha_Vien_Mastersthesis_2026.tex:3438` (`karlback2021ran`) | "a pattern they flag as unexplained". They call it *surprising* and do offer a theory — green-thread stack sizes — which is the same mechanism the thesis then argues for. | "which they call surprising and attribute tentatively to green-thread stack size" — this makes the thesis's own explanation stronger, not weaker. |
| 8 | `tene_hdrhistogram` at `Ha_Vien_Mastersthesis_2026.tex:2402, 3922`; `Thesis_v1.tex:175`; `Thesis_Plan_v2.tex:141` | Cited for coordinated omission, but the cited page (`hdrhistogram.github.io`) documents the histogram, not coordinated omission. | The concept is already carried by `schroeder2006openclosed` in each of those citations, so either rely on that alone, or point the URL at the HdrHistogram documentation for `recordValueWithExpectedInterval`. |
| 9 | `bibliography.bib:129` (`cisa2023memorysafe`) | The `author` field is one braced string containing "and others"; it will print as a run-on corporate name, duplicating the `institution` field which already names all eight agencies correctly. | `author = {{Cybersecurity and Infrastructure Security Agency}}` and let `institution` carry the rest. |
| 10 | `bibliography.bib:588` (`xiao2024rpkt`), `:318` (`3gpp38331`) | Small completeness items: `rpkt` is in the LNCS series (NPC 2024 conference, proceedings published 2025); TS 38.331 v17.5.0 was posted 1 July 2023, not June. | Optional. |

### What was changed

`bibliography.bib` — `agache2020firecracker` (+ Andreea Florescu); `watson2025memorysafety`
(21 authors, CACM order, Murali); `3gpp38913` (`month = apr`); `3gpp38331` (`month = jul`);
`cisa2023memorysafe` (corporate author simplified, `institution` unchanged);
`xiao2024rpkt` (`series`, booktitle now names NPC 2024);
`alsoran` (access date and project status); `tene_hdrhistogram` (URL now points at the repository,
whose "Corrected vs. raw value recording calls" section documents
`recordValueWithExpectedInterval`, and the `note` names that section).

`Ha_Vien_Mastersthesis_2026.tex` — the Karlbäck and Orö quotation (l. 3694), the "unexplained" characterisation
(l. 3437), the `unsafe`-CVE exception (l. 804), and the Cyber Resilience Act dates (l. 349).

One related sentence was **left alone** deliberately: `Thesis_Plan_v2.tex:118` says memory-safety
defects in real Rust code "invariably trace back to `unsafe`". The single exception in Xu et al. is
a compiler bug rather than a program defect, so the plan's summary sentence still holds; it is
noted here only so the difference in wording between the two documents is on the record.

### Two things that look wrong but are right

Recorded so nobody "corrects" them later:

- `emmerich2019drivers` — IEEE's record drops "García" from **Esaú García Sánchez-Torija**. The
  entry follows the paper's own title page, which is correct.
- `szekeres2013sok` — IEEE's record parses **Tao Wei** as a surname. The entry is correct.

---

# Entry-by-entry evidence

Verdicts below describe each entry **as it was found at the start of the audit**. Where a verdict
says FIX, that fix has since been applied and rebuilt — see "What was changed" above.

## Standards and specifications

### `3gpp38401` — TS 38.401, NG-RAN Architecture description, V17.5.0
**Metadata** ✔ `38401-h50.zip` in the 3GPP archive is dated **2023-06-29**, matching `jun 2023`.
The ETSI mirror is *ETSI TS 138 401 V17.5.0 (2023-07)*. URL in the entry resolves.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:254, 372, 594, 609, 1047, 2423`; `Thesis_v1.tex:169`;
`Thesis_Plan_v2.tex:59` — the CU/DU split, the CU-CP/CU-UP separation, the F1/E1/NG interfaces,
and the gNB-CU-CP as the node hosting RRC.
**Evidence — level A** (`ts_138401v170500p.pdf`):
- p. 11, clause 3.1: "gNB-CU-Control Plane (gNB-CU-CP): a logical node hosting the RRC and the
  control plane part of the PDCP protocol of the gNB-CU … terminates the E1 interface connected
  with the gNB-CU-UP and the F1-C interface connected with the gNB-DU."
- p. 16, clause 6.1.2 "Overall architecture for separation of gNB-CU-CP and gNB-CU-UP", Figure
  6.1.2-1.
- Clause 10.4 "E1 interface".
**Verdict** OK. This entry, not `3gpp38300`, is what carries the CP/UP separation claim.

### `3gpp38300` — TS 38.300, NR and NG-RAN Overall description, V17.5.0
**Metadata** ✔ `38300-h50.zip` dated **2023-06-30**; ETSI mirror *V17.5.0 (2023-07)*.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:254, 372, 594, 609, 1047` — alongside 38.401 for architecture and
functional split.
**Evidence — level A** (`ts_138300v170500p.pdf`): p. 21, clause 4.1 "Overall Architecture" (an
NG-RAN node is a gNB or an ng-eNB; Figure 4.1-1); p. 22, clause 4.2 "Functional Split", listing
gNB functions including Radio Resource Management and "Connection setup and release".
**Note** 38.300 v17.5.0 does **not** describe the gNB-CU-CP / gNB-CU-UP separation; where it
mentions CU functionality it defers to TS 38.401 (e.g. p. 19, p. 28). The pairing in the thesis is
fine because 38.401 leads, but 38.300 should not be cited alone for the CP/UP split.
**Verdict** OK with that note.

### `3gpp38331` — TS 38.331, NR RRC Protocol specification, V17.5.0
**Metadata** ⚠ `38331-h50.zip` is dated **2023-07-01**; the entry says June 2023. ETSI mirror is
*V17.5.0 (2023-07)*. One-month slip, cosmetic.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:258, 372, 594, 1044, 2423` — RRC signalling procedures and the UE
lifecycle from establishment to release.
**Evidence — level C** The RRC connection control procedures are clause 5.3 (establishment,
reconfiguration, re-establishment, release). The document itself was not opened for this audit;
it is ~1,000 pages and the claim is structural rather than numeric.
**Verdict** Metadata: change month to `jul` if you want it exact.

### `3gpp38463` — TS 38.463, E1 Application Protocol (E1AP), V17.0.0
**Metadata** ✔ `38463-h00.zip` dated **2022-04-06**, matching `apr 2022`; ETSI mirror
*ETSI TS 138 463 V17.0.0 (2022-05)*.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:372, 609, 1047` — the E1 interface between CU-CP and CU-UP.
**Evidence — level A** Title page of `ts_138463v170000p.pdf`: "NG-RAN; E1 Application Protocol
(E1AP) (3GPP TS 38.463 version 17.0.0 Release 17)".
**Verdict** OK.

### `3gpp22261` — TS 22.261, Service requirements for the 5G system, V18.6.0
**Metadata** ✔ `22261-i60.zip` (i = Release 18, 6.0) is dated **2022-04-01** in the 3GPP archive,
consistent with `mar 2022` (SA plenary approval, posted 1 April).
**Cited** `Ha_Vien_Mastersthesis_2026.tex:597, 1091`; `Thesis_v1.tex:202` — the 5G system's latency and
reliability KPIs.
**Evidence — level C** ETSI no longer mirrors v18.6.0 (only 18.13.0 and later), so the KPI clause
was not opened. The performance requirements live in clause 7. If you want a page-level anchor
here, the cleanest option is to lean on `3gpp38913` clause 7.4, which *is* verified below.
**Verdict** Metadata OK; claim evidence unverified.

### `3gpp38913` — TR 38.913, Study on scenarios and requirements for next generation access technologies, V18.0.0
**Metadata** ⚠ month. `38913-i00.zip` is dated **2024-04-04**; ETSI mirror is *ETSI TR 138 913
V18.0.0 (2024-05)*. The entry says March 2024. → `month = apr`.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:261, 374, 597, 1091`; `Thesis_v1.tex:128, 202` — the millisecond-scale
control-plane budget, and specifically the 10 ms target.
**Evidence — level A** (`tr_138913v180000p.pdf`, **p. 24**, clause 7.4 "Control plane latency"):
"Control plane latency refers to the time to move from a battery efficient state (e.g., IDLE) to
start of continuous data transfer (e.g., ACTIVE). **The target for control plane latency should be
10ms.**" This is exactly the claim at `Thesis_v1.tex:128` and the wording already in the entry's
`note` field.
**Verdict** Claim verified; fix the month.

### `rfc3393` — IP Packet Delay Variation Metric (IPPM)
**Metadata** ✔ Crossref: Demichelis and Chimento, IETF, November 2002, DOI 10.17487/RFC3393.
(Crossref does not carry the RFC number in a comparable field; the entry's `number = 3393` is
correct.)
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1591` — jitter defined as the absolute difference between consecutive
latencies, "the packet-delay-variation quantity of RFC 3393".
**Evidence — level A** (`rfc3393.txt`, abstract and §1): "The metric is based on the difference in
the One-Way-Delay of selected packets. This difference in delay is called 'IP Packet Delay
Variation (ipdv)'."
**Verdict** OK. The thesis's usage — variation from one operation to the next, not spread of the
distribution — is the RFC's sense.

---

## Memory safety: industry and government evidence

### `msrc2019memory` — Miller, BlueHat IL 2019
**Metadata** ✔ Matt Miller, MSRC, February 2019. The repository path in the URL contains the deck:
`2019_02 - BlueHatIL - Trends, challenge, and shifts in software vulnerability mitigation.pdf`.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:275, 340, 751, 3564, 3648`; `Thesis_Plan_v2.tex:63` — most sharply at
751: "memory-safety issues account for roughly 70 % of the security vulnerabilities reported at
Microsoft".
**Evidence — level A** (deck **p. 11**): "**~70% of the vulnerabilities addressed through a
security update each year continue to be memory safety issues**", above the chart "% of memory
safety vs. non-memory safety CVEs by patch year", 2006–2018.
**Verdict** OK. The source says "addressed through a security update" rather than "reported"; the
entry's `note` ("Approximately 70 % of Microsoft CVEs are memory-safety issues") matches the
chart title.

### `google2022android` — Vander Stoep, Memory Safe Languages in Android 13
**Metadata** ✔ Page title and URL confirm: *Memory Safe Languages in Android 13*, Google Online
Security Blog, December 2022, Jeff Vander Stoep.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:275, 340, 754, 3564, 3648`.
**Evidence — level A** for identity and date; the specific "below a fifth by 2025" figure at
`Ha_Vien_Mastersthesis_2026.tex:754` is carried by `vanderstoep2025android` (below), which is cited alongside it.
**Verdict** OK.

### `vanderstoep2025android` — Rust in Android: Move Fast and Fix Things
**Metadata** ✔ blog.google, author metadata "Jeff Vander Stoep", November 2025.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:340, 754` — memory-safety vulnerabilities falling below a fifth of
Android's total by 2025.
**Evidence — level A** (page metadata/description): "The 2025 data continues to validate the
approach, with **memory safety vulnerabilities falling below 20% of total vulnerabilities for the
first time**."
**Verdict** OK — the thesis's "below a fifth … by 2025" is the source's own claim.

### `google2024securebydesign` — Rebert and Kern, Secure by Design
**Metadata** ✔ research.google landing page: *Secure by Design: Google's Perspective on Memory
Safety*, **Google Security Engineering (2024)**, authors Alex Rebert and Christoph Kern.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:340, 3648`.
**Evidence — level B** Title and venue support the claim as used (vendor position on memory
safety). No page-level quote taken.
**Verdict** OK.

### `oncd2024building` — ONCD, Back to the Building Blocks
**Metadata** ✔ Cover page: "BACK TO THE BUILDING BLOCKS: A PATH TOWARD SECURE AND MEASURABLE
SOFTWARE, **FEBRUARY 2024**".
**Cited** `Ha_Vien_Mastersthesis_2026.tex:346, 525, 3648` — the policy push away from memory-unsafe languages.
**Evidence — level A** (**p. 7**): "Experts have identified a few programming languages that both
lack traits associated with memory safety and also have high proliferation across critical
systems, such as C and C++"; and "in most cases, **using a memory safe programming language is the
most efficient way to substantially improve software security**".
**Verdict** OK.

### `cisa2023memorysafe` — The Case for Memory Safe Roadmaps
**Metadata** ✔ for content, ⚠ for the `author` field. Cover page (**p. 1**) gives
"Publication: December 2023" and the eight authoring agencies in exactly the order the entry's
`institution` field lists them: US CISA, US NSA, US FBI, Australian Signals Directorate's ACSC,
Canadian Centre for Cyber Security, UK NCSC, New Zealand NCSC, CERT NZ. The `author` field,
however, is a single braced string ending "and others" and will print as a run-on name.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:346, 525, 3648`; `Thesis_v1.tex:137`; `Thesis_Plan_v2.tex:63` — the
"publish memory-safe roadmaps" claim.
**Evidence — level A** (**p. 2**): "the agencies urge software manufacturers to **create and
publish memory safe roadmaps** that detail how they will eliminate memory safety vulnerabilities
in their products."
**Verdict** Claim verified; tidy the `author` field (fix #9).

### `eu2024cra` — Regulation (EU) 2024/2847, Cyber Resilience Act
**Metadata** ✔ OJ L, 2024/2847, published 20 November 2024; ELI URL resolves.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:350` — "with reporting obligations applying from September 2026 and the
remainder from December 2027".
**Evidence — level A** (**Article 71(2)**, EUR-Lex consolidated text): "This Regulation shall
apply from **11 December 2027**. However, **Article 14 shall apply from 11 September 2026** and
**Chapter IV (Articles 35 to 51) shall apply from 11 June 2026**." Recital (126) says the same in
prose.
**Verdict** Dates are right, but "the remainder from December 2027" omits the June 2026 tranche
(fix #6).

### `watson2025memorysafety` — Watson et al., CACM 68(2):40–45
**Metadata** ✖ author list. Crossref and OpenAlex both give **21** authors; the CACM abstract
itself opens "**Twenty-one authors**, spanning academia and industry…". The entry lists 22: the
extra name is **Christoph Kern**, who appears on the cover of the *extended* version (Cambridge
Computer Laboratory Technical Report UCAM-CL-TR-996) but not on the CACM article. CACM also gives
"Murali Vijayaraghavan" (entry: "Muralidaran"), and orders Chisnall before Chen and Richardson
before Rebert. Volume, issue, pages, year and DOI are all correct.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:343` — memory safety needs standardised terminology and requirements.
**Evidence — level A** (UCAM-CL-TR-996, p. 1 and p. 3, the extended version of the same paper):
"It is time to standardize principles and practices for software memory safety … we explore
memory-safety standardization, which we argue is an essential step…". Crossref's deposited CACM
abstract: "…argue that standardization is an essential next step to achieving universal strong
memory safety."
**Verdict** Claim verified; **fix the author list** (fix #3).

### `szekeres2013sok` — SoK: Eternal War in Memory
**Metadata** ✔ IEEE S&P 2013, pp. 48–62. IEEE's record parses "Tao Wei" as a surname; the entry is
correct.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:749, 1124, 3649`; `Thesis_v1.tex:134, 178` — memory corruption as a
decades-old problem whose deployed mitigations are partial.
**Evidence — level A** (p. 1, abstract): "This problem has existed for **more than 30 years** and
a vast number of potential solutions have been proposed, yet memory corruption attacks continue to
pose a serious threat. Real world exploits show that **all currently deployed protections can be
defeated**."
**Verdict** OK — this is a precise match for "deployed mitigations remain only partial defences".

---

## Rust: foundations and empirical evidence

### `jung2018rustbelt` — RustBelt, PACMPL 2(POPL), Article 66
**Metadata** ✔ The paper's own footer reads "Proceedings of the ACM on Programming Languages, Vol.
2, No. POPL, **Article 66. Publication date: January 2018**", so `year = 2018` and
`pages = 66:1--66:34` are both right. (Crossref's "2017" is the online-first date — do not
"correct" the entry to it.)
**Cited** `Ha_Vien_Mastersthesis_2026.tex:278, 800, 3641`; `Thesis_Plan_v2.tex:65` — machine-checked foundations
for safe Rust.
**Evidence — level A** (p. 1, abstract; restated p. 2): "we give the **first formal (and
machine-checked) safety proof** for a language representing a realistic subset of Rust."
**Verdict** OK.

### `jung2020stacked` — Stacked Borrows, PACMPL 4(POPL), Article 41
**Metadata** ✔ Footer: "Proc. ACM Program. Lang., Vol. 4, No. POPL, **Article 41. Publication
date: January 2020**". `pages = 41:1--41:32` correct.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:802, 3642` — the aliasing discipline `unsafe` code must respect, given a
precise operational semantics.
**Evidence — level A** (p. 1, abstract): "we propose **Stacked Borrows, an operational semantics
for memory accesses in Rust**. Stacked Borrows defines an aliasing discipline and declares
programs violating it to have undefined behavior."
**Verdict** OK.

### `jung2021safe` — Safe Systems Programming in Rust, CACM 64(4):144–152
**Metadata** ✔ Crossref matches on every field.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:796, 3641`; `Thesis_v1.tex:182, 207` — ownership and borrowing statically
forbid mutation of shared state; exceptions confined to `unsafe` behind safe APIs.
**Evidence — level A** (author copy, p. 1): "It tackles this challenge using a strong type system
based on the ideas of **ownership and borrowing, which statically prohibits the mutation of shared
state**"; and the following bullet on data types that "fundamentally depend on shared mutable
state" being encapsulated.
**Verdict** OK.

### `astrauskas2020unsafe` — How Do Programmers Use Unsafe Rust?, PACMPL 4(OOPSLA), Article 136
**Metadata** ✔ Crossref matches; `pages = 136:1--136:27` is the ACM article-number convention.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:804, 3644` — `unsafe` is used sparingly and in localised ways.
**Evidence — level B** Crossref-deposited abstract: "an important assumption of the Rust language,
which we dub the **Rust hypothesis**, is that programmers use Rust by following three main
principles: **use unsafe code sparingly, make it easy to review, and hide it behind a safe
abstraction**… This paper studies empirically how unsafe code is used in practice."
**Verdict** OK.

### `xu2021rustcve` — Memory-Safety Challenge Considered Solved?, TOSEM 31(1), Article 3
**Metadata** ✔ TOSEM 31(1), article 3, issue dated January 2022 → `year = 2022` is right
(Crossref's 2021 is online-first). Pages `3:1--3:25` correct.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:805, 3360, 3644`; `Thesis_Plan_v2.tex:118`.
**Evidence — level A** (arXiv 2003.03296, the authors' copy of the same study): p. 1, abstract —
"Our analysis result shows that Rust can keep its promise that **all memory-safety bugs require
unsafe code**"; and p. 2 — "**all bugs in our dataset require unsafe code except one compiler
bug**."
**Verdict** Entry OK. The thesis sentence at 805 ("every one of them involved `unsafe` code")
should carry the exception (fix #5).

### `qin2020rust` — Understanding Memory and Thread Safety Practices and Issues in Real-World Rust Programs, PLDI 2020, 763–779
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:423, 804, 3644, 3744, 3789`.
**Evidence — level A** (author copy, p. 1, abstract): "We performed the **first empirical study of
Rust by close, manual inspection of 850 unsafe code usages and 170 bugs** in five open-source Rust
projects, five widely-used Rust libraries, two online security databases, and the Rust standard
library."
**Verdict** OK — supports both the "used sparingly" claim and the "blocking bugs still occur"
claim at 3744.

### `evans2020rust` — Is Rust Used Safely by Software Developers?, ICSE 2020, 246–257
**Metadata** ✔ Pages and year match. Crossref's booktitle is "Proceedings of the ACM/IEEE 42nd
International Conference on Software Engineering"; the entry's shorter form is fine.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:810, 3361, 3552, 3647, 3746, 3790` — a small fraction of crates use
`unsafe` directly, but a much larger fraction cannot be fully statically checked.
**Evidence — level A** (arXiv 2007.00752, p. 1, abstract): "software engineers use the keyword
**unsafe in less than 30% of Rust libraries, but more than half cannot be entirely statically
checked** by the Rust compiler because of Unsafe Rust **hidden somewhere in a library's call
chain**."
**Verdict** OK — this is close to a word-for-word match with the thesis sentence at 810.

### `bae2021rudra` — Rudra, SOSP 2021, 84–99
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3645` — ecosystem-scale auditing finds defects nonetheless.
**Evidence — level C** No open copy retrieved; claim is title-level ("Finding Memory Safety Bugs
in Rust at the Ecosystem Scale") and is used only in a list.
**Verdict** OK.

### `zheng2024security` — A Closer Look at the Security Risks in the Rust Ecosystem, TOSEM 33(2), Article 34
**Metadata** ✔ TOSEM 33(2), issue dated February 2024 → `year = 2024` right (Crossref online-first
2023). Pages `34:1--34:30` correct.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3645`.
**Evidence — level A** (arXiv 2308.15046, p. 1): "we first compile a dataset of **433
vulnerabilities, 300 vulnerable code repositories, and 218 vulnerability fix commits** in the Rust
ecosystem, spanning over 7 years."
**Verdict** OK.

### `qin2024safety` — Understanding and Detecting Real-World Safety Issues in Rust, TSE 50(6):1306–1324
**Metadata** ✔ Crossref matches on all fields.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3645, 3744`.
**Evidence — level C** Paywalled; no open copy found. The companion PLDI'20 study
(`qin2020rust`, verified above) carries the same claim in the same sentence at 3744.
**Verdict** OK.

### `zhang2026deadlock` — Two Birds One Stone, Automated Software Engineering 33(2), article 65
**Metadata** ✔ Crossref resolves the DOI and matches authors, journal, volume, issue and year.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3371`; `Thesis_Plan_v2.tex:119` — static deadlock detection for Rust is
an active research problem.
**Evidence — level A** (the preprint the entry's `note` points to, arXiv 2401.01114, p. 1):
"Although Rust claims to enable fearless concurrency, **concurrency errors remain prevalent in
practical applications, with deadlocks particularly prominent and harmful**. Current static
deadlock detection techniques either do not cater to Rust programs … or solely concentrate on
resource deadlocks, disregarding communication deadlocks."
**Verdict** OK. Good that the journal version is cited rather than the preprint.

### `tang2025converos` — Converos, USENIX ATC 2025, 1143–1159
**Metadata** ✔ DBLP confirms pages **1143–1159** and the six-author list.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3373` — model checkers for Rust kernel code are motivated by ownership
and borrowing leaving data races, deadlocks and livelocks reachable.
**Evidence — level A** (`atc25-tang.pdf`, p. 2): "**Although Rust greatly enhances memory safety
and prevents data races in safe code, OS kernel development inevitably requires unsafe, which may
still introduce concurrency-related undefined behaviors such as data races. Logical errors and
flawed designs can lead to deadlocks, livelocks, and functional violations.**" And, in the
abstract: "uncovering 20 bugs that led to issues such as data races, deadlocks, livelocks, and
kernel panics."
**Verdict** OK — an unusually exact match to the sentence it supports.

### `klabnik2023rust` — The Rust Programming Language, 2nd edition
**Metadata** ✔ OpenLibrary record for ISBN 9781718503106: *Rust Programming Language, 2nd
Edition*, Steve Klabnik and Carol Nichols, No Starch Press, 2023.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:278, 791`; `Thesis_v1.tex:135, 182` — ownership and borrowing; safety at
compile time.
**Evidence — level C** Book not opened. The relevant chapters are 4 (ownership) and 16 (fearless
concurrency); add a chapter to the citation if you want it tighter.
**Verdict** OK.

### `bugden2022rust` — Rust: The Programming Language for Safety and Performance
**Metadata** ✔ arXiv 2206.05503, DOI 10.48550/arXiv.2206.05503 (DataCite), 2022.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:901, 3629, 3782` — cross-language benchmark surveys place Rust alongside
C and C++.
**Evidence — level A** (arXiv PDF, p. 1, abstract): "we **surveyed and analyzed recent research on
Rust and research that benchmarks Rust with other available prominent programming languages** …
recent experimental results in benchmarking research show Rust's overall superiority…"
**Verdict** OK, but note this is still the only load-bearing arXiv-only citation — `ASSESSMENT.md`
already flags replacing it as the last optional lift on criterion 2. Its use at 3782 is honest
(the table marks it "General benchmarks / no / no / no").

---

## Performance, tail latency, and measurement method

### `dean2013tail` — The Tail at Scale, CACM 56(2):74–80
**Metadata** ✔ Crossref matches every field.
**Cited** twelve times, incl. `Ha_Vien_Mastersthesis_2026.tex:266, 292, 410, 670, 894, 1215, 3666, 3882`;
`Thesis_v1.tex:147, 172, 213`; `Thesis_Plan_v2.tex:73` — fan-out makes a rare per-operation
latency a common per-request latency.
**Evidence — level B** Crossref-deposited abstract: "Software techniques that tolerate latency
variability are vital to building responsive large-scale Web services." The fan-out argument is
the paper's central section ("The Tail at Scale", §"Why Variability Exists" and §"Reducing
Component Variability").
**Verdict** OK.

### `barroso2017microseconds` — Attack of the Killer Microseconds, CACM 60(4):48–54
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:266, 292, 673, 3666` — at microsecond scale, conventional OS and
software overheads stop being negligible.
**Evidence — level B** Crossref-deposited abstract: "**Microsecond-scale I/O means tension between
performance and productivity** that will need new latency-mitigating ideas, including in hardware."
**Verdict** OK.

### `li2014tales` — Tales of the Tail, SoCC 2014, Article 9
**Metadata** ✔ Crossref matches; `pages = 9:1--9:14` is the article-number convention.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:676, 3666` — hardware, OS and application-level effects inflate the tail
beyond what queueing models predict.
**Evidence — level A** (author copy, p. 1, title and abstract): "Tales of the Tail: **Hardware,
OS, and Application-level Sources of Tail Latency**", University of Washington.
**Verdict** OK.

### `huang2017predictability` — A Top-Down Approach to Achieving Performance Predictability in Database Systems, SIGMOD 2017, 745–758
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3666` — part of the microsecond-scale predictability literature.
**Evidence — level C** Paywalled; used in a list, title-level support.
**Verdict** OK.

### `enberg2019threadpercore` — The Impact of Thread-per-Core Architecture on Application Tail Latency, ANCS 2019, 1–8
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:929, 3668`; `Thesis_v1.tex:251`; `Thesis_Plan_v2.tex:130` — the
justification for holding the concurrency model fixed across both implementations.
**Evidence — level A** (author copy, p. 1, abstract): "The **thread-per-core architecture has
emerged to reduce these overheads, but it also has its challenges** from thread synchronization
and OS interfaces. Applications can mitigate both issues with different techniques, but **their
impact on application tail latency is an open question**."
**Verdict** OK.

### `schroeder2006openclosed` — Open Versus Closed: A Cautionary Tale, NSDI 2006
**Metadata** ✔ DBLP confirms NSDI 2006 and assigns **no page numbers** — the entry correctly omits
them. USENIX page live.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:711, 2402, 3922`; `Thesis_v1.tex:175`; `Thesis_Plan_v2.tex:141` — open
and closed generators produce systematically different response times, the closed model reporting
lower figures.
**Evidence — level A** (`schroeder.pdf`, p. 1, abstract): "Workload generators may be classified
as based on a **closed system model, where new job arrivals are only triggered by job completions**
… or an **open system model, where new jobs arrive independently of job completions** … we
illustrate that there is a **vast difference in behavior between open and closed models** in
real-world settings."
**Verdict** OK. This is the right primary citation for the coordinated-omission argument.

### `tene_hdrhistogram` — HdrHistogram
**Metadata** ✔ Gil Tene is credited on the project page (Authors, Contributors and License
section). Accessed August 2026 as stated.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1810, 2402, 3922`; `Thesis_v1.tex:175, 255`; `Thesis_Plan_v2.tex:141`.
**Evidence — level A** (`hdrhistogram.github.io`): "A Histogram that supports **recording and
analyzing sampled data value counts across a configurable integer value range with configurable
value precision** within the range. Value precision is expressed as the number of significant
digits…" — this fully supports the use at `Ha_Vien_Mastersthesis_2026.tex:1810` (identical HDR configuration,
three significant figures).
**Issue** The page does **not** discuss coordinated omission, which is what the citation is being
asked to carry at 2402, 3922, `Thesis_v1.tex:175` and `Thesis_Plan_v2.tex:141`. In all four places
`schroeder2006openclosed` is cited alongside and does carry it (fix #8).
**Verdict** OK for the histogram; re-point or drop for coordinated omission.

### `georges2007rigorous` — Statistically Rigorous Java Performance Evaluation, OOPSLA 2007, 57–76
**Metadata** ✔ Crossref matches; booktitle wording differs cosmetically.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:464, 716, 1572, 3678, 3920`; `Thesis_v1.tex:235, 273`;
`Thesis_Plan_v2.tex:134` — reporting a single number invites conclusions run-to-run variation does
not support.
**Evidence — level A** (Ghent University copy, p. 1, abstract): "This paper shows that
**prevalent methodologies can be misleading, and can even lead to incorrect conclusions**. The
reason is that the data analysis is not statistically rigorous."
**Verdict** OK — near-verbatim support for the sentence at 1572.

### `efron1993bootstrap` — An Introduction to the Bootstrap
**Metadata** ✔ Crossref: Efron and Tibshirani, 1993, DOI 10.1007/978-1-4899-4541-9. ISBN matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1567, 3920`; `Thesis_v1.tex:274`; `Thesis_Plan_v2.tex:135` —
nonparametric bootstrap 95 % confidence intervals.
**Evidence — level B** Standard reference; the percentile and BCa interval construction the thesis
uses is Chapters 12–14. Book not opened for this audit.
**Verdict** OK.

### `holm1979simple` — A Simple Sequentially Rejective Multiple Test Procedure
**Metadata** ✔ OpenAlex: *Scandinavian Journal of Statistics*, volume 6, pages **65–70**, 1979,
Sture Holm. The JSTOR stable ID in the entry's URL (4615733) matches. **Do not add a DOI here.**
OpenAlex advertises `10.2307/4615733`, but that handle is unregistered: `doi.org` returns 404 and
the handle API reports "not found". It was added during this audit and then reverted. The entry
should stay DOI-less, with the JSTOR URL as the locator.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1613`; `Thesis_v1.tex:275`; `Thesis_Plan_v2.tex:136` — the Holm
step-down procedure controlling family-wise error without assuming independence.
**Evidence — level B** Metadata verified; the paper itself is behind JSTOR. The property the
thesis attributes to it (FWER control without independence assumptions) is the paper's own result.
**Verdict** OK.

### `natella2016fault` — Assessing Dependability with Software Fault Injection: A Survey, CSUR 48(3), Article 44
**Metadata** ✔ Crossref matches; `pages = 44:1--44:55` is the article-number convention.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1426, 3679`; `Thesis_v1.tex:261`; `Thesis_Plan_v2.tex:142`.
**Evidence — level B** Crossref-deposited abstract: "**Software Fault Injection is a method to
anticipate worst-case scenarios caused by faulty software through the deliberate injection of
software faults.** This survey provides a comprehensive overview of the state of the art…"
**Verdict** OK — matches the thesis's definition at 1426 closely.

### `zhou2025oltp` — OLTP Through the Looking Glass 16 Years Later, CIDR 2025
**Metadata** ✔ DBLP confirms CIDR 2025 and assigns no pages; the entry correctly omits them. PDF
retrieved from vldb.org.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:2752` — once per-operation work is optimised, cost is dominated by
communication across isolation boundaries.
**Evidence — level A** (p. 1, abstract): "we revisit these assumptions and demonstrate that
**communication overhead is now the dominant factor affecting OLTP performance** … revealing that
**messaging costs play a critical role in end-to-end performance** … **increased isolation can
lead to higher communication costs**."
**Verdict** OK — this is the strongest external corroboration in the bibliography for the thesis's
handoff-dominance result, and it is used exactly once, in the right place.

---

## Rust in systems and networking

### `balasubramanian2017rust` — System Programming in Rust: Beyond Safety, HotOS 2017, 156–161
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:423, 818, 3319, 3630, 3738, 3783` — the "zero-cost" framing.
**Evidence — level C** Paywalled; no open copy located. The thesis treats the claim critically at
3738 ("better read as workload-dependent than as universal"), which is the safe use.
**Verdict** OK.

### `levy2017kernel` — The Case for Writing a Kernel in Rust, APSys 2017, 1–7
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3630`.
**Evidence — level C** Paywalled; used in a list, title-level support.
**Verdict** OK.

### `mo2023rustshyper` — Rust-Shyper, Journal of Systems Architecture 142:102948
**Metadata** ✔ Crossref matches, including the article number as page.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3631, 3787`.
**Evidence — level C** Elsevier paywall; title-level support for "embedded hypervisor in Rust".
**Verdict** OK.

### `agache2020firecracker` — Firecracker, NSDI 2020, 419–434
**Metadata** ✖ **missing author**. The USENIX proceedings page and the paper's title page both
read: "Alexandru Agache, Marc Brooker, **Andreea Florescu**, Alexandra Iordache, Anthony Liguori,
Rolf Neugebauer, Phil Piwonka, and Diana-Maria Popa, Amazon Web Services." The entry has seven of
those eight. Pages 419–434 confirmed by DBLP. (DBLP also omits Florescu — the proceedings page is
the better authority.)
**Cited** `Ha_Vien_Mastersthesis_2026.tex:355, 3632` — production hypervisors such as AWS Firecracker, which
underpins its serverless platform, are already written in Rust.
**Evidence — level A** (`nsdi20-paper-agache.pdf`): p. 5 — "Firecracker contains **approximately
50k lines of Rust code** (96% fewer lines than QEMU)"; p. 13 — "The use of virtualization, along
with side-channel hardening, **implementation in Rust**, extensive testing and validation…" and
"We have been **running Lambda workloads in production on Firecracker since 2018**."
**Verdict** Claim verified; **add Andreea Florescu** (fix #2).

### `narayanan2020redleaf` — RedLeaf, OSDI 2020, 21–39
**Metadata** ✔ DBLP confirms pages **21–39** and the seven-author list as entered.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3684, 3759, 3786` — evaluated against C baselines constructed for the
purpose.
**Evidence — level A** (`osdi20-narayanan_vikram.pdf`): p. 2 — "we develop efficient versions of a
10Gbps Intel ixgbe network and NVMe solid-state disk device drivers that **match the performance of
the fastest DPDK and SPDK equivalents**"; p. 12, Figure 5 — "C vs Rust performance comparison",
and the ixgbe driver comparison against Linux and DPDK.
**Verdict** OK.

### `emmerich2019drivers` — The Case for Writing Network Drivers in High-Level Programming Languages, ANCS 2019, 1–13
**Metadata** ✔ Author list follows the paper (IEEE's record drops "García" from Esaú García
Sánchez-Torija — the entry is right).
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3319, 3633, 3737, 3759, 3784`; `Thesis_v1.tex:231`;
`Thesis_Plan_v2.tex:70` — most sharply at `Thesis_v1.tex:231`: "running 4 % slower than its C
reference while executing 63 % more instructions per packet".
**Evidence — level A** (arXiv 1909.06344, p. 1, abstract): "Out-of-order CPUs mitigate the cost of
safety checks: **Our Rust driver executes 63% more instructions per packet but is only 4% slower
than a reference C implementation.**" Table 9 (p. 11) gives the normalised results (Rust 98 % of
C).
**Verdict** OK — both numbers are the source's own, in the source's own order.

### `xiao2024rpkt` — rpkt, NPC, 454–465
**Metadata** ✔ Pages **454–465** confirmed by DBLP and Crossref. Note the split year: DBLP lists
the conference as **NPC 2024**, Springer published the LNCS proceedings in **2025**, which is what
the entry's `year` field says. Optional addition: `series = {Lecture Notes in Computer Science}`.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3633` — packet processing within a few percent of a C reference.
**Evidence — level C** Springer paywall; title-level support ("Generic, Safe, and Efficient
Userspace Packet Processing Library in Rust"). The "few percent" half of the sentence is carried
by `emmerich2019drivers`, which is verified above and cited alongside.
**Verdict** OK.

### `li2021ipc` — Understanding the Overheads of Hardware and Language-Based IPC Mechanisms, PLOS 2021, 53–61
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3683, 3759, 3785` — a comparison implementing one network function in
both C++ and Rust.
**Evidence — level C** ACM paywall. Used for the existence of a matched two-language design, not
for a number.
**Verdict** OK.

### `qazi2017pepc` — A High Performance Packet Core for Next Generation Cellular Networks, SIGCOMM 2017, 348–361
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3670, 3788` — Rust has mobile-network precedent in the datapath.
**Evidence — level C** ACM paywall; title-level.
**Verdict** OK.

### `polese2023oran` — Understanding O-RAN, IEEE COMST 25(2):1376–1411
**Metadata** ✔ Crossref matches every field. (The apostrophe in D'Oro differs typographically
only.)
**Cited** `Ha_Vien_Mastersthesis_2026.tex:256, 331, 611, 3669` — O-RAN turns the RAN into virtualised,
multi-vendor software connected by open interfaces.
**Evidence — level A** (arXiv 2202.01032, p. 1, abstract): "**O-RAN promotes virtualized RANs
where disaggregated components are connected via open interfaces** and optimized by intelligent
controllers … **O-RAN networks can be built with multi-vendor, interoperable components**."
**Verdict** OK — a close match to the thesis's phrasing.

### `liu2023l25gc` — L²5GC+, IEEE CloudNet 2023, 203–211
**Metadata** ✔ Crossref matches (its title uses `<sup>` markup; the entry's `L$^2$5GC+` is the
correct LaTeX equivalent).
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3675` — control-plane latency is an active target in the core network.
**Evidence — level C** IEEE paywall; title-level ("An Improved, 3GPP-Compliant 5G Core for
Low-Latency Control Plane Operations").
**Verdict** OK.

### `park2025ctrlbench` — CtrlBench, IEEE ICTC 2025, 1832–1837
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3675`.
**Evidence — level C** IEEE paywall; title-level ("Towards Accurate API-Level Benchmarking in 5G
Core Control Plane").
**Verdict** OK.

### `michaelides2026ranlatency` — Evaluation of Security-Induced Latency on 5G RAN Interfaces, WiSec 2026, 176–181
**Metadata** ✔ Crossref matches authors, venue, pages, year and DOI.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1227` — "IPsec adds roughly 120 µs on average to UE context setup,
against roughly 430 µs for DTLS".
**Evidence — level A** (arXiv 2602.12059, the authors' copy): p. 4 — "Over the F1-C, we monitor
the **UE Context Setup procedure** … To ensure statistical confidence, we **repeat the experiment
1,000 times**"; p. 5 — "On the CP, specifically the F1-C interface, **all IPsec configurations add
on average ∼120 µs to UE context setup, compared to ∼430 µs for DTLS**. The fastest IPsec
configuration (AES256-HMAC) adds only ∼40 µs … Over the E1 interface, IPsec configurations
introduce on average ∼80 µs."
**Verdict** OK — both numbers and the procedure are exactly as the thesis states.

### `alsoran` — Alsoran, a 5G gNB-CU written in Rust
**Metadata** ✔ Repository description: "5G gNodeB Centralized Unit written in Rust"; MIT licence;
last pushed June 2025. The owner's GitHub account (`nplrkn`) shows the given name "Nic" only; the
surname "Larkin" in the entry could not be confirmed from the repository itself — check the QCore
project page if you want it airtight. Consider adding an access date, as the entry has no `year`.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3674` — an open-source proof-of-concept gNB-CU with separated CU-CP and
CU-UP over E1, reporting no latency and with no C++ counterpart.
**Evidence — level A** (repository README): "Alsoran is a **Rust implementation of the gNodeB
Centralized Unit (gNB-CU)** of the 5G Radio Access Network"; "This project is currently a **proof
of concept** and not yet a fully functional gNB-CU"; under Current support: "**Separate CU-CP and
CU-UP communicating using E1**", "Scale-out of GNB-CU-CP workers using multiple TNLAs", "ASN.1
libraries for NGAP, E1AP, F1AP and RRC"; and the banner "This project is no longer active".
**Verdict** OK — the thesis's characterisation is accurate, including the absence of latency
numbers.

---

## The cost of Rust's safety model

### `pereira2017energy` — Energy Efficiency Across Programming Languages, SLE 2017, 256–267
**Metadata** ✔ Crossref matches all fields.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3629, 3781`; `Thesis_Plan_v2.tex:69` — compiled systems languages sit
close together on time and energy; general-purpose benchmarks report average-case behaviour.
**Evidence — level C** No abstract deposited and no open copy retrieved. The claim is the paper's
headline result and the thesis uses it as a general-benchmark reference (its related-work table
marks it "General benchmarks / no / no / no").
**Verdict** OK.

### `zhang2022runtime` — Towards Understanding the Runtime Performance of Rust, ASE 2022, Article 140
**Metadata** ✔ Crossref matches; `pages = 140:1--140:6` is the article-number convention.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3345, 3428, 3634, 3906`; `Thesis_Plan_v2.tex:72` — the literature
localises Rust's cost to bounds, overflow and division checks.
**Evidence — level C** ACM paywall. Note that the thesis is careful here: at 3428 it says these
mechanisms "are candidates to test, not conclusions to import", which is the right register for a
citation used without local instrumentation.
**Verdict** OK.

### `harris2023morello` — Rust for Morello, ECOOP 2023, LIPIcs 263, 39:1–39:27
**Metadata** ✔ The LIPIcs PDF's own running heads confirm **39:1–39:27** and volume 263.
DataCite gives the container as "LIPIcs, Volume 263, ECOOP 2023"; the entry's booktitle is the
conference name, which is conventional.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3345, 3428, 3636, 3906` — the bounds check specifically, set against
hardware-enforced capabilities.
**Evidence — level A** (`LIPIcs.ECOOP.2023.39.pdf`, p. 3, contributions list): "A performance
analysis of Rust on Morello (§4, §5): … **Analysis of the benefits of bounds checking elision on
capability hardware (§5.1)**." Abstract (p. 1): "a comparison of the performance of Rust's runtime
safety checks and the hardware-supported checks of Morello".
**Verdict** OK.

### `cui2025perfbugs` — Unleashing the Efficiency of Rust, ISSRE 2025, 371–381
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3637` — recurring performance anti-patterns.
**Evidence — level C** IEEE paywall; title-level ("An Empirical Study of Performance Bugs in Rust
Projects").
**Verdict** OK.

---

## The C++/Rust boundary and incremental adoption

### `rivera2021galeed` — Keeping Safe Rust Safe with Galeed, ACSAC 2021, 824–836
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:987, 3472, 3556, 3654, 3914, 4132`; `Thesis_Plan_v2.tex:145` — proposed
remedies isolate the two heaps in hardware rather than relying on interface discipline.
**Evidence — level C** ACM paywall; the claim is the paper's design premise (preserving Rust's
heap integrity against C/C++ in the same address space) and is carried jointly with
`kirth2022pkrusafe`.
**Verdict** OK.

### `kirth2022pkrusafe` — PKRU-Safe, EuroSys 2022, 132–148
**Metadata** ✔ Crossref matches (booktitle wording differs cosmetically).
**Cited** `Ha_Vien_Mastersthesis_2026.tex:987, 3472, 3556, 3654, 3914, 4132`.
**Evidence — level C** ACM paywall; title states the mechanism directly: "Automatically Locking
Down the Heap Between Safe and Unsafe Languages".
**Verdict** OK.

### `li2022crosslang` — Detecting Cross-Language Memory Management Issues in Rust, ESORICS 2022, 680–700
**Metadata** ✔ DBLP and Crossref both give pages **680–700**.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:989, 3473, 3655`; `Thesis_v1.tex:267` — defect classes arising
specifically at Rust/C boundaries have been catalogued in their own right.
**Evidence — level C** Springer paywall; title-level, and the thesis uses it only for the
existence of the category.
**Verdict** OK.

### `cai2026interop` — Fortifying the Seams Between C/C++ and Rust, TOSEM (2026)
**Metadata** ✔ Crossref matches authors, journal, year, DOI. Volume/issue not yet assigned, so the
entry correctly omits them.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:990, 3558, 3655` — binding generators carry their own defect history.
**Evidence — level B** Crossref-deposited abstract: "we **mined 320 bugs in the popular interop
tools, i.e., Bindgen, Cbindgen, and CXX**. We observe that the main obstacle is not tool crashes or
performance issues, but the **inability to generate correct and functional code** … Memory layout
mismatch is the most common cause with Bindgen."
**Verdict** OK — supports "review it as code rather than trusting it as tooling output" at 3558.

### `schuermann2023encapsulated` — Encapsulated Functions, KISV 2023, 41–48
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3656` — lighter crossing models proposed for embedded use.
**Evidence — level C** ACM paywall; title-level ("Fortifying Rust's FFI in Embedded Systems").
**Verdict** OK.

### `emre2023aliasing` — Aliasing Limits on Translating C to Safe Rust, PACMPL 7(OOPSLA1):551–579
**Metadata** ✔ Crossref matches every field.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3658` — aliasing patterns expressible in C but not in safe Rust bound
translation in principle.
**Evidence — level B** Crossref-deposited abstract: "existing translation methods are **severely
limited by a lack of precision in the Rust compiler's safety checker, causing many safe pointer
manipulations to be labeled as potentially unsafe** … increasing the number of pointers that can be
translated to safe Rust references by 75% over the baseline (from 12% to 21% of all pointers)."
**Verdict** OK.

### `sharma2024embedded` — Rust for Embedded Systems, ACM CCS 2024, 2296–2310
**Metadata** ✔ Crossref matches (booktitle wording differs cosmetically).
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3659` — interoperation is the central open problem in embedded Rust.
**Evidence — level A** (arXiv 2311.05063, p. 1, abstract): "**Rust interoperability enables
developing Rust applications on top of existing C codebases** … we found that existing Rust
software support is inadequate, SAST tools cannot handle certain features … and **the prevalence of
advanced types in existing Rust software makes it challenging to engineer interoperable code**."
**Verdict** OK.

### `mccormack2026unsafe` — A Mixed Methods Study on the Implications of Unsafe Rust, TOSEM (2026)
**Metadata** ✔ Crossref matches; no volume/issue yet, correctly omitted.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3660` — `unsafe` concentrates at exactly these boundaries.
**Evidence — level A** (arXiv 2404.02230, p. 1, abstract): "we study **how developers reason about
foreign function calls**, the limitations of the tools that they currently use … **limited tooling
support for foreign function calls made participants uncertain about their design choices, and
certain foreign aliasing and concurrency patterns were difficult to encapsulate**."
**Verdict** OK.

### `li2024rustforlinux` — An Empirical Study of Rust-for-Linux, USENIX ATC 2024, 425–443
**Metadata** ✔ DBLP confirms pages **425–443** and the five-author list.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3463, 3662` — the two largest documented adoptions into existing C and
C++ codebases report the same ordering of costs.
**Evidence — level A** (`atc24-li-hongyu.pdf`, p. 3): the paper frames the adoption "as we will
show, [as] **a mixture of success, dissatisfaction, and compromise**", after "over 20K lines of RFL
code being officially merged into Linux mainline since 2022".
**Verdict** OK.

### `fan2026android` — An Empirical Analysis of Rust Integration in AOSP, FSE Companion 2026, 545–556
**Metadata** ✔ Crossref matches.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3463, 3662` — paired with `li2024rustforlinux`.
**Evidence — level C** ACM paywall; title-level, and it is the second of the two "largest
documented adoptions" the sentence refers to.
**Verdict** OK.

### `ardito2021verbosity` — Evaluation of Rust Code Verbosity, Understandability and Complexity, PeerJ CS 7:e406
**Metadata** ✔ Crossref matches every field.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3676` — adoption evidence points at the learning curve rather than
run-time cost.
**Evidence — level B** Crossref-deposited abstract: "The Rust code had an **average verbosity** in
terms of the raw size of the code … **Rust code had a better Cyclomatic Complexity, Halstead
Metrics, and Maintainability Indexes than C and C++** but performed worse than the other considered
object-oriented languages."
**Verdict** OK.

### `crichton2024learning` — Profiling Programming Language Learning, PACMPL 8(OOPSLA1):29–54
**Metadata** ✔ Crossref matches every field.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3460, 3676` — the learning curve as the dominant adoption cost.
**Evidence — level A** (arXiv 2401.01257, p. 1, abstract; restated p. 2): "Over 13 months,
**62,526 readers answered questions 1,140,202 times** … we find that **many readers drop-out of the
book early when faced with difficult language concepts like Rust's ownership types**."
**Verdict** OK.

### `fulton2021adopting` — Benefits and Drawbacks of Adopting a Secure Programming Language, SOUPS 2021, 597–616
**Metadata** ✔ DBLP confirms pages **597–616** and the five-author list.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:3460, 3580, 3676, 3791`; `Thesis_v1.tex:157`; `Thesis_Plan_v2.tex:158` —
the dominant cost is human, not run-time.
**Evidence — level A** (`soups2021-fulton.pdf`, p. 2, abstract): "a range of positive features …
**as well as drawbacks including a steep learning curve, limited library support, and concerns
about the ability to hire additional Rust developers**"; p. 3: "**most seriously a steep learning
curve** to adjust to the paradigms that enforce security guarantees" and "much of the **cost of
adoption occurs up front**, while benefits tend to accrue later".
**Verdict** OK.

---

## C++ safety direction (WG21)

### `sutter2025profiles` — P3081R2, Core safety profiles for C++26
**Metadata** ✔ Document header: "Core safety profiles for C++26, Document Number: **P3081 R2**,
Date: **2025-02-04**, Reply-to: **Herb Sutter**, Audience: EWG, LEWG."
**Cited** `Ha_Vien_Mastersthesis_2026.tex:772` — profiles a conforming implementation must enforce wherever
enabled.
**Evidence — level A** (p. 4, §2.1 Strategy): "**Define standard enforced 'profiles' that a
conforming C++ implementation must enforce when enabled, notably bounds, type, and lifetime.**
… Each rule must be **deterministically decidable at compile time (even if it results in injecting
a check enforced at run time)** … Rules are portable and enforced in the C++ implementation, not in
a separate tool such as a static analyzer." The four profiles appear as §§4–7 (type, bounds,
lifetime, arithmetic).
**Verdict** OK.

### `vandevoorde2026profiles` — P3970R0, Profiles and Safety: a call to action
**Metadata** ✔ Document header: "Doc. No. **P3970R0**, Date: **2026-01-16**", authors David
Vandevoorde, Jeff Garland, Paul E. McKenney, Roger Orr, Bjarne Stroustrup, Michael Wong — exactly
the entry's list and order.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:779, 782, 4008` — the thesis quotes this document twice.
**Evidence — level A**:
- p. 1: "Currently, **there is – to the best of our knowledge – a specification and an experimental
  implementation is being conducted in a major C++ compiler**. Also, an implementation guide is
  being written." Then: "Beyond the framework implementation(s), **we need to design and precisely
  specify a few initial profiles**." → supports the quotation at 779.
- p. 2: "**After that, more profiles should be defined and implemented, notably a concurrency
  profile.**" → supports the quotation at 782 word for word.
**Verdict** OK. Both quoted fragments are verbatim.

### `baxter2024safecpp` — P3390R0, Safe C++
**Metadata** ✔ Published at safecpp.org as WG21 P3390R0; authors Sean Baxter and Christian
Mazakas; September 2024.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:774` — a proposal for a rigorously safe subset with borrow checking and
an accompanying standard library.
**Evidence — level A** (document body): the proposal's own compiler output shows "**borrow
checking**: iterator.cxx:10:11" under "safety: during safety checking of int main() safe", and the
comparison section states "**C++ lacks traits, relocation and borrow checking**".
**Verdict** OK.

---

## Concurrency runtimes and the closest prior work

### `skoudlil2025asyncrust` — A First Look at ROS 2 Applications Written in Asynchronous Rust, ECRTS 2025, LIPIcs 335, 1:1–1:21
**Metadata** ✔ The LIPIcs PDF's running heads confirm **1:1–1:21**, volume 335, ECRTS 2025, and
the three authors as entered.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:950, 3724` — the configuration that meets deadlines is not the idiomatic
work-stealing one; tail behaviour is a property of the runtime.
**Evidence — level A**:
- p. 5, §2.2.2: "**Tokio** is a popular multi-threaded runtime. It seems to be **designed to
  maximize throughput rather than time determinism**. Their scheduling policies are complex and
  difficult to understand due to the use of abstraction layers."
- p. 15: "**futures-rt and rclcpp-rt are the only variants where all callbacks manage to complete
  before the deadlines** given by the publication periods. All other implemented variants fail to
  meet shorter deadlines for topics 1–3. This is expected for the default configurations of Rust
  async runtimes."
- p. 1, abstract: "the experimental results indicate that our proposed structure **achieves bounded
  response times for time-critical tasks**."
**Verdict** OK — supports exactly the rebuttal the thesis builds on it.

### `karlback2021ran` — Karlbäck and Orö, Linköping University, 2021
**Metadata** ✔ mostly. The DiVA record (`urn:nbn:se:liu:diva-176307` → `diva2:1563049`) is the
right thesis: cover page reads "Linköping University, Department of Computer and Information
Science, Master's thesis, 30 ECTS, Datateknik, **2021**, **LIU-IDA/LITH-EX-A--2021/023--SE**,
*Holistic view on alternative programming languages for Radio Access Network applications in cloud
and embedded deployments*". One nuance: the cover lists **Anton Orö before Rasmus Karlbäck**; the
entry and the thesis text use "Karlbäck and Orö". DiVA's own citation order is alphabetical, so
this is defensible, but be aware the title page reads the other way.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1005, 3438, 3692, 3697, 3762, 3792`; `Thesis_v1.tex:139, 189, 222`;
`Thesis_Plan_v2.tex:80`.
**Evidence — level A**, claim by claim (page numbers are PDF pages of `FULLTEXT01.pdf`):
- *"conclude that C++ remains the choice where performance is critical"* (`Ha_Vien_Mastersthesis_2026.tex:3692`) —
  supported, p. 79: "It is quite clear that **C++ is the superior language if low CPU usage is
  important**", alongside the mixed processing-time results on the same page.
- *Memory: "find Rust the lowest of the three languages and C++ the highest, with the gap widening
  as concurrency rises"* (`Ha_Vien_Mastersthesis_2026.tex:3437`) — supported, p. 80: "**We see that C++ has the
  highest memory usage, especially when looking at larger amount of sequences, and Rust has the
  least memory usage.**"
- *"a pattern they flag as unexplained"* (`Ha_Vien_Mastersthesis_2026.tex:3438`) — **overstated.** Same passage,
  p. 80: "**What is surprising with these measurements is how little memory Rust uses. The main
  theory for this is that the initial stack size for the Rust green threads could be the
  smallest**, or that they adapt dynamically fast[er]…". They call it surprising and offer a
  theory — and their theory is the same green-thread mechanism the thesis then argues for, so
  saying so strengthens the thesis (fix #7).
- **The quotation at `Ha_Vien_Mastersthesis_2026.tex:3695–3697` — not found in the source.** The thesis prints:
  "an effort \ldots{} to utilize the different strengths of each language, and stay away from using
  exactly the same implementation". The source, §6.2.5 Implementation, p. 84 of the PDF (**printed
  page 74**), says: "This way we hopefully utilized the languages built-in support for the different
  parts of the code and gave each language an as representative solution as possible and **stayed
  away from using the exact same solution in each language**. We aimed for providing the best
  solution in each language, instead of trying to make the code as identical as possible between
  the languages." And later on the same page: "…a real world scenario where a programmer most
  likely would, and should, **utilize the strengths of each language** when implementing the
  solution." The phrase "an effort was made" does occur on that page, but in a different sentence
  about a different subject: "**Although an effort was made to minimize this**, multiple
  implementation details could probably have been done better" — where "this" is their own
  inexperience skewing results in C++'s favour.
  **Suggested replacement** (accurate, and makes the same point):
  > The authors record that they deliberately did not write the same program three times: they
  > "aimed for providing the best solution in each language, instead of trying to make the code as
  > identical as possible between the languages", and "stayed away from using the exact same
  > solution in each language"~\cite{karlback2021ran}.
**Verdict** **FIX** — the substance is right, the quotation marks are not (fix #1).

### `arvidsson2025async` — Arvidsson and Kaller, Linköping University, 2025
**Metadata** ✔ The DiVA record (`urn:nbn:se:liu:diva-214746` → `diva2:1970356`) matches on every
field: "Master's thesis, 30 ECTS, Computer Science and Engineering, **2025**,
**LIU-IDA/LITH-EX-A--25/055--SE**, *Evaluating Asynchronous Programming Frameworks for 5G Control
Plane Procedures*, **Albin Arvidsson, Martin Kaller**", external supervisor at Ericsson.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:1007, 2933, 3338, 3708, 3761, 3793, 4128`; `Thesis_v1.tex:142, 222`;
`Thesis_Plan_v2.tex:85`.
**Evidence — level A**, claim by claim (PDF pages):
- *Frameworks compared and Boost.Fibers fastest* — p. 3, abstract: "**C++ with Boost.Fibers, Rust
  with both Tokio and Monoio, Go with Goroutines, and Erlang** … The research reveals that **C++
  with Boost.Fibers achieves the highest performance, exhibiting the lowest latency and highest
  throughput, while Rust frameworks present a competitive alternative.**"
- *"Boost.Fibers shows the lowest latency at every load"* (`Ha_Vien_Mastersthesis_2026.tex:3709`) — p. 50: "**it is
  evident that Boost.Fibers consistently exhibits the lowest latency**" across the load sweep;
  same page: "as the load, sequence frequency, increases, latency also rises".
- *"the Rust runtimes track it at the median, their 99th percentile rises more steeply beyond a
  certain request rate"* — supported by §9.1.2 (p. 77) plus the load-sweep figures: "C++ with
  Boost.Fibers displays a **minimal difference between** [median and p99]… In contrast, **both Rust
  frameworks exhibit a much greater disparity between their median and 99th percentile
  latencies**", with the effect "especially under high-load conditions" (p. 78). The *shape* claim
  (rate threshold) is read off their figures rather than a sentence — accurate, but if challenged,
  point to the figures.
- *"the authors attribute the effect to stackless `async`/`await` permitting a context switch
  immediately before an I/O operation is initiated"* (`Ha_Vien_Mastersthesis_2026.tex:3713–3715`) — **exact**,
  §9.1.2, pp. 77–78: "**Rust utilizes stackless async/await** for user-level threading, whereas
  C++ with Boost.Fibers employs stackful fibers … **both Rust frameworks may perform a context
  switch at any await point** … **Scenario 2 can occur in Rust, where a context switch happens just
  before an I/O operation is initiated** … This behavior leads to increased latency, **particularly
  noticeable in the 99th percentile latency measurements**."
**Verdict** OK — the strongest rival result in the thesis is represented fairly and attributed in
the source's own terms.

---

## Tooling

### `lizard` — Terry Yin, Lizard cyclomatic complexity analyser
**Metadata** ✔ PyPI: author **Terry Yin**, project home `lizard.ws`, GitHub `terryyin/lizard`;
version **1.23.0** exists and is the current release (uploaded 2 June 2026), consistent with
"Version 1.23.0. Accessed August 2026" and `year = 2026`.
**Cited** `Ha_Vien_Mastersthesis_2026.tex:2179, 2205` — cyclomatic complexity measured with one tool applied
identically to both languages.
**Evidence — level A** Registry record as above.
**Verdict** OK. Pinning the version in the entry is exactly right for reproducibility.

---

## Appendix: what remains unverified

Everything below is metadata-confirmed; only the supporting passage was not opened, because the
publisher blocks automated access. None of these carries a number or a quotation in the thesis —
each is used for a title-level claim or inside a list — so the risk is low. If you want full
coverage, these are the ones to open through the university proxy:

`pereira2017energy`, `balasubramanian2017rust`, `levy2017kernel`, `mo2023rustshyper`,
`qazi2017pepc`, `liu2023l25gc`, `park2025ctrlbench`, `huang2017predictability`, `li2021ipc`,
`xiao2024rpkt`, `zhang2022runtime`, `cui2025perfbugs`, `bae2021rudra`, `qin2024safety`,
`rivera2021galeed`, `kirth2022pkrusafe`, `li2022crosslang`, `schuermann2023encapsulated`,
`fan2026android`, `klabnik2023rust` (chapter reference), `3gpp38331` (clause 5.3),
`3gpp22261` (clause 7 KPIs).

Two of these are worth a second look for a different reason: `zhang2022runtime` and
`harris2023morello` are the mechanisms the thesis names as candidates for the unexplained
operation-level result, and `bench/TESTBED.md` lists the counter instrumentation that would
settle it. That is a measurement gap, not a citation gap.
