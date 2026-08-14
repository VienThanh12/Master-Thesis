# Literature sweep, August 2026

Candidate sources for `Thesis_POC.tex`, found by searching for work published after the current
bibliography was assembled.

> **Status, 10 August 2026.** The core set (§10, items 1–7) has been **applied**: eleven entries
> added to `bibliography.bib` and the accompanying prose written into `Thesis_POC.tex`. The build is
> clean at 141 pages with no undefined citations. One deviation: the C++ profiles threat was
> written into the external-validity prose of §"Threats to validity" rather than added as a row
> to `tab:threats`, because the companion figure `25_threats_validity.drawio` is hand-laid-out
> and a table row without a matching diagram row would leave the two inconsistent. Everything
> else in this file remains a candidate, not a commitment.

**Baseline:** `bibliography.bib` currently holds 65 entries. The newest are `cai2026interop`,
`mccormack2026unsafe`, and `fan2026android` (2026); `tang2025converos`, `cui2025perfbugs`,
`park2025ctrlbench`, `arvidsson2025async`, and `xiao2024rpkt` (2025).

**Verification convention.** Every entry is marked:

- **VERIFIED** — metadata read off a primary source (publisher page, arXiv abstract, official
  standards or government site). Safe to cite.
- **PARTIAL** — the source exists and was read, but at least one bibliographic field still needs
  confirming. The field in question is named.
- **NOT CITABLE** — found during the search, listed only so it is not re-found later. Do not cite.

No entry in this file was written from memory. Anything that could not be confirmed against a
primary source is marked rather than filled in.

---

## 1. What matters most

### Changes an argument

1. **C++ safety profiles (WG21, 2024–2026).** The thesis argues that C++ leaves safety to the
   programmer while Rust enforces it in the compiler. That is currently stated as a static fact.
   It is a moving target: WG21 has an active, Stroustrup-backed programme to put enforced safety
   guarantees into the language, and rejected a Rust-style borrow-checking proposal in favour of
   it. This is the largest genuine hole in the thesis. See §2.
2. **Škoudlil et al., ECRTS 2025.** Peer-reviewed, artifact-evaluated evidence that async Rust's
   timing behaviour depends on how the runtime is structured, naming the specific Tokio mechanisms
   involved. The thesis's answer to its strongest rival result — Arvidsson and Kaller's tail
   divergence — currently rests on the thesis's own reasoning. This supplies a citation for it.
   See §4.5.
3. **Michaelides et al., WiSec 2026.** Measures the CU-CP-to-DU **UE Context Setup** procedure
   over F1-C, 1,000 repetitions on a disaggregated OAI testbed. That is the procedure class the
   UECM service implements. The thesis's latency budget is currently motivated from specification
   targets; this anchors it in a published measurement of the same procedure. See §7.2.
4. **Zhou et al., CIDR 2025.** In a mature shared-nothing system with one partition and one worker
   thread per core, *communication* — not execution — is now the bottleneck. This is independent
   corroboration of the thesis's most surprising result, that the operation itself is 0.04% of
   end-to-end cost and the handoff is the rest. It turns an apparent anomaly into an instance of a
   documented pattern. See §7.6.

### Upgrades or fills a citation

5. **Schroeder et al., NSDI 2006.** The queueing-theoretic separation of open- and closed-loop
   load generation — the peer-reviewed root cause of coordinated omission, which the thesis
   currently carries on a conference talk. See §7.1.
6. **Google's 2025 Android data.** The thesis cites the 2022 Android post. The 2025 update
   reports a ~1000× lower memory-safety vulnerability density for Rust, and — new, and directly
   on RQ4 — a 4× lower rollback rate and 25% less code-review time. It also documents the first
   Android Rust memory-safety near-miss. See §3.1.
7. **Watson et al., CACM, February 2025.** A 22-author position paper on memory-safety
   standardization, in a venue that outranks the vendor blogs and government reports the
   motivation currently rests on. See §3.2.
8. **The EU Cyber Resilience Act.** The regulatory motivation in the thesis is entirely American
   (ONCD, CISA, NSA). For a thesis written in Finland about a European vendor's product, the
   EU regulation with binding dates in 2026 and 2027 is the more relevant instrument. See §3.4.
9. **Alsoran and QCore.** A Rust gNB-CU — the thesis's exact subsystem, in the thesis's exact
   language — exists as open source and is not mentioned. It needs acknowledging before an
   examiner finds it. See §4.1.

---

## 2. C++ is changing under the thesis's feet

**Why this matters.** §"C++ for latency-critical systems" (Thesis_POC.tex:645–680) says safety in
C++ "remains the programmer's responsibility rather than a property the compiler enforces", and
that C++ "mitigates these defects with tooling rather than with language guarantees". Both
sentences are true of C++23 as shipped, which is what the C++ implementation targets. But the
committee is explicitly trying to change this, and the thesis says nothing about it. An examiner
who follows C++ will notice.

The argument survives the update, and stating it makes the thesis stronger rather than weaker:
profiles did not ship in C++26, the framework was still seeking implementations as of January
2026, a concurrency profile is explicitly deferred until after the initial set, and RQ2's
catalogue includes two concurrency defects. What the thesis should not do is leave the
impression that it did not know.

### 2.1 Sutter, "Core safety profiles for C++26" — VERIFIED

WG21 P3081R2, 2025-02-04, Herb Sutter. <https://isocpp.org/files/papers/P3081R2.pdf>

Proposes standard enforced profiles (`type`, `bounds`, `lifetime`, `arithmetic`) that a
conforming implementation must enforce when enabled. The design constraint is worth quoting in
the thesis: each rule "must be deterministically decidable at compile time (even if it results
in injecting a check enforced at run time)". That parenthesis is the whole difference from
Rust's model, and it is the authors' own words rather than the thesis's characterisation.

### 2.2 Vandevoorde et al., "Profiles and Safety: a call to action" — VERIFIED

WG21 P3970R0, 2026-01-16. Authors: David Vandevoorde, Jeff Garland, Paul E. McKenney, Roger Orr,
Bjarne Stroustrup, Michael Wong.
<https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3970r0.pdf>

The single most useful citation in this section, because it is the profiles authors themselves
describing how far the work has *not* got, seven months before this thesis is submitted. Three
things in it are directly quotable:

- The framework is not yet broadly implemented: "there is — to the best of our knowledge — a
  specification and an experimental implementation is being conducted in a major C++ compiler."
- The initial profiles are still to be designed and specified.
- The concurrency profile is explicitly future work: "After that, more profiles should be defined
  and implemented, notably a concurrency profile."

That last point is the thesis's answer in one line. RQ2 covers data races, lock-order deadlock,
and lost update; the C++ proposal that would address those is the one the authors place after the
ones that have not been specified yet.

### 2.3 Baxter and Mazakas, "Safe C++" — VERIFIED

WG21 P3390R0, September 2024. Authors: Sean Baxter, Christian Mazakas.
<https://safecpp.org/P3390R0.html>, tracked at
<https://github.com/cplusplus/papers/issues/2045>

A proposal to add a rigorously safe subset to C++ with borrow checking and a new standard
library — Rust's model, in C++. Useful to the thesis as evidence that the comparison it draws is
the one the C++ community itself drew.

**The SG23 poll** ("Which should we prioritize: Profiles or Safe C++?") returned Profiles 19,
Both 11, Neutral 6, Safe C++ 9. This was at the Wrocław meeting, November 2024 — recorded in the
issue thread above by Roger Orr on 2024-11-21. Note that at least one secondary source dates this
poll to Hagenberg in February 2025; the primary record says Wrocław 2024. Cite the issue thread
or the meeting minutes, not the blog.

### 2.4 Supporting sources — VERIFIED

- **Stroustrup, "21st Century C++"**, Blog@CACM, 4 February 2025.
  <https://cacm.acm.org/blogcacm/21st-century-c/>. Sets out the profiles vision for a general
  audience. Useful as the citable statement of the position.
- **Stroustrup, "Note to the C++ standards committee members"**, WG21 P3651R0, 2025-03-06.
  <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3651r0.pdf>. Stroustrup's own
  framing of the pressure: "unprecedented, serious attacks on C++". He also records that C++26
  will have a hardened standard library, and states his disappointment that profiles were not
  guaranteed for C++26.

**PARTIAL — needs one check before citing.** The claim that `[[profiles::enforce]]` is deferred
to C++29 comes from a secondary blog. The primary evidence assembled here supports the weaker and
sufficient statement that *as of January 2026 profiles were not in the standard and the framework
was still seeking implementations* (P3970R0), which is all the thesis needs. If a stronger claim
about C++29 is wanted, confirm against WG21 P5000 ("Direction for ISO C++29") first.

### 2.5 Where it goes

- **§"C++ for latency-critical systems" (Thesis_POC.tex:645–680)**, as a new paragraph after the
  tooling paragraph at line 672. Roughly: the committee is addressing this, here is the shape of
  it, here is why the comparison in this thesis is against C++23 as deployed, and here is why the
  concurrency half of RQ2 is unaffected either way.
- **§"Threats to validity" (Thesis_POC.tex:3586)**, under external validity. There is currently no
  row for "the object of comparison is itself moving". It belongs in `tab:threats` as a
  construct- or external-validity row: control is that the comparison is pinned to a named
  standard and compiler version; residual is that a future C++ closes part of the gap.
- **Conclusion / future work (Thesis_POC.tex:3774)**, as a natural re-run condition: repeat the RQ2
  catalogue once an implementation ships an enforced lifetime profile.

---

## 3. Memory-safety evidence and regulation

### 3.1 Vander Stoep, "Rust in Android: move fast and fix things" — VERIFIED

Jeff Vander Stoep, Google Security Blog, 13 November 2025.
<https://blog.google/security/rust-in-android-move-fast-fix-things/>

Direct successor to the already-cited `google2022android`. Numbers, all read off the post:

| Finding | Value |
| --- | --- |
| Memory-safety share of total Android vulnerabilities (2025) | below 20% for the first time |
| Rust memory-safety vulnerability density | ~0.2 per MLOC (5M lines, 1 pre-release vuln) |
| Historical C/C++ density | ~1000 per MLOC |
| Rollback rate, medium and large changes | ~4× lower for Rust than C++ |
| Time in code review | ~25% less for Rust |
| Revisions per change of similar size | ~20% fewer for Rust |
| Share of Android Rust inside `unsafe{}` | ~4% |

The productivity numbers are the important ones for this thesis, and they are new. RQ4 asks what
incremental adoption costs; this is the largest published dataset saying the steady-state cost is
negative. It is measured with the DORA framework on first-party Android changes, with the
comparison controls stated in the post (similar change sizes, overlapping developer pools, trends
tracked over time).

Two caveats to state if cited: the figures are self-reported and not peer-reviewed, and the
1000× density ratio rests on a single pre-release finding, so it is an order-of-magnitude claim
rather than a measurement. Google says as much ("a conservative estimate").

**The near-miss is separately useful for RQ2.** CVE-2025-48530, a linear buffer overflow in
CrabbyAVIF, in `unsafe` Rust, caught before release; Android's Scudo hardened allocator rendered
it non-exploitable via guard pages. This is a clean, citable instance of the thesis's own
argument that the guarantee is bounded by `unsafe`, and it pairs with the thesis's design choice
of keeping the core `unsafe`-free.

**Where it goes:** update the sentence at Thesis_POC.tex:667–668 that currently cites
`google2022android`; §"Discussion on the research questions" for RQ4; and the engineering
guidelines section (Thesis_POC.tex:3300).

### 3.2 Watson et al., "It Is Time to Standardize Principles and Practices for Software Memory Safety" — VERIFIED

*Communications of the ACM* 68(2):40–45, February 2025. DOI 10.1145/3708553.
<https://cacm.acm.org/opinion/it-is-time-to-standardize-principles-and-practices-for-software-memory-safety/>

Twenty-two authors from Cambridge, SRI, Google, Microsoft, Arm, MIT Lincoln Laboratory, King's
College London and others, arguing that there is no shared technology-neutral framework for
specifying memory-safety requirements and that this blocks adoption. An extended version exists
as Cambridge technical report UCAM-CL-TR-996.

**Why it is worth adding:** the memory-safety motivation in the thesis currently rests on a
Microsoft conference talk, Google blog posts, and government reports. This is the same argument
in a peer-reviewed venue with named academic authors, and it is the strongest single citation
available for the claim. Straight upgrade for the citation cluster at Thesis_POC.tex:3425–3429 and
the motivation in Chapter 1.

### 3.3 NSA and CISA, "Memory Safe Languages: Reducing Vulnerabilities in Modern Software Development" — VERIFIED

Joint Cybersecurity Information Sheet, 24 June 2025.
<https://www.cisa.gov/resources-tools/resources/memory-safe-languages-reducing-vulnerabilities-modern-software-development>
PDF: <https://media.defense.gov/2025/Jun/23/2003742198/-1/-1/0/CSI_MEMORY_SAFE_LANGUAGES_REDUCING_VULNERABILITIES_IN_MODERN_SOFTWARE_DEVELOPMENT.PDF>

The 2025 successor to the already-cited `cisa2023memorysafe`. More useful to this thesis than its
predecessor because it is about *adoption* rather than about the case for adoption: it addresses
obstacles, and explicitly states that adoption "does not require existing code to be completely
rewritten", recommending interoperability with existing codebases. That is RQ4's premise stated
by the agencies, and it is a better citation for the incremental-adoption framing than anything
currently in the bibliography.

### 3.4 EU Cyber Resilience Act — VERIFIED

Regulation (EU) 2024/2847 of the European Parliament and of the Council of 23 October 2024 on
horizontal cybersecurity requirements for products with digital elements and amending Regulations
(EU) No 168/2013 and (EU) 2019/1020 and Directive (EU) 2020/1828 (Cyber Resilience Act).
OJ L, 2024/2847, 20 November 2024. <https://eur-lex.europa.eu/eli/reg/2024/2847/oj>

In force 10 December 2024; reporting obligations apply from 11 September 2026; main obligations
from 11 December 2027.

**Why it belongs.** Every regulatory citation in the thesis is American. The thesis is written at
a Finnish university about a European vendor's product. The CRA imposes secure-by-design and
lifecycle vulnerability-management obligations on manufacturers placing products on the EU
market, with liability for exploitable vulnerabilities, and its first binding date falls one
month before this thesis is due. It does not name a language — that point must be made carefully
and is the honest reading — but it is the instrument that actually applies to the subject of the
case study.

**Where it goes:** §"Motivation and industrial context" (Thesis_POC.tex:291), alongside the existing
ONCD and CISA citations. One or two sentences, no more.

---

## 4. Rust in the RAN, and in latency-critical systems

### 4.1 Alsoran — VERIFIED (as a software artefact)

<https://github.com/nplrkn/alsoran> — "5G gNodeB Centralized Unit written in Rust". Proof of
concept, no longer actively developed; the README directs readers to QCore.

This is uncomfortably close to the thesis and should be acknowledged rather than left for an
examiner to raise. What it has: separate CU-CP and CU-UP communicating over E1; ASN.1 libraries
for NGAP, E1AP, F1AP and RRC; scale-out of gNB-CU-CP workers across multiple TNLAs; stateless
workers with UE state in an external store. Its own framing is that "Rust is an attractive choice
of language for new O-RAN development. The main barrier to entry is the ASN.1 and SCTP based
protocols."

**How it strengthens rather than threatens the thesis.** Alsoran is an existence proof that a
gNB-CU can be written in Rust; it is explicitly not a controlled comparison, reports no latency
measurements, and has no C++ counterpart. It occupies the "someone built one" cell, which is
different from the cell this thesis claims. It also independently corroborates two of the
thesis's design decisions — shard-style stateless workers, and treating UE context state as the
thing to get right — which is worth a sentence.

Note also that Alsoran's stated barrier (ASN.1/SCTP) is precisely what the frozen specification
abstracts away, which is a fair scoping remark for the limitations section.

### 4.2 QCore — VERIFIED (as a software artefact)

<https://github.com/nplrkn/qcore> — Nic Larkin, 2025, AGPL. Monolithic private 5G core in Rust;
32 MB executable; reported 30,000 control-plane messages per second on a single CPU core; eBPF
user plane. In "F1 mode" it takes the gNB-CU role, exposing F1-C and F1-U.

The stated motivation is the thesis's own thesis, from the other direction: a monolith to
"minimize control plane processing cost … avoids a lot of the usual network hops, context
switches, database accesses and (de)serialization". Useful in the background chapter as
industrial evidence that control-plane processing cost is a live design concern, and as a
throughput data point in Rust.

Both are software, not papers. Cite as `@misc` with an access date, and treat the performance
figures as vendor-reported.

### 4.3 Esper et al., Wasm-based dApps for real-time RAN — VERIFIED

"Enabling Real-Time Programmability for RAN Functions: A Wasm-Based Approach for Robust and
High-Performance dApps". João Paulo Esper, Yure Freitas, Pedro Souza, Bruno Silvestre, Joao F.
Santos, Alexandre Huff, Cristiano Both, Kleber Cardoso (UFG, UNISINOS, Virginia Tech/CCI, UTFPR).
arXiv 2603.17880. <https://arxiv.org/abs/2603.17880>

A Rust-based Wasm runtime executing untrusted applications inside O-RAN CU/DU functions, reporting
"predictable, deterministic performance, strong isolation, and low latency" for real-time control
loops. Relevant as recent, in-domain evidence that predictability under isolation is an active
RAN research question, and that Rust is the implementation language of choice for the runtime.

*Check whether it has since appeared in a peer-reviewed venue before citing the preprint.*

### 4.4 Lacava et al., dApps reference architecture — VERIFIED

"dApps: Enabling real-time AI-based Open RAN control". Andrea Lacava, Leonardo Bonati, Niloofar
Mohamadi, Rajeev Gangula, Florian Kaltenberger, Pedram Johari, Salvatore D'Oro, Francesca Cuomo,
Michele Polese, Tommaso Melodia. *Computer Networks* 269:111342, 2025.
DOI 10.1016/j.comnet.2025.111342. (Preprint: arXiv 2501.16502.)

Journal-published, not a preprint — cite the *Computer Networks* version. Note that Michele
Polese is already in the bibliography as `polese2023oran`, so this is a familiar and reputable
group in the thesis's own domain.

Reports average control latency below 450 µs for real-time control loops on an OAI-based gNB.
Useful as a published, in-domain number for what "real-time" means in the RAN control plane —
§"Tail latency and predictability in RAN" (Thesis_POC.tex:1088) currently has no external anchor of
this kind.

### 4.5 Škoudlil et al., async Rust and bounded response times — VERIFIED

"A First Look at ROS 2 Applications Written in Asynchronous Rust". Martin Škoudlil, Michal Sojka,
Zdeněk Hanzálek (Czech Technical University in Prague). ECRTS 2025, LIPIcs vol. 335, article 1,
pages 1:1–1:21. DOI 10.4230/LIPIcs.ECRTS.2025.1. Artifact-evaluated (DARTS DOI
10.4230/DARTS.11.1.2). Preprint: arXiv 2505.21323.

**The most useful single find after the C++ profiles material, and it is not obvious from the
title.** The domain is robotics, not telecoms, so it looks off-topic — but it addresses the exact
mechanism behind the result the thesis treats as its strongest challenge.

`arvidsson2025async` reports that Rust's async runtimes track C++ Boost.Fibers at the median but
diverge at the 99th percentile beyond a certain request rate, and attributes this to stackless
`async`/`await` permitting a context switch immediately before an I/O operation. This paper
attacks the same problem from the other side: it analyses the execution model of asynchronous
Rust runtimes against thread-based C++, and shows that a particular application structure —
separating event sampling from callback execution into threads with distinct priorities —
achieves bounded response times matching classical response-time analysis, outperforming the
other configurations tested.

That converts the thesis's current argument from an assertion into a cited one. The thesis says
the tail divergence is a property of Tokio and Monoio rather than of Rust; this is peer-reviewed,
artifact-evaluated evidence, at a top real-time venue, that async Rust's timing behaviour is a
function of how the runtime is structured. It also independently supports the thesis's decision to
use a thread-per-shard model with no async runtime at all, which is currently justified only on
fairness grounds.

**It also names the mechanisms**, which is what makes it quotable rather than merely supportive.
The authors state that Tokio is "designed to maximize throughput rather than time determinism" and
that its policies are "complex and difficult to understand due to the use of abstraction layers",
then document the specifics: a three-deep LIFO slot per worker, a 256-entry local queue, and
stealing half of a victim worker's queue. Their deadline-meeting configuration uses the `futures`
runtime with explicit thread priorities rather than Tokio; the idiomatic Tokio configurations miss
deadlines. They further note that Rust's requirement to associate data explicitly with
synchronisation primitives means poor data structuring causes "unwanted blocking of unrelated
threads, negatively influencing the timing" — which is an argument for the thesis's shard-owned
state, not against Rust.

**Where it goes:** §"Related work" (Thesis_POC.tex:3506–3520), in the passage on Arvidsson and Kaller;
and §"Concurrency models for control-plane software" (Thesis_POC.tex:801) where the choice not to use
an async runtime is made. Pair it with the cooperative-scheduling mechanism paper in §7.7.

---

## 5. Where the Rust guarantee stops (RQ2)

### 5.1 Logic bugs in production Rust: the `rust_binder` CVEs — VERIFIED

Both confirmed against the CVE Program record (assigner: Linux kernel CNA), state PUBLISHED.

- **CVE-2026-23194**, published 14 February 2026 — "rust_binder: correctly handle FDA objects of
  length zero". An empty file-descriptor array triggered an 8-byte out-of-bounds write, because
  `skip == 0` was overloaded to mean "pointer fixup". The fix replaced the sentinel with a Rust
  enum. The overloaded-sentinel pattern was inherited from the C implementation of Binder.
- **CVE-2026-64467**, published 25 July 2026 — "rust_binder: use a u64 stride when cleaning up
  the offsets array". The `Drop` path walked an array of 8-byte offsets with a `usize` stride. On
  32-bit kernels this traverses an N-entry array 2N times and over-decrements a refcount,
  corrupting Binder's reference accounting.

**Why these are valuable.** This is exactly the argument RQ2 is built to make, occurring in
production, in the highest-profile Rust-in-C-codebase migration there is. Neither is a
memory-safety failure of safe Rust: one is an integer-width logic error, the other an API design
flaw carried over from the C original. They support the thesis's framing that the guarantee has a
boundary and that the defects which survive it are logic and concurrency defects — the same
reasoning behind including lock-order deadlock and lost update in the catalogue.

The second one is the better story: a defect that migrated across the language boundary because
the Rust port reproduced a C interface convention. That is a migration-cost observation as much as
a safety one, so it serves RQ4 as well.

Cite the kernel CVE announcements or NVD entries, not aggregator sites.

### 5.2 Verification tooling and its concurrency gap

- **Kani: A Model Checker for Rust** — VERIFIED as arXiv 2607.01504, 1 July 2026. Twelve authors
  (Rémi Delmas, Zyad Hassan, Qinheping Hu, Rahul Kumar, Felipe R. Monteiro, Thanh Nguyen, Adrián
  Palacios, Celina Val, Michael Tautschnig, Justus Adam, Daniel Schwartz-Narbonne, Carolyn Zech).
  The arXiv comment records acceptance at the ASE 2026 Industry Showcase Track, so there is no
  proceedings DOI yet — cite the preprint and note the acceptance. *One caution:* the comment
  calls ASE 2026 the "39th" conference, which does not match the official numbering; do not
  reproduce the ordinal.

  The relevant fact for this thesis is a stated limitation: Kani is restricted to sequential Rust
  and does not model threads, `async`/`await`, atomics, or the aliasing models. For concurrency
  the Kani documentation points to Loom and Shuttle
  (<https://model-checking.github.io/kani/tool-comparison.html>, VERIFIED).
- **"Surveying the Rust Verification Landscape"** — VERIFIED as arXiv 2410.01981, 2 October 2024,
  by Alex Le Blanc and Patrick Lam. No journal or proceedings DOI; cite as a preprint. Survey
  covering Prusti, Creusot, Verus, Aeneas, Kani. Notes that even tools which do verify `unsafe`
  code miss a range of undefined behaviour including data races and lifetime-aliasing violations.
- **Verus: A Practical Foundation for Systems Verification** — VERIFIED. Andrea Lattuada, Travis
  Hance, Jay Bosamiya, Matthias Brun, Chanhee Cho, Hayley LeBlanc, Pranav Srinivasan, Reto
  Achermann, Tej Chajed, Chris Hawblitzel, Jon Howell, Jacob R. Lorch, Oded Padon, Bryan Parno.
  SOSP 2024, pages 438–454, DOI 10.1145/3694715.3695952. Verifies safe and unsafe Rust in one
  framework; the reported cost is roughly 5 lines of proof per line of implementation.
  (**VerusBelt**, DOI 10.1145/3808325, is the semantic soundness proof — probably one level of
  detail beyond what this thesis needs.)

**Where this goes.** §"Discussion on the research questions" already argues that the defects safe
Rust does not prevent are caught later rather than never. That argument is currently made from the
thesis's own results. These sources let it be made from the state of the art as well: the
tooling that would catch lock-order deadlock at compile time is exactly the tooling that does not
yet handle concurrency. It also sharpens the existing `zhang2024deadlock` citation.

### 5.3 Tree Borrows — VERIFIED

Neven Villani, Johannes Hostert, Derek Dreyer, Ralf Jung. *Proceedings of the ACM on Programming
Languages* 9(PLDI):1019–1042, 2025. DOI 10.1145/3735592. The thesis cites Stacked Borrows
(`jung2020stacked`) as the aliasing model for `unsafe` code. Tree Borrows is the newer model from
an overlapping author group. Since the thesis cites the aliasing model only in passing, this is a
low-effort accuracy fix rather than new argument: cite both, or cite the newer one.

---

## 6. Migration cost and automated translation (RQ4)

The thesis measures migration cost by building an FFI seam by hand. A body of work published
since has been measuring the same cost with automation, and it is now large enough that its
absence is noticeable in §"Related work".

### 6.1 Rust Foundation Interop Initiative — PARTIAL

<https://github.com/rustfoundation/interop-initiative> — problem statement.

The document carries no author byline. Cite it as a corporate-authored technical document
("Rust Foundation") with an access date, rather than attributing it to an individual. **This is
the least-verified item in this file** — confirm the intended citable form before use, and treat
it as optional supporting material rather than load-bearing evidence.

The clearest available statement of why the C ABI is the constraint: no toolchain compiles both
languages in one source file, so interoperation goes through platform C ABIs, and "the more
C++-specific facilities are relied upon, the greater the challenge becomes". It also assesses
`cxx` — already mentioned at Thesis_POC.tex:844 — as "restrictive and opinionated" by its own
description and incomplete for arbitrary interoperation. Good support for the thesis's decision
to use a plain `extern "C"` seam, which is currently justified on the thesis's own terms.

### 6.2 Automated C-to-Rust translation

- **Hong and Ryu, "Automatically Translating C to Rust"** — VERIFIED. Jaemin Hong, Sukyoung Ryu
  (KAIST). *Communications of the ACM* 68(11):58–65, 2025. DOI 10.1145/3737696.
  Survey of why C2Rust output is unidiomatic and unsafe-heavy and what refinement passes exist.
  Also notes that DARPA has a programme on automatic C-to-Rust translation. **The best single
  citation if only one is wanted** — peer-reviewed, in a general venue, and it summarises the
  others.
- **EvoC2Rust** — VERIFIED as arXiv 2508.04295 (Chaofan Wang, Tingrui Yu, Beijun Shen, Jie Wang,
  Dong Chen, Wenrui Zhang, Yuling Shi, Chen Xie, Xiaodong Gu), **accepted at ICSE 2026 SEIP**.
  Project-level translation; reports 92.25% module-level compilation success and 89.53% test pass
  rate on six industrial projects.
- **Feng et al.** — VERIFIED as arXiv 2604.02852 (Jia Feng, Wenjie Gan, Cuiyun Gao, Chaozheng
  Wang, Feng Luo, Xin Xia, Ge Li, Kui Liu), **accepted at FSE 2026 Industry**. Dependency-guided
  repository-level translation.
- **Rustine**, "Translating Large-Scale C Repositories to Idiomatic Rust" — VERIFIED as arXiv
  2511.20617 (Saman Dehghan, Tianran Sun, Tianxiang Wu, Zihan Li, Reyhaneh Jabbarvand),
  25 November 2025. No venue yet; preprint only. 23 C repositories (27–13,200 LOC), fully
  compilable Rust with no human intervention, 87% functional equivalence against test suites,
  averaging 3.92 hours and $0.48 per repository, with 4.5 hours of human effort to resolve
  semantic mismatches where assertions failed.
- **SACTOR**, ACL 2026 — two-stage translation validated end-to-end through the FFI, the same
  mixed C-and-Rust configuration the thesis builds by hand for RQ4. *Metadata not confirmed;
  verify the author list and proceedings pages before citing.*

Numbers quoted above are as reported in the abstracts, not independently checked.

**How to use these without overclaiming.** They do not measure what RQ4 measures. They translate
C (not C++), they optimise for compilability and test-passing (not for run-time cost at the seam),
and none reports latency across the boundary. That is the point: they make the thesis's
measurement complementary rather than superseded. One or two sentences in §"Related work" and a
sentence in future work is the right weight — this is a fast-moving area and a thesis submitted in
November 2026 should be seen to know it exists.

### 6.3 An FFI overhead figure to *not* cite — NOT CITABLE

A Chromium-to-Rust migration experiment circulating with a "FFI crossing is 50–290× slower"
figure is a commit message in a personal GitHub repository, and the comparison is against a
different workload rather than a matched one. The thesis's own A/B measurement of the seam is
better evidence than this. Ignore it.

---

## 7. Measurement methodology and control-plane performance

This section is the second search pass. It is aimed at the parts of the thesis that are about
*how* things were measured rather than about Rust or C++, and it turned up two of the strongest
finds in this whole file (§7.2 and §7.6).

### 7.1 A citable foundation for the load generator

The thesis already handles coordinated omission correctly (Thesis_POC.tex:629, 638, 3693), but the
citation carrying it is `tene_hdrhistogram`, a conference talk. That is a weak load-bearing
reference for a methodology chapter. There is a canonical peer-reviewed alternative.

**Schroeder, Wierman and Harchol-Balter, "Open Versus Closed: A Cautionary Tale"** — VERIFIED
(DBLP; USENIX page live). NSDI '06, San Jose, 2006. No DOI (USENIX did not assign them).
<https://www.usenix.org/conference/nsdi-06/open-versus-closed-cautionary-tale>

Formally separates closed-loop generation (a new request is triggered only by a completion) from
open-loop generation (arrivals independent of completions), and shows via implementation and
trace-driven simulation that the two produce drastically different response-time behaviour on the
same system. Response times under closed models are systematically lower. It also shows that
scheduling-policy choice matters far more in open systems than closed ones.

This is the queueing-theoretic root cause of what practitioners call coordinated omission. It
lets the open-loop UECM generator be justified from theory rather than from a talk. **Recommended
as the primary citation**, with Tene retained as a supporting practitioner reference.

Supporting, in descending order of usefulness:

- **Friedrich, Wingerath and Ritter, "Coordinated Omission in NoSQL Database Benchmarking"** —
  VERIFIED (GI digital library page live). BTW 2017, Gesellschaft für Informatik, LNI. No DOI.
  <https://dl.gi.de/handle/20.500.12116/918>. The only peer-reviewed paper found that addresses
  coordinated omission *by name*. Argues that adding HdrHistogram to YCSB mitigated but did not
  solve the problem, because the generator remained closed-loop. Worth citing precisely because it
  makes the distinction the thesis relies on: correcting the histogram is not the same as opening
  the loop.
- **van der Kouwe, Heiser, Andriesse, Bos and Giuffrida, "SoK: Benchmarking Flaws in Systems
  Security"** — VERIFIED. IEEE EuroS&P 2019, pp. 310–325, DOI 10.1109/EuroSP.2019.00031.
  Catalogues 22 benchmarking flaws and finds an average of five per tier-1 paper surveyed. A
  checklist-style citation for §"Threats to validity", where the thesis already does most of what
  this paper asks for and can say so against a named standard.
- **Li, Pons, Petit, Pons and Sahuquillo, "TailBench++"** — VERIFIED. *Journal of Cloud
  Computing* 15(1), 2026, DOI 10.1186/s13677-026-00908-3. Extends TailBench with dynamic client
  arrival, fluctuating QPS and multi-server topologies. Its validation protocol — thirteen repeats
  per QPS point with 95% confidence intervals *on the 95th and 99th percentiles* — is a published
  precedent for what the thesis's campaign already does with bootstrap intervals.

### 7.2 The exact procedure, measured — VERIFIED

**Michaelides, Lapawa, Eguiguren Chavez and Henze, "Evaluation of Security-Induced Latency on 5G
RAN Interfaces and User Plane Communication".** WiSec '26 (19th ACM Conference on Security and
Privacy in Wireless and Mobile Networks), pp. 176–181, 2026. DOI 10.1145/3765613.3797453.

**This measures the CU-CP-to-DU UE Context Setup procedure over F1-C, repeated 1,000 times, on a
disaggregated OAI testbed.** That is the procedure class the UECM service implements. Nothing
else found in this sweep comes so directly to the point.

The reported figures: IPsec adds roughly 120 µs on average to UE context setup over F1-C (as low
as ~40 µs for AES256-HMAC) against roughly 430 µs for DTLS; over E1, roughly 80 µs against
~300 µs for DTLS. The implication is that these context-setup procedures sit in a sub-millisecond
regime where hundreds of microseconds is material.

**Why this is worth real space in the thesis.** §"Tail latency and predictability in RAN"
currently motivates the latency budget from specification targets. This anchors it in a published
measurement of the same procedure on real software, which is a much stronger footing. It also
gives an external reference point for the thesis's own end-to-end numbers, and — usefully for
§"Threats to validity" — it demonstrates that effects of a few tens of microseconds are treated as
significant by others working on this procedure.

### 7.3 Overload as a first-class condition, not an edge case

Both VERIFIED. These justify the thesis's decision to drive the system past saturation, which is
currently argued from first principles.

- **Nguyen, El Malki, Rebecchi, Knopp and Önen, "Beyond Static Thresholds: Adaptive RRC Signaling
  Storm Detection with Extreme Value Theory".** IEEE MSWiM 2025, pp. 360–368,
  DOI 10.1109/MSWiM67937.2025.11309091. Doubly useful: it characterises the overload regime, and
  extreme value theory is a statistically defensible tool for reasoning about p99.99 that the
  thesis could borrow when the bare-metal campaign adds that percentile.
- **Giustini, Lacava, Bonati, Maxenti, Polese, Melodia and Cuomo, "StormShield: Fingerprint-Based
  Detection and Mitigation of RRC Signaling Storms in O-RAN 5G RANs".** WiSec '26, pp. 194–204,
  DOI 10.1145/3765613.3811685. Same group as §4.4 and as the already-cited `polese2023oran`.

### 7.4 A published baseline for control-plane procedure performance — VERIFIED

**Mukute, Mamushiane, Lysko, Modroiu, Magedanz and Mwangama, "Control Plane Performance
Benchmarking and Feature Analysis of Popular Open-Source 5G Core Networks".** *IEEE Access* 12,
pp. 113336–113360, 2024. DOI 10.1109/ACCESS.2024.3441725.

Journal-length benchmarking of registration and session-management procedure latency and
throughput across OpenAirInterface, Open5GS and free5GC. Useful mainly as a sanity check: it gives
an order of magnitude for control-plane procedure performance in comparable software, against
which the UECM numbers can be shown to be plausible.

### 7.5 Why sharding and run-to-completion help the tail

The thesis picks thread-per-shard for fairness reasons — it is the model both implementations can
express identically. These sources supply the independent performance justification, which is
currently missing.

- **Liao et al., "Towards Optimal Rack-scale μs-level CPU Scheduling through In-Network Workload
  Shaping" (Pallas)** — VERIFIED (DBLP; USENIX page live). USENIX ATC '25, pp. 179–198. No DOI.
  <https://www.usenix.org/conference/atc25/presentation/liao>. Partitions work into shards
  *homogeneous in CPU demand*, on the grounds that an M/G/K problem decomposes into M/D/K′
  subproblems where FCFS is tail-optimal. Reduces tail latency by 8.5× at medium load and up to
  two orders of magnitude at high load. **This is the sharpest available statement of why sharding
  helps the tail** — service-time homogeneity within a shard, not merely cache locality — and it
  is a better justification for the thesis's design than the one currently given.
- **Jia et al., "Aquifer: Transparent Microsecond-Scale Scheduling for vRAN Workloads"** —
  VERIFIED. *IEEE Transactions on Services Computing* 17(6), pp. 3171–3184, 2024,
  DOI 10.1109/TSC.2024.3440032. Argues that preserving **run-to-completion** task processing is
  critical for vRAN latency and stability, and reclaims otherwise-wasted CPU only at task
  boundaries. The strongest published justification for the thesis's design *in a RAN context*.
- **Jia, Tian, You, Chen and Chen, "Skyloft: A General High-Efficient Scheduling Framework in User
  Space"** — VERIFIED. SOSP '24, pp. 265–279, DOI 10.1145/3694715.3695973. Quantifies how much
  tail latency comes from lack of preemption rather than from the sharding model. Relevant as a
  confound to name: both implementations here inherit the same OS scheduling behaviour, which is
  part of why the comparison is fair.
- **Iyer, Unal, Kogias and Candea, "Achieving Microsecond-Scale Tail Latency Efficiently with
  Approximate Optimal Scheduling" (Concord)** — VERIFIED. SOSP '23, pp. 466–481,
  DOI 10.1145/3600006.3613136. With Skyloft, establishes the modern consensus that head-of-line
  blocking rather than synchronisation overhead dominates the tail at microsecond scale.
- **Enberg, Rao and Tarkoma, "I/O Is Faster Than the CPU"** — VERIFIED. HotOS XVII, 2019,
  pp. 81–87, DOI 10.1145/3317550.3321426. The position-paper companion to the already-cited
  `enberg2019threadpercore`, from the same University of Helsinki group. Cheap to add and gives
  the architectural rationale behind a measurement the thesis already leans on.

### 7.6 Independent corroboration of the thesis's most surprising result — VERIFIED

**Zhou, Leis, Yu and Stonebraker, "OLTP Through the Looking Glass 16 Years Later: Communication is
the New Bottleneck".** CIDR 2025. (DBLP-confirmed; the vldb.org PDF blocks automated fetches, so
retrieve it manually.)

Revisits the classic Harizopoulos OLTP breakdown using VoltDB — a canonical shared-nothing system
with one partition and one worker thread per core, which is structurally the thesis's own design.
The finding: now that transaction execution itself is heavily optimised, **communication
dominates**. Process isolation with shared memory and polling still costs 31–66% more than no
isolation; socket IPC costs more again; virtualisation adds an order of magnitude.

**This is the best external support in the whole sweep for the thesis's §7.5.2 result** — that the
operation itself accounts for 0.04% of end-to-end cost and the cross-thread submit-and-complete
handoff accounts for essentially all of it. That number currently reads as an oddity specific to
this measurement. Zhou et al. say the same thing about a different mature shared-nothing system,
from a different research community, which converts it from an anomaly into an instance of a known
pattern. It also directly frames the RQ4 seam measurement, since the FFI boundary is another
communication cost of exactly this kind.

### 7.7 The mechanism behind async tail divergence

- **Xie, Jin and Vasilakis, "Towards Hybrid Cooperative-Preemptive Scheduling"** — VERIFIED.
  PLOS '25 (13th Workshop on Programming Languages and Operating Systems, co-located with SOSP),
  pp. 68–75, DOI 10.1145/3764860.3768329. Names Tokio explicitly and catalogues the failure modes
  of cooperative scheduling: a single task monopolising a worker, head-of-line blocking, resource
  exhaustion. The cleanest peer-reviewed statement of *why* a cooperatively scheduled async Rust
  runtime can show a worse p99 than a fiber-based or preemptive C++ implementation.
- **Teper, Kuhse, Günzel, von der Brüggen, Howar and Chen, "Thread Carefully: Preventing
  Starvation in the ROS 2 Multithreaded Executor"** — VERIFIED. *IEEE TCAD* 43(11),
  pp. 3588–3599, 2024, DOI 10.1109/TCAD.2024.3446865. Shows the C++ ROS 2 multi-threaded executor
  is *not* starvation-free. Keeps the argument honest: "the C++ side is thread-based, therefore
  predictable" is not automatically true, so a Rust p99 regression still needs attributing to a
  named mechanism rather than to the language.

### 7.8 Already cited — do not double-add

**Li, Huang, Narayanan and Burtsev, PLOS '21** surfaced again as a top recommendation. It is
already in the bibliography as `li2021ipc`. One detail from it may not be used in the thesis yet
and is worth checking: they report that a carefully performance-planned Rust implementation runs
**within 4–8% of unsafe C++** on a matched two-language design. That is a published prior
expectation the thesis's own overhead results can be compared against.

### 7.9 What is *not* there

Negative results, recorded so they are not searched for again:

- **No peer-reviewed paper from 2024–2026 uses the term "coordinated omission".** The 2017 BTW
  paper in §7.1 remains the only peer-reviewed source that names it. This is why the
  recommendation is to cite the root cause (open versus closed) rather than to hunt for a modern
  paper on the phenomenon.
- **Pekka Enberg has no doctoral dissertation on thread-per-core.** His publication list shows the
  ANCS 2019 paper already cited, the HotOS 2019 paper in §7.5, and a workshop paper. He has since
  written a trade book, *Latency* (Manning), which is not peer-reviewed — though given that he is
  a Helsinki PhD candidate and this is a Helsinki thesis, it may be worth a supporting mention.
- **No academic measurement study of Glommio or Monoio exists.** Evidence for those runtimes is
  engineering-grade only. Notably, Monoio's own benchmark documentation concedes it is *slower*
  than Tokio at low connection counts, and that "if the workload is very unbalanced, it may cause
  performance degradation than Tokio since CPU cores may not be fully utilized" — which is the
  load-imbalance weakness of thread-per-core stated by its own implementers. Usable as an
  engineering citation if clearly marked as such, but not as evidence.
- **The substantive critiques of thread-per-core are not academic.** The best are blog essays
  (withoutboats, "Thread-per-core"; and a companion piece on skew at rising core counts) arguing
  that a key-value store is the best possible case for partitioning and that applications needing
  atomic mutation across partitions pay real correctness costs. Honest and relevant, but cite them
  as engineering commentary if at all — the peer-reviewed version of the load-imbalance argument
  is in Pallas (§7.5).

**Flagged as unverified, do not cite without checking:** two ICPE 2026 preprints on
variability-guided optimisation and on declarative benchmark harnesses (author lists and final
metadata unconfirmed); a 2025 arXiv preprint on Open RAN disaggregation latency (no peer-reviewed
venue confirmed, and its quoted O-RAN budget figures of 1.5–10 ms DU-to-CU and 250 µs fronthaul
are second-hand — cite the O-RAN or 3GPP document directly if that budget is load-bearing); and
the 2020 IEEE S&P magazine version of the benchmarking-flaws paper.

---

## 8. Sources found and rejected

Recorded so the same search does not surface them again. All appeared prominently for the
obvious query "Rust vs C++ performance 2026".

| Source | Why not |
| --- | --- |
| JetBrains RustRover blog, "Rust VS C++ Comparison for 2026" | Vendor marketing; no method |
| Medium, "Rust vs C++ in 2026: we rewrote our core engine…" | Anonymous, unverifiable, no method |
| Boardor, "Practical Showdown … HFT Engines" | Blog; p99 numbers with no reproducible setup |
| reintech.io, "Rust vs C++ Performance Comparison 2026" | SEO content |
| theeditorial.news, "C++26 vs Carbon vs Rust" | Unattributed benchmark claims |
| ResearchGate, "A Comparative Study of C++ and Rust…" | No identifiable venue or peer review |
| LinkedIn profiles indicating Rust roles at Ericsson | Not a citable source |

Worth noting for the discussion: several of these blogs independently claim *better* p99 latency
for Rust after a rewrite, attributing it to reduced shared mutable state and allocation rather
than to code generation. That is an interesting hypothesis and it aligns with the thesis's own
allocation findings — but it is not evidence, and it must not be cited. If the thesis wants to
make that argument it has to come from the measured data.

Also searched without result: no peer-reviewed study of Rust adoption at Ericsson or Nokia beyond
the two master's theses already cited. If a Nokia-internal data point is available through the
supervisors, it has no published equivalent and would be a genuine contribution.

---

## 9. Verification status

Metadata confirmation is **complete**. Every item was checked against a primary source:
arXiv abstract pages for the preprints, Crossref publisher-deposited records for the ACM and
Elsevier DOIs, DataCite for the LIPIcs DOI, the CVE Program record for the two CVEs, EUR-Lex for
the regulation, and open-std.org / isocpp.org for the WG21 papers.

Two corrections came out of it, both worth noting because the preprint would have been the wrong
thing to cite:

- The async Rust paper (§4.5) is **published at ECRTS 2025**, not a preprint.
- The dApps paper (§4.4) is **published in *Computer Networks***, not a preprint.

Three items remain short of full verification and are marked in place: the Rust Foundation interop
document (§6.1, citable form), SACTOR (§6.2, author list and pages), and the C++29 deferral claim
(§2.4, which the thesis does not need — the weaker statement is already supported).

The second search pass (§7) is also complete. Its DOIs were checked against Crossref, and the
three sources without DOIs — the NSDI, USENIX ATC and CIDR papers — were confirmed against DBLP
and their publisher pages. Items it could not verify are listed at the end of §7.9 and must not be
cited as they stand.

**No search work is outstanding.** What remains is editorial: deciding which of these to use, and
writing them in.

## 10. Suggested order of work

1. Write the C++ profiles paragraph (§2). Largest gap, and everything needed is verified.
2. Add Škoudlil et al. to the Arvidsson discussion (§4.5), with the cooperative-scheduling paper
   from §7.7 alongside it. Small edit, and it turns the thesis's central rebuttal from an
   assertion into a cited one.
3. Anchor the latency budget on Michaelides et al. (§7.2) and the 0.04% handoff result on Zhou et
   al. (§7.6). Both are single-sentence additions that make existing results land harder.
4. Promote Schroeder et al. (§7.1) to the primary coordinated-omission citation, keeping Tene as
   support. Methodology chapters get read closely; a talk is a weak place to rest this.
5. Swap in the 2025 Android data and Watson et al. (§3.1, §3.2). Two citation updates, immediate
   improvement, low risk.
6. Add the EU CRA sentence to the motivation (§3.4).
7. Add the Alsoran acknowledgement (§4.1). Short, and better volunteered than extracted.
8. Then decide on the optional enrichment: RQ2 and RQ4 additions (§5, §6), and the design
   justification for sharding from Pallas and Aquifer (§7.5).

Items 1–7 are worth doing regardless. Item 8 is a judgement call about how much related work a
master's thesis needs, and §"Related work" is already dense.

There is one thing here that is not a citation and is worth acting on separately: the extreme
value theory approach in §7.3 is a defensible way to reason about p99.99 from a finite sample.
`TODO.md` lists p99.99 and a jitter statistic as harness gaps to close *before* the bare-metal
campaign, so if that appeals it should be decided now rather than after the data is collected.

---

## 11. BibTeX

Ready to paste into `bibliography.bib`. Every field below was read from a primary source. The
`@misc` entries need `urldate` set to the day they are actually cited.

```bibtex
@article{watson2025memorysafety,
  author  = {Watson, Robert N. M. and Baldwin, John and Chen, Tony and Chisnall, David and
             Clarke, Jessica and Davis, Brooks and Filardo, Nathaniel Wesley and Gutstein, Brett
             and Jenkinson, Graeme and Kern, Christoph and Laurie, Ben and Mazzinghi, Alfredo and
             Moore, Simon W. and Neumann, Peter G. and Okhravi, Hamed and Rebert, Alex and
             Richardson, Alex and Sewell, Peter and Tratt, Laurence and
             Vijayaraghavan, Muralidaran and Vincent, Hugo and Witaszczyk, Konrad},
  title   = {It Is Time to Standardize Principles and Practices for Software Memory Safety},
  journal = {Communications of the ACM},
  volume  = {68},
  number  = {2},
  pages   = {40--45},
  year    = {2025},
  doi     = {10.1145/3708553}
}

@misc{vanderstoep2025android,
  author       = {Vander Stoep, Jeff},
  title        = {{Rust} in {Android}: Move Fast and Fix Things},
  howpublished = {Google Security Blog},
  year         = {2025},
  month        = nov,
  url          = {https://blog.google/security/rust-in-android-move-fast-fix-things/}
}

@techreport{nsacisa2025msl,
  author      = {{National Security Agency} and
                 {Cybersecurity and Infrastructure Security Agency}},
  title       = {Memory Safe Languages: Reducing Vulnerabilities in Modern Software Development},
  type        = {Cybersecurity Information Sheet},
  year        = {2025},
  month       = jun,
  url         = {https://www.cisa.gov/resources-tools/resources/memory-safe-languages-reducing-vulnerabilities-modern-software-development}
}

@misc{eu2024cra,
  author       = {{European Parliament and Council of the European Union}},
  title        = {Regulation ({EU}) 2024/2847 of 23 October 2024 on horizontal cybersecurity
                  requirements for products with digital elements and amending Regulations ({EU})
                  No 168/2013 and ({EU}) 2019/1020 and Directive ({EU}) 2020/1828
                  ({Cyber} {Resilience} {Act})},
  howpublished = {Official Journal of the European Union, OJ L, 2024/2847},
  year         = {2024},
  month        = nov,
  url          = {https://eur-lex.europa.eu/eli/reg/2024/2847/oj}
}

@misc{sutter2025profiles,
  author       = {Sutter, Herb},
  title        = {Core Safety Profiles for {C++26}},
  howpublished = {ISO/IEC JTC1/SC22/WG21 document P3081R2},
  year         = {2025},
  month        = feb,
  url          = {https://isocpp.org/files/papers/P3081R2.pdf}
}

@misc{vandevoorde2026profiles,
  author       = {Vandevoorde, David and Garland, Jeff and McKenney, Paul E. and Orr, Roger and
                  Stroustrup, Bjarne and Wong, Michael},
  title        = {Profiles and Safety: A Call to Action},
  howpublished = {ISO/IEC JTC1/SC22/WG21 document P3970R0},
  year         = {2026},
  month        = jan,
  url          = {https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3970r0.pdf}
}

@misc{baxter2024safecpp,
  author       = {Baxter, Sean and Mazakas, Christian},
  title        = {Safe {C++}},
  howpublished = {ISO/IEC JTC1/SC22/WG21 document P3390R0},
  year         = {2024},
  month        = sep,
  url          = {https://safecpp.org/P3390R0.html}
}

@misc{stroustrup2025cpp21,
  author       = {Stroustrup, Bjarne},
  title        = {21st Century {C++}},
  howpublished = {Blog@CACM, Communications of the ACM},
  year         = {2025},
  month        = feb,
  url          = {https://cacm.acm.org/blogcacm/21st-century-c/}
}

@inproceedings{skoudlil2025asyncrust,
  author    = {{\v S}koudlil, Martin and Sojka, Michal and Hanz{\'a}lek, Zden{\v e}k},
  title     = {A First Look at {ROS} 2 Applications Written in Asynchronous {Rust}},
  booktitle = {37th Euromicro Conference on Real-Time Systems (ECRTS 2025)},
  series    = {Leibniz International Proceedings in Informatics (LIPIcs)},
  volume    = {335},
  pages     = {1:1--1:21},
  publisher = {Schloss Dagstuhl -- Leibniz-Zentrum f{\"u}r Informatik},
  year      = {2025},
  doi       = {10.4230/LIPIcs.ECRTS.2025.1}
}

@article{lacava2025dapps,
  author  = {Lacava, Andrea and Bonati, Leonardo and Mohamadi, Niloofar and Gangula, Rajeev and
             Kaltenberger, Florian and Johari, Pedram and D'Oro, Salvatore and Cuomo, Francesca
             and Polese, Michele and Melodia, Tommaso},
  title   = {{dApps}: Enabling Real-Time {AI}-Based {Open} {RAN} Control},
  journal = {Computer Networks},
  volume  = {269},
  pages   = {111342},
  year    = {2025},
  doi     = {10.1016/j.comnet.2025.111342}
}

@article{villani2025treeborrows,
  author  = {Villani, Neven and Hostert, Johannes and Dreyer, Derek and Jung, Ralf},
  title   = {Tree Borrows},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {9},
  number  = {PLDI},
  pages   = {1019--1042},
  year    = {2025},
  doi     = {10.1145/3735592}
}

@inproceedings{lattuada2024verus,
  author    = {Lattuada, Andrea and Hance, Travis and Bosamiya, Jay and Brun, Matthias and
               Cho, Chanhee and LeBlanc, Hayley and Srinivasan, Pranav and Achermann, Reto and
               Chajed, Tej and Hawblitzel, Chris and Howell, Jon and Lorch, Jacob R. and
               Padon, Oded and Parno, Bryan},
  title     = {Verus: A Practical Foundation for Systems Verification},
  booktitle = {Proceedings of the ACM SIGOPS 30th Symposium on Operating Systems Principles
               (SOSP '24)},
  pages     = {438--454},
  year      = {2024},
  doi       = {10.1145/3694715.3695952}
}

@article{hong2025c2rust,
  author  = {Hong, Jaemin and Ryu, Sukyoung},
  title   = {Automatically Translating {C} to {Rust}},
  journal = {Communications of the ACM},
  volume  = {68},
  number  = {11},
  pages   = {58--65},
  year    = {2025},
  doi     = {10.1145/3737696}
}

@misc{delmas2026kani,
  author       = {Delmas, R{\'e}mi and Hassan, Zyad and Hu, Qinheping and Kumar, Rahul and
                  Monteiro, Felipe R. and Nguyen, Thanh and Palacios, Adri{\'a}n and Val, Celina
                  and Tautschnig, Michael and Adam, Justus and Schwartz-Narbonne, Daniel and
                  Zech, Carolyn},
  title        = {Kani: A Model Checker for {Rust}},
  howpublished = {arXiv:2607.01504 [cs.SE]. Accepted at the ASE 2026 Industry Showcase Track},
  year         = {2026},
  url          = {https://arxiv.org/abs/2607.01504}
}

@misc{leblanc2024verification,
  author       = {Le Blanc, Alex and Lam, Patrick},
  title        = {Surveying the {Rust} Verification Landscape},
  howpublished = {arXiv:2410.01981 [cs.PL]},
  year         = {2024},
  url          = {https://arxiv.org/abs/2410.01981}
}

@misc{alsoran,
  author       = {Larkin, Nic},
  title        = {Alsoran: A {5G} {gNodeB} Centralized Unit Written in {Rust}},
  howpublished = {Open-source software repository},
  url          = {https://github.com/nplrkn/alsoran}
}

@misc{cve202623194,
  author       = {{Linux Kernel CNA}},
  title        = {{CVE-2026-23194}: rust\_binder: Correctly Handle {FDA} Objects of Length Zero},
  howpublished = {CVE Program record},
  year         = {2026},
  month        = feb,
  url          = {https://nvd.nist.gov/vuln/detail/CVE-2026-23194}
}

@misc{cve202664467,
  author       = {{Linux Kernel CNA}},
  title        = {{CVE-2026-64467}: rust\_binder: Use a u64 Stride When Cleaning Up the Offsets
                  Array},
  howpublished = {CVE Program record},
  year         = {2026},
  month        = jul,
  url          = {https://nvd.nist.gov/vuln/detail/CVE-2026-64467}
}

@inproceedings{schroeder2006openclosed,
  author    = {Schroeder, Bianca and Wierman, Adam and Harchol-Balter, Mor},
  title     = {Open Versus Closed: A Cautionary Tale},
  booktitle = {Proceedings of the 3rd USENIX Symposium on Networked Systems Design and
               Implementation (NSDI '06)},
  year      = {2006},
  url       = {https://www.usenix.org/conference/nsdi-06/open-versus-closed-cautionary-tale}
}

@inproceedings{friedrich2017coordinated,
  author    = {Friedrich, Steffen and Wingerath, Wolfram and Ritter, Norbert},
  title     = {Coordinated Omission in {NoSQL} Database Benchmarking},
  booktitle = {Datenbanksysteme f{\"u}r Business, Technologie und Web (BTW 2017), Workshopband},
  publisher = {Gesellschaft f{\"u}r Informatik},
  year      = {2017},
  url       = {https://dl.gi.de/handle/20.500.12116/918}
}

@inproceedings{vanderkouwe2019benchmarking,
  author    = {van der Kouwe, Erik and Heiser, Gernot and Andriesse, Dennis and Bos, Herbert and
               Giuffrida, Cristiano},
  title     = {{SoK}: Benchmarking Flaws in Systems Security},
  booktitle = {2019 IEEE European Symposium on Security and Privacy (EuroS\&P)},
  pages     = {310--325},
  year      = {2019},
  doi       = {10.1109/EuroSP.2019.00031}
}

@article{li2026tailbench,
  author  = {Li, Zhilin and Pons, Lucia and Petit, Salvador and Pons, Julio and
             Sahuquillo, Julio},
  title   = {{TailBench++}: Flexible Multi-Client, Multi-Server Benchmarking for
             Latency-Critical Workloads},
  journal = {Journal of Cloud Computing},
  volume  = {15},
  number  = {1},
  year    = {2026},
  doi     = {10.1186/s13677-026-00908-3}
}

@inproceedings{michaelides2026ranlatency,
  author    = {Michaelides, Sotiris and Lapawa, Jakub and Eguiguren Chavez, Daniel and
               Henze, Martin},
  title     = {Evaluation of Security-Induced Latency on {5G} {RAN} Interfaces and User Plane
               Communication},
  booktitle = {Proceedings of the 19th ACM Conference on Security and Privacy in Wireless and
               Mobile Networks (WiSec '26)},
  pages     = {176--181},
  year      = {2026},
  doi       = {10.1145/3765613.3797453}
}

@inproceedings{nguyen2025rrcevt,
  author    = {Nguyen, Dang Kien and El Malki, Rim and Rebecchi, Filippo and Knopp, Raymond and
               {\"O}nen, Melek},
  title     = {Beyond Static Thresholds: Adaptive {RRC} Signaling Storm Detection with Extreme
               Value Theory},
  booktitle = {2025 International Conference on Modeling, Analysis and Simulation of Wireless and
               Mobile Systems (MSWiM)},
  pages     = {360--368},
  year      = {2025},
  doi       = {10.1109/MSWiM67937.2025.11309091}
}

@inproceedings{giustini2026stormshield,
  author    = {Giustini, Noemi and Lacava, Andrea and Bonati, Leonardo and Maxenti, Stefano and
               Polese, Michele and Melodia, Tommaso and Cuomo, Francesca},
  title     = {{StormShield}: Fingerprint-Based Detection and Mitigation of {RRC} Signaling Storms
               in {O-RAN} {5G} {RANs}},
  booktitle = {Proceedings of the 19th ACM Conference on Security and Privacy in Wireless and
               Mobile Networks (WiSec '26)},
  pages     = {194--204},
  year      = {2026},
  doi       = {10.1145/3765613.3811685}
}

@article{mukute20245gcore,
  author  = {Mukute, Tariro and Mamushiane, Lusani and Lysko, Albert A. and
             Modroiu, Elena-Ramona and Magedanz, Thomas and Mwangama, Joyce},
  title   = {Control Plane Performance Benchmarking and Feature Analysis of Popular Open-Source
             {5G} Core Networks: {OpenAirInterface}, {Open5GS}, and {free5GC}},
  journal = {IEEE Access},
  volume  = {12},
  pages   = {113336--113360},
  year    = {2024},
  doi     = {10.1109/ACCESS.2024.3441725}
}

@article{jia2024aquifer,
  author  = {Jia, Yunshan and Zhong, Yinmin and Wang, Meng and Gao, Jiaqi and Zhang, Pengyu and
             Liu, Xuanzhe and Jin, Xin},
  title   = {Aquifer: Transparent Microsecond-Scale Scheduling for {vRAN} Workloads},
  journal = {IEEE Transactions on Services Computing},
  volume  = {17},
  number  = {6},
  pages   = {3171--3184},
  year    = {2024},
  doi     = {10.1109/TSC.2024.3440032}
}

@inproceedings{liao2025pallas,
  author    = {Liao, Xudong and Tian, Han and Wan, Xinchen and Zeng, Chaoliang and Wang, Hao and
               Zhang, Junxue and Ma, Mengyu and Liu, Guyue and Chen, Kai},
  title     = {Towards Optimal Rack-Scale $\mu$s-Level {CPU} Scheduling through In-Network
               Workload Shaping},
  booktitle = {Proceedings of the 2025 USENIX Annual Technical Conference (USENIX ATC '25)},
  pages     = {179--198},
  year      = {2025},
  url       = {https://www.usenix.org/conference/atc25/presentation/liao}
}

@inproceedings{jia2024skyloft,
  author    = {Jia, Yuekai and Tian, Kaifu and You, Yuyang and Chen, Yu and Chen, Kang},
  title     = {Skyloft: A General High-Efficient Scheduling Framework in User Space},
  booktitle = {Proceedings of the ACM SIGOPS 30th Symposium on Operating Systems Principles
               (SOSP '24)},
  pages     = {265--279},
  year      = {2024},
  doi       = {10.1145/3694715.3695973}
}

@inproceedings{iyer2023concord,
  author    = {Iyer, Rishabh and Unal, Musa and Kogias, Marios and Candea, George},
  title     = {Achieving Microsecond-Scale Tail Latency Efficiently with Approximate Optimal
               Scheduling},
  booktitle = {Proceedings of the 29th Symposium on Operating Systems Principles (SOSP '23)},
  pages     = {466--481},
  year      = {2023},
  doi       = {10.1145/3600006.3613136}
}

@inproceedings{enberg2019iofaster,
  author    = {Enberg, Pekka and Rao, Ashwin and Tarkoma, Sasu},
  title     = {{I/O} Is Faster Than the {CPU}: Let's Partition Resources and Eliminate (Most)
               {OS} Abstractions},
  booktitle = {Proceedings of the Workshop on Hot Topics in Operating Systems (HotOS XVII)},
  pages     = {81--87},
  year      = {2019},
  doi       = {10.1145/3317550.3321426}
}

@inproceedings{zhou2025oltp,
  author    = {Zhou, Xinjing and Leis, Viktor and Yu, Xiangyao and Stonebraker, Michael},
  title     = {{OLTP} Through the Looking Glass 16 Years Later: Communication Is the New
               Bottleneck},
  booktitle = {15th Annual Conference on Innovative Data Systems Research (CIDR 2025)},
  year      = {2025},
  url       = {https://www.vldb.org/cidrdb/papers/2025/p17-zhou.pdf}
}

@inproceedings{xie2025cooperative,
  author    = {Xie, Yizheng and Jin, Di and Vasilakis, Nikos},
  title     = {Towards Hybrid Cooperative-Preemptive Scheduling},
  booktitle = {Proceedings of the 13th Workshop on Programming Languages and Operating Systems
               (PLOS '25)},
  pages     = {68--75},
  year      = {2025},
  doi       = {10.1145/3764860.3768329}
}

@article{teper2024starvation,
  author  = {Teper, Harun and Kuhse, Daniel and G{\"u}nzel, Mario and von der Br{\"u}ggen, Georg
             and Howar, Falk and Chen, Jian-Jia},
  title   = {Thread Carefully: Preventing Starvation in the {ROS} 2 Multithreaded Executor},
  journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  volume  = {43},
  number  = {11},
  pages   = {3588--3599},
  year    = {2024},
  doi     = {10.1109/TCAD.2024.3446865}
}
```

Two notes on style. The existing bibliography uses `IEEEtran`, which renders `@misc` entries
without the emphasis that `@techreport` gets — check how the WG21 and CVE entries look in the
compiled PDF before committing to the entry types. And the thesis cites 3GPP specifications as
`@techreport`, so `nsacisa2025msl` follows that pattern for consistency.
