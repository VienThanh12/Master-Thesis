# Literature sweep, August 2026

Candidate sources for `Ha_Vien_Mastersthesis_2026.tex`, found by searching for work published after the current
bibliography was assembled.

> **Status, 10 August 2026.** The core set (§10, items 1–7) has been **applied**: eleven entries
> added to `bibliography.bib` and the accompanying prose written into `Ha_Vien_Mastersthesis_2026.tex`. The build is
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

**Why this matters.** §"C++ for latency-critical systems" (Ha_Vien_Mastersthesis_2026.tex:645–680) says safety in
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

- **§"C++ for latency-critical systems" (Ha_Vien_Mastersthesis_2026.tex:645–680)**, as a new paragraph after the
  tooling paragraph at line 672. Roughly: the committee is addressing this, here is the shape of
  it, here is why the comparison in this thesis is against C++23 as deployed, and here is why the
  concurrency half of RQ2 is unaffected either way.
- **§"Threats to validity" (Ha_Vien_Mastersthesis_2026.tex:3586)**, under external validity. There is currently no
  row for "the object of comparison is itself moving". It belongs in `tab:threats` as a
  construct- or external-validity row: control is that the comparison is pinned to a named
  standard and compiler version; residual is that a future C++ closes part of the gap.
- **Conclusion / future work (Ha_Vien_Mastersthesis_2026.tex:3774)**, as a natural re-run condition: repeat the RQ2
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

**Where it goes:** update the sentence at Ha_Vien_Mastersthesis_2026.tex:667–668 that currently cites
`google2022android`; §"Discussion on the research questions" for RQ4; and the engineering
guidelines section (Ha_Vien_Mastersthesis_2026.tex:3300).

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
available for the claim. Straight upgrade for the citation cluster at Ha_Vien_Mastersthesis_2026.tex:3425–3429 and
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

**Where it goes:** §"Motivation and industrial context" (Ha_Vien_Mastersthesis_2026.tex:291), alongside the existing
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
§"Tail latency and predictability in RAN" (Ha_Vien_Mastersthesis_2026.tex:1088) currently has no external anchor of
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

**Where it goes:** §"Related work" (Ha_Vien_Mastersthesis_2026.tex:3506–3520), in the passage on Arvidsson and Kaller;
and §"Concurrency models for control-plane software" (Ha_Vien_Mastersthesis_2026.tex:801) where the choice not to use
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
`cxx` — already mentioned at Ha_Vien_Mastersthesis_2026.tex:844 — as "restrictive and opinionated" by its own
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

The thesis already handles coordinated omission correctly (Ha_Vien_Mastersthesis_2026.tex:629, 638, 3693), but the
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

---

# Third sweep, 17 August 2026 — the research gap re-audited

> **Status: applied, same day.** Everything in §D below is done. Fourteen entries added to
> `bibliography.bib` (98 active entries, all cited, no orphans); `Thesis_Plan_v2.tex` §2 rewritten;
> the three `Thesis_v2.tex` bullets corrected; `Ha_Vien_Mastersthesis_2026.tex` §`sec:gap`, the search protocol,
> §`sec:relatedwork`, `tab:related`, the peak-RSS discussion, the skill-asymmetry threat and the
> future-work list updated; `29_research_gap` rebuilt with five columns and six rows; the deck
> slide-6 subtitle corrected. All three PDFs rebuild with zero errors, zero undefined references
> and zero overfull boxes. `li2024rustforlinux` is commented out in favour of the TOCS version.
> One defect was found and fixed in passing: `tab:related` had grown taller than the page and was
> **silently dropping its last three rows**, including this thesis's own; the column widths were
> rebalanced so the whole table renders.
>
> **Second pass, same day.** A head-to-head comparison against the five theses was added as
> `tab:vendortheses` (object measured, regime reported, each study's own verdict, with this thesis
> as the last row), together with the single-vendor external-validity argument and the Nokia-side
> publication check in §E. `gjomemo2016mesc` is the fourteenth entry. The two tables now
> cross-reference each other in their captions so the overlap reads as a division of labour rather
> than repetition: `tab:vendortheses` carries the substance, `tab:related` the three gap axes.
>
> What is *not* done, and is the one thing left: **read Emberg & Wadsten and Olsson & Stenström in
> full.** The prose now makes absence claims about them (no tail under overload, no concurrency
> model held fixed) that were checked against abstracts only.

The first two sweeps looked for sources that improve the argument. This one attacks it. The gap
statement in `Thesis_Plan_v2.tex` §2 and `Ha_Vien_Mastersthesis_2026.tex` §`sec:gap` rests on two Ericsson
master's theses plus an unqualified negative claim (*"Neither isolates the language"*, *"The gap
is therefore…"*). The question asked here was the adversarial one: **is that still true in
August 2026, and is "two theses" the right count?**

Short answer: the gap survives, the count does not. There are **five** Ericsson-hosted Nordic
theses in this space, not two, and one of them already builds a matched C++/Rust pair across an
FFI seam and compares it statistically. The differentiator has to move from *"nobody builds a
matched pair"* to *"nobody does it for a stateful concurrent subsystem, past saturation, with a
two-sided defect boundary"* — which is what this thesis actually does, so the correction costs
nothing and removes a claim an examiner could break in one search.

## A. Method, and a warning about it

Queried programmatically: Crossref, OpenAlex, Semantic Scholar, arXiv, DBLP, **DiVA** (Swedish
university repositories) and **Finna** (all Finnish repositories). Query strings covered the
three axes the gap claims — matched-pair control, tail behaviour past saturation, measured
adoption cost — plus the domain and the async-runtime confound.

Two lessons worth keeping, because they change how this search must be run:

1. **Free-text "Rust" queries are unusable in the general indexes.** Crossref and OpenAlex
   relevance-rank wheat rust, iron rust and rust-resistance genomics above the programming
   language. Only DBLP (computer science only) and OpenAlex with
   `title_and_abstract.search` restricted queries return usable result sets. A search protocol
   that says "Google Scholar and ACM DL" will silently under-report here.
2. **The closest prior work is invisible to every citation index.** Neither `karlback2021ran`
   nor `arvidsson2025async` appears in Crossref, OpenAlex, DBLP or Semantic Scholar. Forward or
   backward citation chaining from them is therefore impossible, and no amount of database
   searching finds them or their siblings. They are only reachable through **repository**
   search. The thesis's documented search protocol (`Ha_Vien_Mastersthesis_2026.tex`:1339–1351) names four
   indexed databases and citation chaining; it should also name DiVA and Finna, or it does not
   describe the search that actually found the closest work.

## B. The main finding: the neighbouring work is a cluster of five, not a pair

All metadata below was read from the DiVA repository record (CSV export of the primary record),
and every URN was resolved through `urn.kb.se` on 17 August 2026. **VERIFIED** as grey
literature — that is, the record is confirmed; peer review is absent by definition and must be
stated wherever they are cited.

⚠ **Abstracts were read in full; the theses themselves were not.** Every finding attributed below
comes from the author's own abstract. Before any of this reaches thesis prose, read at least
Emberg & Wadsten and Olsson & Stenström end to end: the claims that matter — that neither reports
tail behaviour past saturation, and what concurrency model each holds — are absence claims that an
abstract cannot settle.

| Thesis | Level, year | Host | What it does | Result |
| --- | --- | --- | --- | --- |
| Karlbäck & Orö (`karlback2021ran`) | MSc 2021, LiU | Ericsson | C++/Rust/Go, RAN apps, idiomatic-per-language by design | C++ preferred where performance critical; **Rust lowest peak RSS** |
| Olsson, V. (`olsson2023ranmgmt`) | MSc 2023, KTH | Ericsson AB | Rust vs **C** for RAN **node management** software | Execution speed "on par or better"; **peak memory generally higher in Rust**; safety materially better |
| Olsson, J. & Stenström (`olsson2023asyncpackets`) | MSc 2023, LiU | Ericsson | Rust async (**Glommio, thread-per-core**) vs DPDK Eventdev C apps | Rust throughput **20–50%** of DPDK, "latency far worse"; concludes async Rust "currently not a viable approach" |
| Emberg & Wadsten (`emberg2023asn1`) | MSc 2023, LiU | Ericsson (Linköping) | **Matched C++ and Rust ASN.1 decompilers**, both calling third-party C++ (in Rust via a C wrapper), Mann–Whitney comparison + developer interviews | Session 1: comparable. Session 2 (after further optimisation): **Rust worse by 85–91%**. Concludes Rust likely more resource-efficient *in practice* |
| Arvidsson & Kaller (`arvidsson2025async`) | MSc 2025, LiU | Ericsson | Five async frameworks, 5G control-plane procedures, median + p99 | Boost.Fibers fastest at every load; Rust p99 rises more steeply past a threshold rate |

Two further non-vendor theses from 2026 land on the thesis's own methods:

| Thesis | Level, year | What it does | Why it matters here |
| --- | --- | --- | --- |
| Sundvisson & Hofer (`sundvisson2026drivers`) | BSc 2026, BTH | Two **functionally equivalent** C and Rust user-space BME280 drivers; 48 h stress, Valgrind, `unsafe` audit, LD_PRELOAD fault injection, 12 h AFL++, sequential probability ratio testing | C **0.178%** faster — "detectable at 99% confidence but well within a ±1% equivalence zone"; Rust **+29% memory**; five small `unsafe` blocks at syscalls |
| Andersson (`andersson2026stdmemsafety`) | BSc 2026, LiU | Reproduces CWE classes in C++/Rust/Python to establish **the stage at which each fault is detected** (compile-time / runtime / silent) | Same framing as RQ2, minus concurrency, minus the boundary classes, minus a domain |

### What each of the three new ones does to the argument

**Emberg & Wadsten is the one that bites.** It is the closest prior work *by method* and it is
uncited. It builds one component twice in C++ and Rust, routes the Rust side through a C
wrapper to reach third-party C++ — an FFI seam, i.e. RQ4's object — and compares the two
statistically. The sentence "Neither isolates the language" is safe only because it is scoped to
the other two theses; as a claim about the literature it is now false. What Emberg & Wadsten do
*not* have is what should carry the gap instead: a stateful, concurrent subsystem, a fixed
concurrency model, a load sweep past saturation, tail percentiles under coordinated-omission
control, paired tests with family-wise correction, and a defect catalogue that spans the
boundary of the guarantee.

There is also a methodological gift in it. Their two benchmarking sessions **reversed the
verdict**: comparable performance after a normal code review, Rust 85–91% worse after both sides
were optimised further. That is precisely the single-author skill-asymmetry threat the plan names
and bounds with the frozen specification and the parity suite — currently asserted, and now
citable as something that has demonstrably happened in this exact domain.

**Olsson (KTH) resolves the peak-RSS disagreement in the thesis's favour.** §`sec:rqdiscussion`
defends the sign of the RSS result against Karlbäck & Orö, who found Rust *lowest*. A second
Ericsson RAN thesis, on a different subsystem, reports peak memory "generally higher in Rust".
That turns a one-against-one disagreement into two-against-one with a mechanism already
identified (Karlbäck's C++ runs on Boost.Fibers, one stack per fiber, so their figure measures
per-context runtime cost). Sundvisson & Hofer's +29% is a third instance, outside telecom.
Do not overstate this: none of the three isolates the allocator, which is the thesis's larger
effect.

**Olsson & Stenström is the third exhibit for the confound, and the strongest.** Rust async over
Glommio against DPDK Eventdev in C, in Ericsson's own packet-processing setting, reaching 20–50%
of DPDK throughput with "far worse" latency. Read carelessly this is a devastating result for
Rust; read correctly it is a comparison of Glommio against a kernel-bypass framework tuned for a
decade, in which the language is the least of the differences. It belongs in the gap section
because it makes the pattern unmistakable: **every** telecom-domain comparison to date varies the
runtime with the language, and the effect sizes it produces (20–50%, not 2–5%) show how much of
the measurement the runtime owns. It also documents that the thread-per-core-plus-async
combination has already been tried at Ericsson and failed on latency — which is a reason the
thesis's thread-per-shard-without-async design is the interesting control, and a strong item for
future work.

## C. Peer-reviewed additions, all metadata verified via Crossref

**VERIFIED** — publisher-deposited record read; abstracts read where quoted.

1. **Suchert & Castrillon, Bench 2022** (LNCS 13852:160–175, publ. 2023). Manually translated
   the **STAMP** transactional benchmark suite to Rust, plus a `c2rust`-transpiled version.
   Finding: "idiomatic implementations using safe Rust are generally slower than both C and
   transpiled code, they guarantee memory safety and improve code quality." A matched pair on a
   **concurrent** workload, contrary result, peer-reviewed. Better neighbour for `tab:related`
   than any of the general-purpose benchmark rows.
2. **Gonzalez, Mvondo & Bromberg, PLOS@SOSP 2023** (pp. 18–25). Rust UDP tunnelling driver in
   the Linux kernel against an equivalent C driver: latency **+0.1906%** (p = 1.464e-15),
   throughput **−0.00090%** (p = 6.004e-5). A matched networking pair whose difference is
   statistically overwhelming and practically nil — the cleanest published instance of the
   distinction the thesis's pre-committed interval-vs-*p* rule (§5.5) exists to enforce.
3. **Pirelli & Candea, ICSE 2023** (pp. 2173–2184). Argues safety without run-time overhead is
   achievable through type invariants, and shows **safe network device drivers with no run-time
   overhead** in extended Rust and C#. The peer-reviewed counterweight to `emmerich2019drivers`:
   the thesis currently presents the "not literally free" side of this question only.
4. **Li, Guo, Yang, Wang & Xu, ACM TOCS 44(2), 2026** — "Rust Meets Linux: Lessons from an
   Evolving Experiment". Same author list as `li2024rustforlinux` (USENIX ATC '24): this is the
   journal version, and it sharpens the conclusion — "If not properly managed, Rust's safety
   features even introduce notable runtime overhead and increased development complexity."
   Citation **upgrade**, and a contrary result the thesis should carry rather than soften.
   *Article number not confirmed; Crossref reports pages 1–33 — check before citing with a page
   range.*
5. **Hughes & Tratt, PACMPL 9(OOPSLA2):3588–3614, 2025** — "Garbage Collection for Rust: The
   Finalizer Frontier". Opens with the fact the RQ2 boundary needs: Rust's lack of GC makes
   shared-ownership data structures "awkward, inefficient, or both". Peer-reviewed support for
   the reference-cycle leak class, one of the two boundary classes that came back with the C++
   tooling ahead.
6. **Hong & Ryu, CACM 68(11):58–65, 2025** — "Automatically Translating C to Rust". Peer-reviewed
   home for the RQ4 translation story, in place of leaning on preprints (§6.2).
7. **Zhuang, SoftwareX 35:102771, 2026** — FlowPrioritize, a priority-scheduling library for
   async Rust runtimes. Supporting evidence, alongside `skoudlil2025asyncrust`, that priority and
   determinism are things async Rust runtimes must be *given*, not properties they have.
8. **Okawa & Yamaguchi, CANDARW 2024** (pp. 355–359) — finds Rust "significantly lower" in some
   cases and proposes mitigation. Minor, small venue; use only if a second general contrary
   result is wanted next to `emmerich2019drivers`.

Also surfaced, peer-reviewed, relevant but optional: Cui et al., ICSE 2024 (safety requirements
in unsafe Rust, 10.1145/3597503.3639136); Zhang et al., QRS 2024 (bugs beyond memory safety,
10.1109/QRS62785.2024.00035); Gülmez et al., SecDev 2023 (in-process isolation for unsafe Rust,
10.1109/SecDev56634.2023.00020 — a third source on the point `rivera2021galeed` and
`kirth2022pkrusafe` already make); Poos et al., ICSOFT 2025 (controlled experiment on ownership
and error localisation, but Rust against **Java**, 10.5220/0013647500003964).

## D. What has to change in the documents

Ordered by risk, highest first.

1. **`Thesis_Plan_v2.tex` §2, sentence 1** — "Two master's theses at Ericsson are the closest
   prior work" is factually wrong now. Minimum fix: "at least five", naming the two that carry
   the argument and citing the rest.
2. **`Thesis_Plan_v2.tex` §2, final paragraph** — replace the unqualified "Neither isolates the
   language … The gap is therefore" with the three-axis formulation already used in
   `Ha_Vien_Mastersthesis_2026.tex` §`sec:relatedwork` ("Individually, none of the three axes is unoccupied…").
   The plan currently makes a stronger claim than the full draft does, which is the wrong way
   round for a supervisor-facing document.
3. **`Ha_Vien_Mastersthesis_2026.tex` §`sec:gap` and §`sec:relatedwork`** — add Emberg & Wadsten as the closest
   work by method, and Olsson & Stenström as the third instance of the runtime confound. New
   rows for `tab:related`: Emberg & Wadsten (matched pair **yes**, overload tail no, adoption
   cost **dev. effort + seam**), Suchert & Castrillon (matched pair yes, others no), Gonzalez et
   al. (matched pair yes, others no), Olsson & Stenström (matched pair no, tail no, no).
   ⚠ `diagrams/29_research_gap.drawio` is hand-laid-out: adding study columns means editing the
   diagram, or the figure and the table will contradict each other. Same constraint as recorded
   for `tab:threats` in the first sweep — decide deliberately, do not half-do it.
4. **`Thesis_v2.tex`** ch. 1 and ch. 4 bullets — both say "the closest prior work does not
   isolate the language" and cite the two theses. Same correction, one bullet each.
5. **§`sec:rqdiscussion`, peak RSS** — add `olsson2023ranmgmt` (same domain, same direction) and
   optionally `sundvisson2026drivers`. Keep the allocator-dominates finding intact.
6. **§`sec:threats`, skill asymmetry** — cite Emberg & Wadsten's session-to-session reversal as
   the documented instance of the threat.
7. **§`sec:methodperf` / methodology search protocol** — add DiVA and Finna to the named sources,
   and state that the closest prior work is grey literature absent from the citation indexes.
   This is a strength, not an embarrassment: it is why the comparison has not been made yet.

## E. Negative results, recorded so they are not searched for again

- **There is no Nokia-side or Finnish counterpart.** Finna, which federates Aaltodoc, Trepo,
  Helda, JYX, LUTPub, UTUPub, Osuva, Oulu and Theseus, returns nothing on Rust with RAN, 5G,
  telecom or tail latency. The Finnish Rust literature is device drivers (Meyer, Tampere 2024),
  embedded schedulers (Abu Hanif, Tampere 2025), memory-management overviews and course
  material. The entire domain-specific prior work is Swedish and Ericsson-hosted.
- **Checked again on the publication side, 17 August 2026, and the absence holds.** OpenAlex
  author-affiliation search across Nokia's institutional entities (US ≈18,200 indexed works,
  Finland ≈8,500, Germany ≈2,100, France ≈1,450) with `title_and_abstract.search`:
  - `radio access network` → several hundred hits, so the filter demonstrably works and the
    nulls below are real rather than an artefact of a wrong institution ID. **Check this first if
    you ever re-run it**; a mistyped ID returns zero for everything and looks like a finding.
  - `Rust` → **one** hit, counted twice across two entities: *Profiling with Trust: System
    Monitoring from Trusted Execution Environments* (Research Square **preprint**, two Nokia
    Finland co-authors). Rust is incidental to it. Not a language comparison, not citable as one.
  - `memory safety` → **two** hits, both Nokia US: the 2002 Dalí storage manager (unrelated;
    "safety" in the database-durability sense) and **Gjomemo et al., QRS 2016** — see below.
- **The one genuinely useful thing that search turned up** is `gjomemo2016mesc`: *Leveraging
  Static Analysis Tools for Improving Usability of Memory Error Sanitization Compilers*, QRS 2016,
  pp. 323–334, two of six authors at Nokia. VERIFIED against Crossref. Its premise, quoted from
  the abstract, is that certifying compilation "has not been practical, leaving code
  instrumentation as the next best strategy for compilation". That is the after-the-fact detection
  branch the thesis argues against, stated in a peer-reviewed venue with the host vendor's own
  co-authors. It converts the Nokia framing from *"our company has not done this"* — which is not
  a research gap and would read badly — into *"the nearest published position from this side takes
  the opposite branch"*, which is one. Use it that way and not as corporate score-keeping.
  Note honestly that two of six authors is a collaboration, not a corporate position: the prose
  says "co-authored by two Nokia researchers", which is what the record supports.
- **No peer-reviewed study, in any venue, compares Rust and C++ implementations of a stateful,
  concurrent control-plane subsystem under overload.** The three axes are occupied separately
  (matched pairs: Emmerich, Li, Narayanan, Suchert, Gonzalez, Pirelli; control-plane percentile
  latency: Arvidsson, Michaelides; adoption cost: Karlbäck, Emberg, Li TOCS, Hong) and never
  together. This is the sentence the gap should rest on.
- **No 2026 work closes the gap.** arXiv returns nothing on Rust plus gNB / radio access /
  control plane in 2026; the nearest is `Zink et al., RBFRT` (2025), a Rust runtime-control API
  for Intel Tofino switches — networking control software in Rust, no C++ counterpart, no
  language comparison. Venue unconfirmed, do not cite as peer-reviewed.
- The generic web result set for "Rust vs C++ 2026" is unchanged from §8: vendor blogs and SEO
  content, now including two claiming 20–45% p99 *improvements* after a Rust rewrite. Still not
  citable. Still consistent with the thesis's allocation findings, and still not evidence.
- DBLP's publication API ignores `author:Name:` prefix syntax and returns nothing; use free-text
  queries. Semantic Scholar's search endpoint rate-limits hard (HTTP 429) at more than roughly
  one query per five seconds without a key; its single-paper `DOI:` lookup is the reliable path.

## F. BibTeX for the additions

Every field below was read from the DiVA record or the Crossref deposit. Thesis levels are as
recorded by the repository; the two 2026 entries are **bachelor's** theses and must be described
as such wherever they appear.

```bibtex
@mastersthesis{olsson2023ranmgmt,
  author    = {Olsson, Viktor},
  title     = {{Rust} Programming Language as an Alternative to {C} for {RAN}
               Management Applications},
  school    = {KTH Royal Institute of Technology, School of Electrical Engineering
               and Computer Science},
  year      = {2023},
  type      = {Master's thesis},
  note      = {Carried out at Ericsson AB},
  url       = {https://urn.kb.se/resolve?urn=urn:nbn:se:kth:diva-325822}
}

@mastersthesis{olsson2023asyncpackets,
  author    = {Olsson, Josef and Stenstr{\"o}m, Isak},
  title     = {{Rust} Async for Thread-per-Core Packet Processing},
  school    = {Link{\"o}ping University, Department of Computer and Information
               Science},
  year      = {2023},
  type      = {Master's thesis},
  note      = {Carried out at Ericsson AB. Report
               LIU-IDA/LITH-EX-A--23/052--SE},
  url       = {https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-197029}
}

@mastersthesis{emberg2023asn1,
  author    = {Emberg, Cecilia and Wadsten, Anna},
  title     = {Attainable Safety and Long-Term Resource-Efficiency Using {Rust}:
               Evaluating the Viability of {Rust} in Terms of Development Effort
               and Performance for the Decompilation of {ASN.1} Messages},
  school    = {Link{\"o}ping University, Department of Computer and Information
               Science},
  year      = {2023},
  type      = {Master's thesis},
  note      = {Carried out at Ericsson, Link{\"o}ping. Report
               LIU-IDA/LITH-EX-A--23/078--SE},
  url       = {https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-195552}
}

@mastersthesis{sundvisson2026drivers,
  author    = {Sundvisson, Alexander and Hofer, Silas},
  title     = {User-Space Device Drivers on Embedded {Linux}: A Comparative Case
               Study of {C} and {Rust}},
  school    = {Blekinge Institute of Technology, Department of Software
               Engineering},
  year      = {2026},
  type      = {Bachelor's thesis},
  url       = {https://urn.kb.se/resolve?urn=urn:nbn:se:bth-29775}
}

@mastersthesis{andersson2026stdmemsafety,
  author    = {Andersson, Oliver},
  title     = {Programming Language Standards and Their Impact on Memory Safety:
               {C++}, {Rust} and {Python}},
  school    = {Link{\"o}ping University, Department of Computer and Information
               Science},
  year      = {2026},
  type      = {Bachelor's thesis},
  note      = {Report LIU-IDA/LITH-EX-G--26/057--SE},
  url       = {https://urn.kb.se/resolve?urn=urn:nbn:se:liu:diva-226479}
}

@inproceedings{suchert2023stamp,
  author    = {Suchert, Felix and Castrillon, Jeronimo},
  title     = {{STAMP-Rust}: Language and Performance Comparison to {C} on
               Transactional Benchmarks},
  booktitle = {Benchmarking, Measuring, and Optimizing (Bench 2022)},
  series    = {Lecture Notes in Computer Science},
  volume    = {13852},
  pages     = {160--175},
  publisher = {Springer},
  year      = {2023},
  doi       = {10.1007/978-3-031-31180-2_10},
  url       = {https://doi.org/10.1007/978-3-031-31180-2_10}
}

@inproceedings{gonzalez2023rustudp,
  author    = {Gonzalez, Am{\'e}lie and Mvondo, Djob and Bromberg,
               Y{\'e}rom-David},
  title     = {Takeaways of Implementing a Native {Rust} {UDP} Tunneling Network
               Driver in the {Linux} Kernel},
  booktitle = {Proceedings of the 12th Workshop on Programming Languages and
               Operating Systems (PLOS)},
  pages     = {18--25},
  year      = {2023},
  doi       = {10.1145/3623759.3624547},
  url       = {https://doi.org/10.1145/3623759.3624547}
}

@inproceedings{pirelli2023safelowlevel,
  author    = {Pirelli, Solal and Candea, George},
  title     = {Safe Low-Level Code Without Overhead is Practical},
  booktitle = {Proceedings of the 45th IEEE/ACM International Conference on
               Software Engineering (ICSE)},
  pages     = {2173--2184},
  year      = {2023},
  doi       = {10.1109/ICSE48619.2023.00183},
  url       = {https://doi.org/10.1109/ICSE48619.2023.00183}
}

@article{li2026rustlinux,
  author  = {Li, Hongyu and Guo, Liwei and Yang, Yexuan and Wang, Shangguang and
             Xu, Mengwei},
  title   = {{Rust} Meets {Linux}: Lessons from an Evolving Experiment},
  journal = {ACM Transactions on Computer Systems},
  volume  = {44},
  number  = {2},
  year    = {2026},
  doi     = {10.1145/3789260},
  url     = {https://doi.org/10.1145/3789260}
}

@article{hughes2025gcrust,
  author  = {Hughes, Jacob and Tratt, Laurence},
  title   = {Garbage Collection for {Rust}: The Finalizer Frontier},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {9},
  number  = {OOPSLA2},
  pages   = {3588--3614},
  year    = {2025},
  doi     = {10.1145/3763179},
  url     = {https://doi.org/10.1145/3763179}
}

@article{hong2025ctorust,
  author  = {Hong, Jaemin and Ryu, Sukyoung},
  title   = {Automatically Translating {C} to {Rust}},
  journal = {Communications of the ACM},
  volume  = {68},
  number  = {11},
  pages   = {58--65},
  year    = {2025},
  doi     = {10.1145/3737696},
  url     = {https://doi.org/10.1145/3737696}
}

@article{zhuang2026flowprioritize,
  author  = {Zhuang, Kaiyi},
  title   = {{FlowPrioritize}: A Model-Driven Priority Scheduling Library for
             Asynchronous {Rust} Runtimes},
  journal = {SoftwareX},
  volume  = {35},
  pages   = {102771},
  year    = {2026},
  doi     = {10.1016/j.softx.2026.102771},
  url     = {https://doi.org/10.1016/j.softx.2026.102771}
}

@inproceedings{gjomemo2016mesc,
  author    = {Gjomemo, Rigel and Phung, Phu H. and Ballou, Edmund and
               Namjoshi, Kedar S. and Venkatakrishnan, V. N. and Zuck, Lenore},
  title     = {Leveraging Static Analysis Tools for Improving Usability of
               Memory Error Sanitization Compilers},
  booktitle = {Proceedings of the 2016 IEEE International Conference on Software
               Quality, Reliability and Security (QRS)},
  pages     = {323--334},
  year      = {2016},
  note      = {Two of the six authors are affiliated with Nokia},
  doi       = {10.1109/QRS.2016.44},
  url       = {https://doi.org/10.1109/QRS.2016.44}
}

@inproceedings{okawa2024ruststudy,
  author    = {Okawa, Shunsuke and Yamaguchi, Saneyasu},
  title     = {A Performance Study on {Rust} and {C} Programs},
  booktitle = {Proceedings of the 12th International Symposium on Computing and
               Networking Workshops (CANDARW)},
  pages     = {355--359},
  year      = {2024},
  doi       = {10.1109/CANDARW64572.2024.00066},
  url       = {https://doi.org/10.1109/CANDARW64572.2024.00066}
}
```

---

# Fourth sweep, 19 August 2026 — the apparatus, not the argument

> **Status: four items applied on 19 August 2026. The rest remain candidates.**
>
> Applied, as the minimum set agreed with the author (§G items 1, 2, 3 and 7):
>
> | Item | Where it went | Entries added |
> | --- | --- | --- |
> | Loom accuracy fix | §`sec:safetyresults`, the two-model-checker paragraph | `bornholt2021shardstore` |
> | TSan mechanism and detector status | §`sec:cpplatency`, the sanitiser-limits paragraph | `bensalem2005deadlock`, `tsandeadlock` |
> | RustMC | §`sec:interop` and the future-work list | `pearce2026rustmc` |
> | CHERI-SIMT caution | §`sec:relatedwork`, beside `harris2023morello` | `naylor2026cherisimt` |
>
> `bibliography.bib` is at 105 entries, all cited, no orphans. The build is clean at 163 pages with
> zero errors and zero undefined references, and the one overfull box is the pre-existing 63.2811pt
> one. Dash and semicolon counts are unchanged.
>
> **One lesson worth keeping, because it cost two rebuilds.** The first drafts of the TSan and
> CHERI-SIMT additions were full paragraphs placed next to rigid `[H]` floats, and each one bumped a
> float and cost two pages of half-empty layout. Rewriting them as clauses inside existing
> paragraphs, and moving the TSan attribution back to where the tool is introduced in Chapter 2,
> removed the cascade entirely. In this document, *where* a sentence goes matters as much as how long
> it is.
>
> **Revised the same day.** The first version of this sweep anchored each area on the paper that
> founded it, which for allocators meant 1998 to 2002 and for benchmarking meant 2009 to 2015. The
> author's objection was that this is too old for a 2026 submission, and it was correct: a
> bibliography an examiner scans by date should not rest on twenty-year-old work for a claim about
> current software. The sweep was re-run under a stricter rule.
>
> **The rule.** Every area is anchored on the most recent peer-reviewed source that makes the
> claim. A founding paper is cited only where the thesis names the *algorithm* that paper
> introduced, in which case its date is a fact about the algorithm rather than a weakness in the
> bibliography, exactly as `holm1979simple` and `efron1993bootstrap` already work in
> §`sec:stats`. Everything else that could not be replaced with current work is marked
> **superseded** below and should not be cited.
>
> The re-run paid off in every area. The anchors are now ISMM 2026, FORTE 2026, PLDI 2026,
> ASPLOS 2026, ICPE 2026, and *Sensors* 2024, and four of them are closer to the thesis than the
> older sources were. One of them, RustMC, verifies concurrent Rust *across an FFI boundary* and
> evaluates itself against Loom's own test suite, which is this thesis's exact apparatus.

The first three sweeps searched for work that bears on the *argument*: Rust against C++, the RAN
domain, the research gap. None of them audited the citations behind the *apparatus*, meaning the
tools the results are produced with and the statistical treatment they are read under. This sweep
did that, and the apparatus turns out to be the thinnest-cited part of an otherwise very strong
bibliography.

The trigger was a mechanical audit rather than a hunch. `bibliography.bib` holds 100 entries, every
one of them cited and none orphaned, and it contains **no citation at all** for any of the
following, each of which the draft leans on:

| Load-bearing in the draft | Occurrences | Citations today |
| --- | --- | --- |
| `jemalloc`, arenas, allocator effect on peak RSS | RQ3's headline result | none |
| Loom, Shuttle, and what their guarantees are | the RQ2 boundary answer | none |
| ThreadSanitizer's mechanism and its intermittency | `tab:faults` footnote `$^{\S}$` | none |
| The virtualised host as a limit on the far tail | the reason criteria 3 and 4 sit at 4.5 | none |
| Systems benchmarking methodology | all of §`sec:stats` | one, `georges2007rigorous`, Java and JIT-oriented |

Four of those five are places where the draft explains a *mechanism* in its own voice. That is the
category an examiner probes first, because it is where a thesis is most easily caught asserting
something it has not established. Each one below can now be attributed instead.

## A. What the audit found, separately from this sweep

Worth recording because it is cheap to act on and independent of anything new.

**Twenty-two candidates from the first sweep were verified and never applied.** They are the
scheduling and sharding set (`liao2025pallas`, `jia2024aquifer`, `jia2024skyloft`,
`iyer2023concord`, `enberg2019iofaster`), the coordinated-omission supports
(`friedrich2017coordinated`, `vanderkouwe2019benchmarking`, `li2026tailbench`), the overload
sources (`nguyen2025rrcevt`, `giustini2026stormshield`), the control-plane baseline
(`mukute20245gcore`), the RQ2 boundary material (`cve202623194`, `cve202664467`, `delmas2026kani`,
`lattuada2024verus`, `leblanc2024verification`, `villani2025treeborrows`), and four singletons
(`nsacisa2025msl`, `stroustrup2025cpp21`, `lacava2025dapps`, `teper2024starvation`,
`xie2025cooperative`). Sweep 1 §10 item 8 deliberately left these as a judgement call about how
much related work a master's thesis needs. That judgement has still not been made, and two of them
(`vanderkouwe2019benchmarking`, `enberg2019iofaster`) now look stronger in light of §E below.
`hong2025c2rust` in that list is a duplicate key for the applied `hong2025ctorust`, not a real
outstanding item.

Reproduce the audit with `.bibaudit/sweep_diff.py`. Metadata for anything new is checked with
`.bibaudit/verify_candidates.py DOI ...`, which prints the registration agency's own record,
including the `subtitle` field that ACM's older deposits keep separate from `title` (this is why
several titles below look truncated in Crossref and are given here in full).

## B. What the model checkers and sanitisers actually guarantee

**Read the two unnumbered entries first.** They are the current work and they are closer to this
thesis than anything else in this sweep. B.1 is the only peer-reviewed account of Loom and Shuttle
in production and is what corrects the draft, so it stays. B.2 to B.5 are the papers that
*introduced* the algorithms the draft names, and under the recency rule they are cite-the-origin
material only: use them in the sentence that names the algorithm, or not at all. B.6 is tool
documentation and is dated by nature.

### The anchor: Pearce, Lange and O'Keeffe, FORTE 2026 — VERIFIED

"RustMC: Automated Verification of Real-World Concurrent Rust". Oliver Pearce, Julien Lange, Dan
O'Keeffe (Royal Holloway, University of London). *Formal Techniques for Distributed Objects,
Components, and Systems* (FORTE 2026), Urbino, 8--12 June 2026, LNCS, pages 235--255.
DOI 10.1007/978-3-032-28187-6_14. (A February 2025 preprint exists as arXiv 2502.06293 under the
earlier title "RustMC: Extending the GenMC stateless model checker to Rust". Cite the FORTE
version.)

**This is the best find of the revised sweep and it lands on two of the thesis's claims at once.**
A stateless model checker for concurrent Rust built on GenMC, and, from the abstract, it verifies
"Rust code and any foreign function dependencies", finding "concurrency bugs in unsafe Rust code,
FFI calls to C/C++, and atomic operations". The authors state it is "the only available framework
capable of exhaustively exploring the state space of Rust programs and their dependencies".

Two consequences for this thesis, both material:

1. **It is the tool that would verify the RQ4 seam.** The thesis builds an `extern "C"` seam by
   hand, confines `unsafe` to it, and argues the tax is bounded rather than free. What it does not
   do, and says it does not do, is verify the seam's concurrency behaviour. RustMC is exactly that
   capability, published four months before submission. This belongs in future work and in the
   §`sec:interop` discussion, and volunteering it is much better than having an examiner name it.
2. **It benchmarks against Loom's own test suite.** The authors "evaluate our tool's functionality
   on the Loom model checker test suite and a set of production-level Rust concurrent data
   structures". So the thesis's choice of Loom can now be positioned against a published
   evaluation of Loom rather than against the tool's documentation.

### State of the art in interleaving exploration: Kokologiannakis et al., POPL 2022 — VERIFIED

"Truly stateless, optimal dynamic partial order reduction". Michalis Kokologiannakis, Iason
Marmanis, Vladimir Gladstein, Viktor Vafeiadis. *Proceedings of the ACM on Programming Languages*
6(POPL):1--28, 2022. DOI 10.1145/3498711.

Relevant for one specific reason. B.1 establishes that Loom uses **bounded** partial-order
reduction, a 2013-era technique, and this is the optimal-DPOR result that supersedes it: one
interleaving per equivalence class, exhaustive without a bound. It lets the draft say what its
tool's bound costs, in current terms, instead of leaving "exhaustively" unqualified. Optional, but
it is the difference between naming a limitation and appearing not to know there is one.

A companion, if the distributed case is ever wanted: **Enea, Giannakopoulou, Kokologiannakis and
Majumdar, "Model Checking Distributed Protocols in Must"**, PACMPL 8(OOPSLA2):1900--1927, 2024,
DOI 10.1145/3689778. VERIFIED. Out of scope for a single-process subsystem. Recorded so it is not
re-found.

### B.1 Bornholt et al., SOSP 2021 — VERIFIED, and it corrects the draft

"Using Lightweight Formal Methods to Validate a Key-Value Storage Node in Amazon S3". James
Bornholt, Rajeev Joshi, Vytautas Astrauskas, Brendan Cully, Bernhard Kragl, Seth Markle, Kyle
Sauri, Drew Schleit, Grant Slatton, Serdar Tasiran, Jacob Van Geffen, Andrew Warfield. SOSP '21,
pages 836--850. DOI 10.1145/3477132.3483540.

**This is the find of the sweep.** It is a peer-reviewed account of a production Rust system
validated with *the same two model checkers this thesis uses, for the same reason*, by the team
that wrote one of them. Read the paper's own description against `Ha_Vien_Mastersthesis_2026.tex`:2932--3047 and
the draft is doing the same thing on a smaller object.

Three passages are directly usable, quoted from the paper's section on checking concurrent
executions:

- Loom "implements the CDSChecker algorithm for sound model checking in the release/acquire memory
  model, and uses bounded partial-order reduction to reduce state explosion."
- "we developed and open-sourced the stateless model checker Shuttle, which implements randomized
  algorithms such as probabilistic concurrency testing."
- "We use Loom to soundly check all interleavings of small, correctness-critical code such as
  custom concurrency primitives, and Shuttle to randomly check interleavings of larger test
  harnesses to which Loom does not scale."

That third sentence is the division of labour `faults/run_model_checking.sh` implements, stated
independently in a top venue.

**The correction.** `Ha_Vien_Mastersthesis_2026.tex`:3030 says Loom "enumerates thread interleavings exhaustively
under the C11 model". Two words in that are loose. The model is **release/acquire**, a fragment of
C11 rather than C11 entire, and the exploration is sound **under bounded partial-order reduction**
rather than exhaustive without qualification. The draft's claim is close enough to be defensible
in conversation and wrong enough to be worth fixing in writing, and fixing it costs one clause.
Note also that a bound is a *stronger* thing to admit here, because the draft already says each
model had to be shrunk to fit: the bound is part of why.

Two more things in the paper are worth a sentence each. It records that ShardStore needs "a small
amount of unsafe Rust code, mostly for interacting with block devices" and that the team ran the
suite under Miri and **had to extend Miri to support threads and locks** before it was useful,
which is a published precedent for both the draft's `unsafe`-free-core design and its use of Miri
at `Ha_Vien_Mastersthesis_2026.tex`:2130. And its related work reports VeriBetrKV's cost as "7 lines of proof for
every line of implementation", which sits alongside the roughly 5-to-1 figure recorded for Verus
in §5.2 of the first sweep.

Incidental but pleasing: Vytautas Astrauskas is a co-author here and is already in the
bibliography as `astrauskas2020unsafe`.

### B.2 Burckhardt et al., ASPLOS 2010 — VERIFIED, origin of the algorithm

"A randomized scheduler with probabilistic guarantees of finding bugs". Sebastian Burckhardt,
Pravesh Kothari, Madanlal Musuvathi, Santosh Nagarakatte. ASPLOS '10, pages 167--178.
DOI 10.1145/1736020.1736040.

Probabilistic concurrency testing itself, and the reference Bornholt et al. cite for what Shuttle
implements. The draft says Shuttle "samples them with probabilistic concurrency testing", which is
exactly right and currently unattributed. Citing PCT also lets the draft say what kind of
assurance a Shuttle pass is: a probabilistic guarantee parameterised by bug depth, not a proof.
That distinction matters, because the draft's whole RQ2 argument is about *what stage and what
strength* of detection each language gets.

### B.3 Norris and Demsky, OOPSLA 2013 — VERIFIED, origin of the algorithm

"CDSchecker: checking concurrent data structures written with C/C++ atomics". Brian Norris, Brian
Demsky. OOPSLA '13, pages 131--150. DOI 10.1145/2509136.2509514. (Crossref splits the subtitle;
the full title is as given.)

Loom's algorithm, one level down from B.1. Optional. Cite it if the draft wants to name the model
rather than take Loom's soundness on the tool's word, which for a claim about what a *guarantee*
covers is the more careful choice.

### B.4 Serebryany and Iskhodzhanov, WBIA 2009 — VERIFIED, origin of the tool

"ThreadSanitizer: data race detection in practice". Konstantin Serebryany, Timur Iskhodzhanov.
WBIA '09, pages 62--71. DOI 10.1145/1791194.1791203. (Subtitle split in Crossref as above.)

The tool the C++ arm's safety claim rests on, cited nowhere in a thesis that names it twenty-two
times. It is a workshop paper, which is the honest thing to say about it, and it is the
authors' own account of the hybrid happens-before-plus-lockset algorithm. Straight fill.

### B.5 Bensalem and Havelund — VERIFIED, and it explains the draft's own result

"Dynamic Deadlock Analysis of Multi-threaded Programs". Saddek Bensalem, Klaus Havelund. Haifa
Verification Conference 2005, LNCS 3875, pages 208--223. DOI 10.1007/11678779_15.
*Note the date:* the conference is 2005, Springer's deposit records the LNCS volume as 2006. Cite
the conference year and the volume, as DBLP does.

**This is the peer-reviewed foundation for the mechanism `Ha_Vien_Mastersthesis_2026.tex`:3009--3012 explains in
its own voice.** The draft argues that TSan builds its lock-order graph from acquisitions that
succeed, so a run in which the first inversion blocks yields one edge and never the second, and
the detector stays silent at the moment the bug manifests. Bensalem and Havelund set out the
technique that reasoning is about: lock-graph analysis over a single execution trace, in which a
cycle signifies a deadlock *potential*, and whose stated purpose is to "identify deadlock
potentials even though no deadlocks occur in the examined execution trace".

Read together, the draft's finding stops being an oddity and becomes the expected behaviour of the
technique. The analysis is designed for traces that *survive*, so the trace that deadlocks is the
one it has least to say about. That is a much stronger way to write the same paragraph, and it
generalises the way the draft already claims it does.

The paper is also about reducing false positives specifically, via thread labels, gate locks and
segmentation, which is the complementary error mode and worth one clause for balance.

**On its date.** 2005 is old, and here that is the point rather than a problem: the draft names the
technique, so this is the paper that introduced it. The recent companion is already in the
bibliography. `tang2025converos` (USENIX ATC 2025) model-checked twelve concurrency modules of a
Rust operating system and found twenty bugs including deadlocks and livelocks, at a
specification-to-code ratio of 0.3 to 2.3 and four person-months of effort. Those are *cost*
figures for getting concurrency defects caught at model-checking time, which is the quantity
`Ha_Vien_Mastersthesis_2026.tex`:3038--3047 argues about and currently supports only with its own two models. Worth
checking whether the draft already uses that detail from a source it already cites.

### B.6 The two tool records, as tool records — VERIFIED as documentation, not as research

Neither is peer-reviewed. Both are primary sources about the software, which is what is wanted
here, and both must be labelled as such if cited.

- **ThreadSanitizerDeadlockDetector**, google/sanitizers wiki.
  <https://github.com/google/sanitizers/wiki/ThreadSanitizerDeadlockDetector>. States the
  mechanism in one sentence ("The deadlock detector maintains a directed graph of lock
  acquisitions. If a lock B is acquired while a lock A is being held by the same thread, a
  directed edge `A=>B` is added to the lock acquisition graph. A potential deadlock is reported
  when there is a cycle in the graph"), and describes the detector as **experimental**, supporting
  only `pthread_mutex_*` / `pthread_rwlock_*` / `pthread_spin_*`, and "tested only on tiny test
  cases". It also confirms that detection needs `TSAN_OPTIONS=detect_deadlocks=1`, which is worth
  checking against what `faults/` actually sets.
- **google/sanitizers issue #1258.** Upstream record that there are two detector implementations
  and that **neither is actively maintained**, plus a contributor's diagnosis that version 1, the
  default, checks for the cycle in `DD::MutexBeforeLock` while the edge is only added in
  `DD::MutexAfterLock`. That is the draft's mechanism, described by the tool's own issue tracker,
  and it independently corroborates a paragraph the draft currently supports with its own
  measurements alone.

**Use these carefully.** They raise the register of the `$^{\S}$` footnote in `tab:faults` from
"we observed this" to "this is a known property of an unmaintained experimental detector", which
is a materially stronger claim about continuous-integration practice. They do not license saying
TSan is broken in general: the race detector is a different component with a peer-reviewed
account (B.4) and the draft's own positive controls show it live.

## C. The virtualised host, cited rather than asserted

The single largest grade blocker in `AGENT.md` is that the measurement host is a virtualised KVM
guest, so the far tail below saturation cannot be resolved. That limitation is currently argued
entirely from first principles and from the guest's own counters. There is a literature on exactly
this quantity, and it is not cited.

**The revised sweep found it in the thesis's own domain, which the first version missed.** The
strongest sources here are not general real-time-virtualisation papers but measurements of
virtualised RAN, and three of them speak to the draft's threat row directly. They are placed first
below because they are the anchors. C.1 to C.3 keep the numbers they were given in the first version
of this sweep, so the numbering in this section records when each was found rather than the order to
read them in.

### C.4 Ocampo, Fida, Elmokashfi and Bryhni, *Sensors* 2024 — VERIFIED

"Assessing the Cloud-RAN in the Linux Kernel: Sharing Computing and Network Resources". Andres F.
Ocampo, Mah-Rukh Fida, Ahmed Elmokashfi, Haakon Bryhni. *Sensors* 24(7):2365, 2024.
DOI 10.3390/s24072365.

An empirical study of virtual baseband unit performance on a Linux real-time kernel under resource
contention with collocated workloads, evaluating **CPU affinity and CPU isolation as the
mitigations**. Reported effect: CPU affinity reduces throughput variability by up to 40% and
reduces scheduling latency for the real-time threads.

**This is the closest published support for the thesis's own controls.** §`sec:testbed` pins the
clock and isolates cores, and currently justifies both from first principles. Here is a
peer-reviewed, in-domain, 2024 measurement of what those two controls are worth, and of the
variability that remains without them. It is a better citation for the testbed design than anything
in the general virtualisation literature, and it is recent.

### C.5 Abeni et al., ISC High Performance Workshops 2022 — VERIFIED

"On the Use of Linux Real-Time Features for RAN Packet Processing in Cloud Environments". Luca
Abeni, Tommaso Cucinotta, Balázs Pinczel, Péter Mátray, Murali Krishna Srinivasan, Tobias
Lindquist. LNCS 13387, pages 371--382, 2022. DOI 10.1007/978-3-031-23220-6_26.

Names the mechanism behind the thesis's most specific admission. From the abstract: "A significant
portion of the variability and instability in the observed end-to-end performance in this domain is
due to the power saving capabilities of modern CPUs, often in contrast with the low-latency and
high-performance requirements of this type of applications." The draft's threat row says the
guest's frequency is unobservable. This says frequency management is a leading cause of
instability in cloudified RAN specifically, which is the argument the draft is reaching for, in a
cRAN context, with Ericsson co-authors.

### C.6 Foukas and Radunovic, SIGCOMM 2021 — VERIFIED

"Concordia: teaching the 5G vRAN to share compute". Xenofon Foukas, Bozidar Radunovic. SIGCOMM '21,
pages 580--596. DOI 10.1145/3452296.3472894.

Top-venue, in-domain, and the one sentence worth quoting is the premise: vRAN tasks "have
sub-millisecond latency requirements that have to be met 99.999% of times. We show that this is
difficult to achieve with existing systems." That is the thesis's regime and the thesis's
percentile, asserted by others in a better venue, on a commercial-grade reference platform. It
also supports the choice to report p99.9 and beyond rather than stopping at the median.

Optional companion: **Manousis, Sharma, Sekar and Sherry, "Contention-Aware Performance Prediction
For Virtualized Network Functions"**, SIGCOMM 2020, pages 270--282, DOI 10.1145/3387514.3405868.
VERIFIED. Contention between collocated virtualised network functions as a predictable quantity.
One source too many unless the threat section develops the collocation argument.

### C.1 Abeni and Faggioli, Journal of Systems Architecture 2020 — VERIFIED

"Using Xen and KVM as real-time hypervisors". Luca Abeni, Dario Faggioli. *Journal of Systems
Architecture* 106:101709, 2020. DOI 10.1016/j.sysarc.2020.101709. (A preliminary version exists as
ISORC 2019, pages 18--26, DOI 10.1109/ISORC.2019.00014. Cite the journal version.)

Measures the latency a hypervisor introduces, defined as the difference between the theoretical
schedule and the real one, across Xen and KVM on several machines, and gives configuration
guidance. Headline result: **a properly configured KVM guest shows a worst-case latency below
100 µs.**

**Cite this with care, because it cuts both ways and the careless reading is the wrong one.** It
does not say the thesis's host is fine. It says hypervisor-induced latency is a measurable
quantity, that it lands in the tens-to-hundreds-of-microseconds range, and that reaching the low
end of that range requires a configuration the thesis's general-purpose guest does not have. That
is the right shape of argument for §`sec:threats`: the interference is of the same order as the
percentiles under discussion, which is precisely why the far tail is not readable here and why
`bench/TESTBED.md` exists. Written that way it strengthens the limitation. Written as "KVM is good
to 100 µs" it would invite the examiner's obvious question.

### C.2 Gebai, Giraldeau and Dagenais, Journal of Cloud Computing 2014 — VERIFIED

"Fine-grained preemption analysis for latency investigation across virtual machines". Mohamad
Gebai, Francis Giraldeau, Michel R. Dagenais. *Journal of Cloud Computing* 3(1), 2014.
DOI 10.1186/s13677-014-0023-3.

**The closest match to the draft's own words.** `tab:threats` says of the virtualised host that
"frequency unobservable and CPU steal non-zero, neither removable from inside the guest". This
paper's premise is that averaged steal time "is insufficient to diagnose abnormal latencies in
time-sensitive applications", that "the added latency is not directly visible from the virtual
machine point of view", and that recovering the cause requires tracing on the host. It also records
that hardware performance counters are not available to guests. Every clause of the draft's threat
row is a finding in this paper.

**On its date, and the honest reading.** 2014 is the oldest thing in the revised sweep, and it
survives the recency rule only because no newer source states the from-inside-the-guest
unobservability argument as squarely. If one citation has to carry that argument, C.4 and C.5 are
newer and in-domain and should carry it, with this one added only if the specific point about
averaged steal time being insufficient is made explicitly. Do not use it as the sole support for
the threat row.

### C.3 Abeni, Journal of Systems Architecture 2024 — VERIFIED

"Virtualized real-time workloads in containers and virtual machines". Luca Abeni. *Journal of
Systems Architecture* 154:103238, 2024. DOI 10.1016/j.sysarc.2024.103238.

The current version of the same question, comparing container and VM latency with `cyclictest`, and
reporting that a non-real-time guest kernel gives a much larger worst case than a Preempt-RT one
even where the distributions look similar in shape. Useful in `bench/TESTBED.md` as published
support for the bare-metal protocol's design, and as the more recent of the two if only one is
wanted.

## D. Peak RSS: the allocator literature the RQ3 result needs

RQ3's headline is that peak RSS shows two effects, that both are real, and that the allocator
effect is roughly ten times the language effect. The draft explains the allocator half by pinned
arena count making arena metadata a large fixed cost on both sides (`Ha_Vien_Mastersthesis_2026.tex`:2861--2864).
No source is given for what an arena is, why its metadata scales with count, or why allocator
choice should dominate.

**This was the area the recency objection hit hardest, and it is now the best-resolved of the
five.** The first version of this sweep proposed Johnstone and Wilson (1998), Hoard (2000) and
Berger, Zorn and McKinley (2002). It turns out the 2002 paper was replicated in 2026 by one of its
own authors, using `jemalloc` specifically, and the replication is a better citation than the
original on every axis that matters here. Take D.0 and ignore the rest unless the lineage is wanted.

### D.0 van Kempen and Berger, ISMM 2026 — VERIFIED, and it replaces three older citations

"Reconsidering 'Reconsidering Custom Memory Allocation'". Nicolas van Kempen, Emery D. Berger.
*Proceedings of the 2026 ACM SIGPLAN International Symposium on Memory Management* (ISMM '26),
pages 14--24. DOI 10.1145/3814942.3816132.

A deliberate replication of Berger, Zorn and McKinley (2002) with modern allocators, by an author
of the original. Findings, as reported in the paper:

- Modern general-purpose allocators "have considerably closed the performance gap with region-based
  custom allocation, reducing region allocator speedups from up to 44% in the original study to at
  most 15% in our evaluation." The allocators named are `jemalloc` and `mimalloc`.
- Under **adversarial allocation**, meaning a heap preconditioned with synthetic fragmentation,
  naive allocation slows by up to 2× while region allocators are unaffected, and "the default Linux
  allocator is considerably more affected by fragmentation than jemalloc and mimalloc".

**Why this is the right citation for RQ3 rather than the 2002 original.** It is 2026. It names
`jemalloc`, which is the thesis's allocator, rather than a generic general-purpose allocator. It
establishes that the choice between `jemalloc` and the system allocator is a measurable, studied
effect on both time and footprint, which is exactly what the thesis found and currently presents
without external support. And its clean-heap-versus-adversarial contrast is a published precedent
for the draft's own careful hedge, that the ordering it measured "is partly a consequence of the
fairness controls rather than a fact about `jemalloc` in general": this paper shows the same
allocator ranking moving with the heap state it is measured under.

One caution. It is a study of allocator *performance* under fragmentation, not a study of peak RSS
attribution between a language and an allocator. It corroborates that allocator choice is a
first-order variable. It does not corroborate the specific ten-to-one ratio, and the prose must not
imply that it does.

### The three older allocator sources, and what to do with them

Under the recency rule these are **superseded by D.0** for every claim the thesis actually makes.
Recorded so the reasoning is not lost, and so they are not re-found in a later sweep.

- **Berger, Zorn and McKinley, "Reconsidering custom memory allocation"**, OOPSLA '02,
  DOI 10.1145/582419.582421. Cite only if the draft wants to say the 2026 result is a replication,
  which needs the original named. Crossref's deposit gives the first page only, so the page range
  would need confirming.
- **Berger et al., "Hoard: a scalable memory allocator for multithreaded applications"**, ASPLOS
  2000, pages 117--128, DOI 10.1145/378993.379232. The origin of per-thread heaps and of **memory
  blowup** as a named property. Cite only in a sentence that uses the term.
- **Johnstone and Wilson, "The memory fragmentation problem: solved?"**, ISMM 1998, pages 26--36,
  DOI 10.1145/286860.286864. Drop. D.0 makes the fragmentation point on current allocators.
- **Powers et al., "Mesh"**, PLDI 2019, DOI 10.1145/3314221.3314582, and **Liétar et al.,
  "snmalloc"**, ISMM 2019, DOI 10.1145/3315573.3329980. Both VERIFIED and both still reasonable on
  date, but neither is needed once D.0 is in. Keep in reserve.

### The remaining gap here, stated plainly

There is still no source for what a `jemalloc` arena *is*, because the allocator's own design paper
is the only place that describes it and that paper is from 2006 (D.1 below). This is unavoidable and
it is not a weakness: citing an allocator's design document for a fact about that allocator's design
is correct practice regardless of date, in the same way the thesis cites RFC 3393 for a definition.

### D.1 Evans, BSDCan 2006 — VERIFIED as a technical paper, not peer-reviewed

"A Scalable Concurrent malloc(3) Implementation for FreeBSD". Jason Evans. BSDCan 2006,
16 April 2006. <https://papers.freebsd.org/2006/bsdcan/evans-jemalloc/>

The canonical `jemalloc` reference, from the author, and the source of the arena design the draft's
result turns on. It presents arenas as the mechanism for reducing lock contention between threads
and discusses fragmentation measurement directly. Not peer-reviewed, and the entry should say so,
but citing the allocator's own design paper is better than citing nothing for a claim about that
allocator's metadata.

The superseded entries that stood here as D.2, D.3 and D.4 are consolidated in the block above.
Their metadata is verified and their BibTeX is retained in §I, so nothing has to be re-searched if
the lineage argument is wanted after all.

## E. The benchmarking canon §`sec:stats` already follows

§`sec:stats` is among the strongest sections in the thesis: interleaved variants, median with
non-parametric bootstrap intervals, asymmetric intervals reported in full, exact paired permutation
tests, Holm correction, a pre-committed interval-versus-*p* rule, and a stated resolving-power
floor. Its statistical machinery is properly referenced (`efron1993bootstrap` for the bootstrap,
`holm1979simple` for the correction), but it carries **one** citation for *benchmarking
methodology*, `georges2007rigorous`, which is about Java and JIT warm-up and is therefore slightly
off-target for a native two-language comparison. The community's standard reference for what this
section does is not cited.

**Two current sources came out of the re-run, and one of them closes an item sweep 1 left open.**
Sweep 1 §7.9 flagged "two ICPE 2026 preprints on variability-guided optimisation and on declarative
benchmark harnesses (author lists and final metadata unconfirmed)" and said they must not be cited
as they stood. The harness one is now confirmed with a DOI and page range, so that flag can be
cleared.

### E.0 Paolillo, Van Molle and Hasselmann, ICPE 2026 — VERIFIED

"benchkit: A Declarative Framework for Composable Performance Evaluation of System Software".
Antonio Paolillo, Mats Van Molle, Ken Hasselmann. *Proceedings of the 17th ACM/SPEC International
Conference on Performance Engineering* (ICPE '26), pages 170--183. DOI 10.1145/3777884.3796997.
Artifact badged Available, Functional and Reusable.

Not a source for a claim about Rust, and not a tool the thesis should adopt at this stage. It is
useful for a narrower and more valuable purpose: it is a 2026 peer-reviewed statement of what a
credible systems performance campaign has to record, and the thesis already does almost all of it.
Its repeatability section names, as the mitigations a framework should provide, fixing CPU
frequencies, disabling noise-inducing services such as `irqbalance`, repeated runs, and structured
capture of hardware, kernel version and frequency-governor state at experiment time. §`sec:testbed`
and §`sec:repro` do these things.

**It also states the thesis's own limitation in someone else's words**, which is why it belongs in
§`sec:threats` rather than only in §`sec:repro`: "full reproducibility and replicability of
system-level experiments are inherently limited by factors outside the framework's control:
hardware performance counters, kernel scheduler behavior, and low-level system interfaces may differ
across machines and kernel versions". That is the residual the thesis carries, published four
months before submission, by authors building infrastructure to reduce it.

### E.0b Papadopoulos et al., IEEE TSE 2021 — VERIFIED

"Methodological Principles for Reproducible Performance Evaluation in Cloud Computing". Alessandro
Vittorio Papadopoulos, Laurens Versluis, Andre Bauer, Nikolas Herbst, Joakim von Kistowski, Ahmed
Ali-Eldin, Cristina L. Abad, Jose Nelson Amaral, Petr Tuma, Alexandru Iosup. *IEEE Transactions on
Software Engineering* 47(8):1528--1543, 2021. DOI 10.1109/TSE.2019.2927908.

Ten authors, a software engineering journal, and a set of named principles for performance
evaluation where the platform is shared and partly unobservable. That last condition is the
thesis's condition. It is the better companion to E.1 than any of E.2 to E.4, because it is a
decade newer and because its subject is evaluation on infrastructure the experimenter does not fully
control.

### E.1 Hoefler and Belli, SC 2015 — VERIFIED

"Scientific benchmarking of parallel computing systems". Torsten Hoefler, Roberto Belli. SC '15,
pages 1--12. DOI 10.1145/2807591.2807644.

**The single highest-value addition in this sweep after B.1**, because it is the citation an
examiner in systems would expect to see and its rules are the ones the draft already keeps: report
distributions rather than single numbers, use non-parametric statistics for non-normal
measurements, state and justify the number of repeats, and report the uncertainty of derived
quantities. It converts §`sec:stats` from a well-argued local design into a design that visibly
conforms to a named standard. One sentence, large return.

### E.2 Kalibera and Jones, ISMM 2013 — VERIFIED

"Rigorous benchmarking in reasonable time". Tomas Kalibera, Richard Jones. ISMM '13, pages 63--74.
DOI 10.1145/2464157.2464160.

Peer-reviewed treatment of how to choose repetition counts under a time budget, which is exactly
the trade-off `\NRepeats{}` embodies and which the draft currently justifies by the corrected
significance floor alone. Pair with E.1 where the repeat count is set.

### E.3 Mytkowicz et al., ASPLOS 2009 — VERIFIED

"Producing wrong data without doing anything obviously wrong!". Todd Mytkowicz, Amer Diwan,
Matthias Hauswirth, Peter F. Sweeney. ASPLOS 2009, pages 265--276. DOI 10.1145/1508244.1508275.

Measurement bias from the environment, and the standard argument that experimental setups must be
varied or randomised rather than merely repeated. This is the peer-reviewed justification for the
interleaved design, which the draft currently motivates in its own words ("slow drift, thermal
effects, and background activity perturb them equally instead of biasing one"). Good fit,
low risk.

**On dates in this section.** E.1 is the canon and is cited on that basis, the way a standard
reference is. E.2 and E.3 are older and now optional: use E.2 only in the sentence that justifies
`\NRepeats{}`, and E.3 only in the sentence that justifies interleaving, since in both cases the
draft is making the argument that paper made. If neither sentence needs a citation, prefer E.0 and
E.0b, which are 2026 and 2021 and say enough on their own.

### E.4 Curtsinger and Berger, ASPLOS 2013 — VERIFIED, and it is a double-edged addition

"STABILIZER: statistically sound performance evaluation". Charlie Curtsinger, Emery D. Berger.
ASPLOS '13, pages 219--228. DOI 10.1145/2451116.2451141.

Shows that code and data **layout** alone shifts performance enough to swamp the effects
benchmarks try to measure, and randomises layout so that ordinary statistics become applicable.

**Read the consequence before deciding.** This thesis compares two separately compiled binaries,
so layout differs between the arms by construction, and layout is not among the controlled
variables in `tab:controls`. Citing STABILIZER names a confound the study does not remove. That is
a real residual threat rather than a manufactured one, and the interleaved design does not touch
it, because the layout difference is fixed across every repeat rather than varying with drift.
Two defensible positions: add it to §`sec:threats` as a named residual and gain credit for
volunteering it, or leave it out and risk an examiner who knows the paper. The first is more in
keeping with how the rest of the thesis handles inconvenient evidence, and it pairs naturally with
the forced-idiom log, which is already the draft's answer to "the two programs are not identical".
**This is the author's call, not an obvious add.**

## F. The `Bugden` replacement (criterion 2's last soft spot)

`docs/ASSESSMENT.md` has recorded for three passes that one load-bearing citation remains an arXiv
preprint: `bugden2022rust`, carrying "throughput and memory use alongside C and C++"
(`Ha_Vien_Mastersthesis_2026.tex`:822) and "compiled systems languages close on time and energy"
(`Ha_Vien_Mastersthesis_2026.tex`:3623).

Neither claim actually needs a preprint. Two peer-reviewed sources cover it, and one is already
half in the bibliography. **Both are 2021, so read F.0a and F.0b first: the re-run found two 2026
papers that report matched C++-to-Rust overheads directly, which is closer to the claim than either
2021 source and closer to this thesis than anything else in this section.**

### F.0a Popescu et al., PLDI 2026 — VERIFIED

"Cpp2Rust: Automatic Translation of C++ to Safe Rust". Lucian Popescu, Francisco Gouveia, Henrique
Preto, João Silveira, Dmytro Hrybenko, José Fragoso Santos, Nuno P. Lopes. *Proceedings of the ACM
on Programming Languages* 10(PLDI):480--504, 2026. DOI 10.1145/3808266. **PARTIAL on one field:
the authors' own PDF cites it as Article 188, 25 pages, while Crossref's deposit gives pages
480--504. Check which form the venue expects before citing with a page range.**

**This closes a gap sweep 1 explicitly recorded and could not fill.** Sweep 1 §6.2 surveyed
automated translation and noted, as the reason none of it supersedes RQ4, that "they translate C
(not C++)". This is C++ to Rust, at PLDI, four months before submission, and the authors call it
"the first system capable of translating C++ programs into functionally equivalent and memory-safe
Rust code automatically".

Three things in it are directly usable:

- The mechanism is a *cost*, stated as a design choice: it resolves the mismatch between C++'s
  unrestricted aliasing and Rust's ownership model "by inserting runtime-enforced ownership and
  mutability checks", explicitly "trading some performance for security". That is the opposite pole
  from the thesis's hand-written seam, which keeps the core `unsafe`-free and pays a bounded tax at
  the boundary instead.
- The measured spread is the useful part: "full memory safety with only a 2% performance penalty on
  WOFF2 compression, while being 6× slower on Brunsli due to heavy usage of pointer arithmetic".
  A range from 2% to 6× on two programs from one tool is a strong argument for the thesis's own
  position that a language-level overhead claim has to be made on the target workload rather than
  in general.
- It puts a boundary on RQ4's future work. Automated C++-to-Rust translation now exists and is
  semantics-preserving, so the future-work sentence should no longer say the migration must be
  manual. It should say what the automated route costs where the seam route does not.

### F.0b Naylor et al., ASPLOS 2026 — VERIFIED, and it criticises a source the thesis already cites

"CHERI-SIMT: Implementing Capability Memory Protection in GPUs". Matthew Naylor, Alexandre Joannou,
A. Theodore Markettos, Paul Metzger, Simon W. Moore, Timothy M. Jones. ASPLOS '26, pages 50--66.
DOI 10.1145/3760250.3762234. **PARTIAL on the year: Crossref's deposit records 2025 while the event
field records ASPLOS '26. Confirm the citable year before use.**

The GPU subject looks off-topic and the relevant part is not the subject. The authors build a
**like-for-like C++-to-Rust port** of a benchmark suite and report "a geometric mean overhead of
46% from using Rust", of which "bounds checking alone accounts for a 34% overhead".

**The reason to add it is the paragraph after that number.** It engages `harris2023morello`, which
this thesis already cites, and disputes how it should be read: prior work "reports that the Rust
compiler is very good at eliminating bounds checks, resulting in low overhead ... However, care is
needed when interpreting these results as it is unclear how many bounds checks are avoided due to
the use of unsafe code blocks. For example, in the matrixmultiply benchmark they use, the key
functions are declared as unsafe and operate directly on raw pointers."

That is a peer-reviewed 2026 critique of a citation already in the bibliography, and it is the
single most useful item in this sweep for criterion 2, which is graded on critical maturity and on
acknowledging contrary results. It also supports a design decision the thesis has already made and
currently defends on its own terms: measuring a core that is `unsafe`-free means the bounds checks
are actually present, so the overhead being reported is the real one. Cite it in
§`sec:relatedwork` next to `emmerich2019drivers` and `suchert2023stamp`, and note honestly that
the workload is a GPU kernel and the absolute figure does not transfer.

### F.1 Pereira et al., Science of Computer Programming 2021 — VERIFIED

"Ranking programming languages by energy efficiency". Rui Pereira, Marco Couto, Francisco Ribeiro,
Rui Rua, Jácome Cunha, João Paulo Fernandes, João Saraiva. *Science of Computer Programming*
205:102609, 2021. DOI 10.1016/j.scico.2021.102609.

The journal extension of `pereira2017energy`, which the thesis already cites for the same claim in
the same sentence. Upgrading to the journal version and dropping the preprint costs nothing and
removes the soft spot from the time-and-energy half outright.

### F.2 Costanzo, Rucci, Naiouf and De Giusti, CLEI 2021 — VERIFIED

"Performance vs Programming Effort between Rust and C on Multicore Architectures: Case Study in
N-Body". XLVII Latin American Computing Conference (CLEI 2021), pages 1--10.
DOI 10.1109/CLEI53233.2021.9640225. (An arXiv preprint exists as 2107.11912. Cite the IEEE
version.)

A matched Rust and C pair on a parallel numerical workload, with development effort measured
alongside run time. Their own finding, quoted: performance "close in double precision, but not in
single precision, where C version was superior", because "Rust does not optimize math operations
as well as C with this data type", concluding that Rust "reduces programming effort while
maintaining acceptable performance levels".

Two reasons it is worth more than a citation swap. It is a **matched pair with an effort
measurement**, so it belongs in the `tab:related` population and in the RQ4 discussion, not only in
the background sentence. And its optimisation sequence includes a step that switches the Rust
build to `jemalloc`, which is an independent instance of an allocator choice being treated as a
performance variable in a two-language comparison, exactly as the fairness controls here treat it.
Be precise about scope when citing: the comparison is Rust against **C**, not C++.

**What this does not settle.** The `Ha_Vien_Mastersthesis_2026.tex`:822 claim is about C++ as well as C, and neither
F.1 nor F.2 is a C++ matched pair on throughput and memory. The bibliography's existing
`suchert2023stamp`, `gonzalez2023rustudp` and `pirelli2023safelowlevel` already carry that side
from three directions. The honest fix is to let those three carry the C++ half and use F.1 and F.2
for the general one, at which point `bugden2022rust` can go.

## G. What to change, ordered by risk

Revised with the sweep. Every anchor named here is 2021 or later except E.1, which is cited as a
standard reference, and the algorithm-origin papers, which appear only in the sentences that name
their algorithms.

1. **`Ha_Vien_Mastersthesis_2026.tex`:3030, the Loom sentence.** Accuracy fix, and the only item in this sweep that
   makes an existing sentence *wrong* rather than merely unsupported. Release/acquire, not C11
   entire. Sound under bounded partial-order reduction, not exhaustive full stop. Cite B.1, with
   TruSt if the draft wants to say what the bound costs in current terms.
2. **`Ha_Vien_Mastersthesis_2026.tex`:3009--3012 and the `tab:faults` `$^{\S}$` footnote.** Attribute the lock-graph
   mechanism to B.5, and the unmaintained-experimental-detector status to B.6. The draft's own
   reasoning survives intact and stops being the only support for its most surprising RQ2 finding.
3. **§`sec:relatedwork` and the RQ4 future work: add RustMC.** A 2026 model checker that verifies
   concurrent Rust *and its FFI dependencies*, evaluated against Loom's own test suite, is the
   single most on-target new source in this sweep and it is four months old. Better volunteered than
   found by an examiner.
4. **§`sec:stats` and §`sec:repro`.** Add E.1 as the standard reference and E.0 (ICPE 2026) for what
   a campaign must record, with E.0b if a second is wanted. E.2 and E.3 only in the two sentences
   named in §E.
5. **§`sec:threats`, the virtualised-host row, §`sec:testbed`, and `bench/TESTBED.md`.** Lead with
   C.4 (*Sensors* 2024, in-domain, and it quantifies what CPU affinity and isolation are worth) and
   C.5 (cRAN, frequency management as the named cause of instability). Add C.6 for the
   sub-millisecond-at-99.999% premise and C.1 for the order of magnitude, minding the framing
   warning there. C.2 is support, not the sole citation.
6. **§`sec:resources` and the RQ3 discussion.** Add D.0 (ISMM 2026) for allocator choice as a
   first-order, currently-studied variable, and D.1 for what an arena is. The 2000-to-2002 cluster
   is superseded and should not be cited unless the replication lineage is being made explicit.
7. **§`sec:relatedwork`, the contrary-results passage.** Add F.0b (ASPLOS 2026), which reports a
   like-for-like C++-to-Rust port at 46% geometric-mean overhead *and* disputes the reading of
   `harris2023morello`, a citation the thesis already carries. Highest-value single item for
   criterion 2.
8. **Background §`sec:cpplatency` and §`sec:relatedwork`, plus the RQ4 discussion.** Retire
   `bugden2022rust`. F.0a and F.0b are the 2026 sources for the C++ side, F.1 upgrades
   `pereira2017energy` to its journal version for the general claim, and F.2 adds a matched pair
   with an effort measurement. F.0a also means the RQ4 future work should stop implying that
   C++-to-Rust migration must be done by hand.
9. **Shuttle's guarantee.** Add B.2 wherever the draft says probabilistic concurrency testing, and
   **B.4** wherever ThreadSanitizer is first named. Both are origin citations for tools the draft
   names, so their dates are appropriate.
10. **Decide E.4 deliberately, either way.** If it goes in, it goes in `tab:threats` as a residual
    the study does not control, and the diagram constraint recorded in sweep 1 §2.5 applies:
    `diagrams/25_threats_validity.drawio` is hand-laid-out, so a table row without a diagram row
    leaves the two inconsistent.

Items 1 and 2 are corrections and should be done regardless. Items 3 to 9 are fills, with 3 and 7
the two that most change how current the bibliography looks. Item 10 is a judgement call.

## H. Negative results, recorded so they are not searched for again

- **Corrected by the re-run: Loom *has* been evaluated in a peer-reviewed paper.** The first version
  of this section claimed no peer-reviewed paper measures Loom or Shuttle as objects of study. That
  was wrong for Loom: RustMC (FORTE 2026) evaluates against the Loom test suite. It remains true for
  Shuttle, which has no paper of its own, only the repository and the account in B.1.
- **Every area of the apparatus turned out to have current work.** Recorded because it is the
  general lesson of the re-run: searching for the founding paper is easy and searching for the
  current one takes a second pass, and in all five areas the second pass produced a source that was
  both newer and closer to the thesis. The allocator area is the clearest case, where the 2002 paper
  has a 2026 replication by one of its own authors that names the thesis's allocator.
- **No peer-reviewed evaluation of the TSan deadlock detector exists.** Searched under lock-order
  inversion, potential deadlock, false negative and detector-effectiveness phrasings. The
  literature covers the *technique* (B.5 and its successors) and the tool's own documentation
  covers the *implementation* (B.6), and nothing joins them. This is why the draft's twelve-repeat
  measurement is worth keeping as a contribution in its own right: it is a small piece of evidence
  about a tool nobody has evaluated.
- **No peer-reviewed source compares Rust's and C++'s standard collections on memory footprint.**
  Searched for open-addressing versus node-based hash-map footprint, `hashbrown`, SwissTable and
  `unordered_map`. The mechanism behind the language half of the peak-RSS result therefore stays
  where it belongs, in the forced-idiom log and the compiled record-size probes of
  `bench/artefact_facts.py`.
- **The general-web result set for cross-language performance is unchanged from sweeps 1 and 3.**
  The 2026 additions are a JetBrains vendor post and two arXiv preprints ("Is Rust C++-fast?",
  2209.09127, and a 2026 multi-language AI-workload benchmark, 2606.18141, which reports Rust
  trailing C and C++ by 9% on a geometric mean and all three staying below 6 MiB). Both are
  preprints, so neither improves on what §F already fixes. Not citable.
- **`bibliography.bib` is clean.** 100 entries, 100 cited, no orphans, no undefined keys. Anything
  added here must be cited or it breaks that.

## I. BibTeX

Every field below was read from the registration agency's own record via
`.bibaudit/verify_candidates.py`, or from the publisher's page for the two items without a DOI.
Titles that ACM splits into `title` and `subtitle` are reassembled here. `urldate` on the `@misc`
entries must be set to the day they are actually cited.

Entries are grouped: the current anchors first, then the algorithm-origin and superseded entries,
which are retained so that nothing has to be re-searched if the lineage argument is wanted.

**Current anchors (2021--2026).**

```bibtex
@inproceedings{pearce2026rustmc,
  author    = {Pearce, Oliver and Lange, Julien and O'Keeffe, Dan},
  title     = {{RustMC}: Automated Verification of Real-World Concurrent {Rust}},
  booktitle = {Formal Techniques for Distributed Objects, Components, and Systems (FORTE 2026)},
  series    = {Lecture Notes in Computer Science},
  pages     = {235--255},
  publisher = {Springer},
  year      = {2026},
  doi       = {10.1007/978-3-032-28187-6_14}
}

@article{kokologiannakis2022trust,
  author  = {Kokologiannakis, Michalis and Marmanis, Iason and Gladstein, Vladimir and
             Vafeiadis, Viktor},
  title   = {Truly Stateless, Optimal Dynamic Partial Order Reduction},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {6},
  number  = {POPL},
  pages   = {1--28},
  year    = {2022},
  doi     = {10.1145/3498711}
}

@inproceedings{vankempen2026allocation,
  author    = {van Kempen, Nicolas and Berger, Emery D.},
  title     = {Reconsidering ``Reconsidering Custom Memory Allocation''},
  booktitle = {Proceedings of the 2026 ACM SIGPLAN International Symposium on Memory Management
               (ISMM '26)},
  pages     = {14--24},
  year      = {2026},
  doi       = {10.1145/3814942.3816132}
}

@article{ocampo2024cloudran,
  author  = {Ocampo, Andres F. and Fida, Mah-Rukh and Elmokashfi, Ahmed and Bryhni, Haakon},
  title   = {Assessing the {Cloud-RAN} in the {Linux} Kernel: Sharing Computing and Network
             Resources},
  journal = {Sensors},
  volume  = {24},
  number  = {7},
  pages   = {2365},
  year    = {2024},
  doi     = {10.3390/s24072365}
}

@inproceedings{abeni2022ranrt,
  author    = {Abeni, Luca and Cucinotta, Tommaso and Pinczel, Bal{\'a}zs and M{\'a}tray, P{\'e}ter
               and Srinivasan, Murali Krishna and Lindquist, Tobias},
  title     = {On the Use of {Linux} Real-Time Features for {RAN} Packet Processing in Cloud
               Environments},
  booktitle = {High Performance Computing. ISC High Performance 2022 International Workshops},
  series    = {Lecture Notes in Computer Science},
  volume    = {13387},
  pages     = {371--382},
  publisher = {Springer},
  year      = {2022},
  doi       = {10.1007/978-3-031-23220-6_26}
}

@inproceedings{foukas2021concordia,
  author    = {Foukas, Xenofon and Radunovic, Bozidar},
  title     = {Concordia: Teaching the {5G} {vRAN} to Share Compute},
  booktitle = {Proceedings of the 2021 ACM SIGCOMM Conference},
  pages     = {580--596},
  year      = {2021},
  doi       = {10.1145/3452296.3472894}
}

@inproceedings{paolillo2026benchkit,
  author    = {Paolillo, Antonio and Van Molle, Mats and Hasselmann, Ken},
  title     = {benchkit: A Declarative Framework for Composable Performance Evaluation of System
               Software},
  booktitle = {Proceedings of the 17th ACM/SPEC International Conference on Performance Engineering
               (ICPE '26)},
  pages     = {170--183},
  year      = {2026},
  doi       = {10.1145/3777884.3796997}
}

@article{papadopoulos2021reproducible,
  author  = {Papadopoulos, Alessandro Vittorio and Versluis, Laurens and Bauer, Andre and
             Herbst, Nikolas and von Kistowski, Joakim and Ali-Eldin, Ahmed and Abad, Cristina L.
             and Amaral, Jose Nelson and Tuma, Petr and Iosup, Alexandru},
  title   = {Methodological Principles for Reproducible Performance Evaluation in Cloud Computing},
  journal = {IEEE Transactions on Software Engineering},
  volume  = {47},
  number  = {8},
  pages   = {1528--1543},
  year    = {2021},
  doi     = {10.1109/TSE.2019.2927908}
}

@article{popescu2026cpp2rust,
  author  = {Popescu, Lucian and Gouveia, Francisco and Preto, Henrique and Silveira, Jo{\~a}o and
             Hrybenko, Dmytro and Fragoso Santos, Jos{\'e} and Lopes, Nuno P.},
  title   = {{Cpp2Rust}: Automatic Translation of {C++} to Safe {Rust}},
  journal = {Proceedings of the ACM on Programming Languages},
  volume  = {10},
  number  = {PLDI},
  pages   = {480--504},
  year    = {2026},
  doi     = {10.1145/3808266},
  note    = {Page form unconfirmed: the authors' PDF cites Article 188, Crossref gives 480--504}
}

@inproceedings{naylor2026cherisimt,
  author    = {Naylor, Matthew and Joannou, Alexandre and Markettos, A. Theodore and
               Metzger, Paul and Moore, Simon W. and Jones, Timothy M.},
  title     = {{CHERI-SIMT}: Implementing Capability Memory Protection in {GPUs}},
  booktitle = {Proceedings of the 31st ACM International Conference on Architectural Support for
               Programming Languages and Operating Systems (ASPLOS '26)},
  pages     = {50--66},
  year      = {2026},
  doi       = {10.1145/3760250.3762234},
  note      = {Year unconfirmed: Crossref's deposit records 2025, the event field ASPLOS '26}
}
```

**Algorithm origins, tool documentation, and superseded entries.** Cite the first four only in the
sentence that names the algorithm or tool. The allocator entries after `evans2006jemalloc` are
superseded by `vankempen2026allocation` and are kept only for the lineage argument.

```bibtex
@inproceedings{bornholt2021shardstore,
  author    = {Bornholt, James and Joshi, Rajeev and Astrauskas, Vytautas and Cully, Brendan and
               Kragl, Bernhard and Markle, Seth and Sauri, Kyle and Schleit, Drew and
               Slatton, Grant and Tasiran, Serdar and Van Geffen, Jacob and Warfield, Andrew},
  title     = {Using Lightweight Formal Methods to Validate a Key-Value Storage Node in
               {Amazon} {S3}},
  booktitle = {Proceedings of the ACM SIGOPS 28th Symposium on Operating Systems Principles
               (SOSP '21)},
  pages     = {836--850},
  year      = {2021},
  doi       = {10.1145/3477132.3483540}
}

@inproceedings{burckhardt2010pct,
  author    = {Burckhardt, Sebastian and Kothari, Pravesh and Musuvathi, Madanlal and
               Nagarakatte, Santosh},
  title     = {A Randomized Scheduler with Probabilistic Guarantees of Finding Bugs},
  booktitle = {Proceedings of the 15th International Conference on Architectural Support for
               Programming Languages and Operating Systems (ASPLOS '10)},
  pages     = {167--178},
  year      = {2010},
  doi       = {10.1145/1736020.1736040}
}

@inproceedings{norris2013cdschecker,
  author    = {Norris, Brian and Demsky, Brian},
  title     = {{CDSchecker}: Checking Concurrent Data Structures Written with {C/C++} Atomics},
  booktitle = {Proceedings of the 2013 ACM SIGPLAN International Conference on Object Oriented
               Programming Systems Languages and Applications (OOPSLA '13)},
  pages     = {131--150},
  year      = {2013},
  doi       = {10.1145/2509136.2509514}
}

@inproceedings{serebryany2009tsan,
  author    = {Serebryany, Konstantin and Iskhodzhanov, Timur},
  title     = {{ThreadSanitizer}: Data Race Detection in Practice},
  booktitle = {Proceedings of the Workshop on Binary Instrumentation and Applications
               (WBIA '09)},
  pages     = {62--71},
  year      = {2009},
  doi       = {10.1145/1791194.1791203}
}

@inproceedings{bensalem2005deadlock,
  author    = {Bensalem, Saddek and Havelund, Klaus},
  title     = {Dynamic Deadlock Analysis of Multi-threaded Programs},
  booktitle = {Hardware and Software, Verification and Testing (Haifa Verification Conference
               2005)},
  series    = {Lecture Notes in Computer Science},
  volume    = {3875},
  pages     = {208--223},
  publisher = {Springer},
  year      = {2005},
  doi       = {10.1007/11678779_15}
}

@misc{tsandeadlock,
  author       = {{The Sanitizers Project}},
  title        = {{ThreadSanitizer} Deadlock Detector},
  howpublished = {Project documentation, google/sanitizers wiki},
  url          = {https://github.com/google/sanitizers/wiki/ThreadSanitizerDeadlockDetector}
}

@article{abeni2020hypervisors,
  author  = {Abeni, Luca and Faggioli, Dario},
  title   = {Using {Xen} and {KVM} as Real-Time Hypervisors},
  journal = {Journal of Systems Architecture},
  volume  = {106},
  pages   = {101709},
  year    = {2020},
  doi     = {10.1016/j.sysarc.2020.101709}
}

@article{gebai2014preemption,
  author  = {Gebai, Mohamad and Giraldeau, Francis and Dagenais, Michel R.},
  title   = {Fine-Grained Preemption Analysis for Latency Investigation across Virtual Machines},
  journal = {Journal of Cloud Computing},
  volume  = {3},
  number  = {1},
  year    = {2014},
  doi     = {10.1186/s13677-014-0023-3}
}

@article{abeni2024virtualized,
  author  = {Abeni, Luca},
  title   = {Virtualized Real-Time Workloads in Containers and Virtual Machines},
  journal = {Journal of Systems Architecture},
  volume  = {154},
  pages   = {103238},
  year    = {2024},
  doi     = {10.1016/j.sysarc.2024.103238}
}

@misc{evans2006jemalloc,
  author       = {Evans, Jason},
  title        = {A Scalable Concurrent \texttt{malloc(3)} Implementation for {FreeBSD}},
  howpublished = {BSDCan 2006, Ottawa},
  year         = {2006},
  month        = apr,
  url          = {https://papers.freebsd.org/2006/bsdcan/evans-jemalloc/}
}

@inproceedings{berger2000hoard,
  author    = {Berger, Emery D. and McKinley, Kathryn S. and Blumofe, Robert D. and
               Wilson, Paul R.},
  title     = {Hoard: A Scalable Memory Allocator for Multithreaded Applications},
  booktitle = {Proceedings of the 9th International Conference on Architectural Support for
               Programming Languages and Operating Systems (ASPLOS '00)},
  pages     = {117--128},
  year      = {2000},
  doi       = {10.1145/378993.379232}
}

@inproceedings{berger2002customalloc,
  author    = {Berger, Emery D. and Zorn, Benjamin G. and McKinley, Kathryn S.},
  title     = {Reconsidering Custom Memory Allocation},
  booktitle = {Proceedings of the 17th ACM SIGPLAN Conference on Object-Oriented Programming,
               Systems, Languages, and Applications (OOPSLA '02)},
  year      = {2002},
  doi       = {10.1145/582419.582421},
  note      = {Page range unconfirmed: Crossref's deposit records the first page only}
}

@inproceedings{johnstone1998fragmentation,
  author    = {Johnstone, Mark S. and Wilson, Paul R.},
  title     = {The Memory Fragmentation Problem: Solved?},
  booktitle = {Proceedings of the 1st International Symposium on Memory Management (ISMM '98)},
  pages     = {26--36},
  year      = {1998},
  doi       = {10.1145/286860.286864}
}

@inproceedings{powers2019mesh,
  author    = {Powers, Bobby and Tench, David and Berger, Emery D. and McGregor, Andrew},
  title     = {Mesh: Compacting Memory Management for {C/C++} Applications},
  booktitle = {Proceedings of the 40th ACM SIGPLAN Conference on Programming Language Design and
               Implementation (PLDI '19)},
  pages     = {333--346},
  year      = {2019},
  doi       = {10.1145/3314221.3314582}
}

@inproceedings{hoefler2015benchmarking,
  author    = {Hoefler, Torsten and Belli, Roberto},
  title     = {Scientific Benchmarking of Parallel Computing Systems},
  booktitle = {Proceedings of the International Conference for High Performance Computing,
               Networking, Storage and Analysis (SC '15)},
  pages     = {1--12},
  year      = {2015},
  doi       = {10.1145/2807591.2807644}
}

@inproceedings{kalibera2013benchmarking,
  author    = {Kalibera, Tomas and Jones, Richard},
  title     = {Rigorous Benchmarking in Reasonable Time},
  booktitle = {Proceedings of the 2013 International Symposium on Memory Management (ISMM '13)},
  pages     = {63--74},
  year      = {2013},
  doi       = {10.1145/2464157.2464160}
}

@inproceedings{mytkowicz2009bias,
  author    = {Mytkowicz, Todd and Diwan, Amer and Hauswirth, Matthias and Sweeney, Peter F.},
  title     = {Producing Wrong Data without Doing Anything Obviously Wrong!},
  booktitle = {Proceedings of the 14th International Conference on Architectural Support for
               Programming Languages and Operating Systems (ASPLOS '09)},
  pages     = {265--276},
  year      = {2009},
  doi       = {10.1145/1508244.1508275}
}

@inproceedings{curtsinger2013stabilizer,
  author    = {Curtsinger, Charlie and Berger, Emery D.},
  title     = {{STABILIZER}: Statistically Sound Performance Evaluation},
  booktitle = {Proceedings of the 18th International Conference on Architectural Support for
               Programming Languages and Operating Systems (ASPLOS '13)},
  pages     = {219--228},
  year      = {2013},
  doi       = {10.1145/2451116.2451141}
}

@article{pereira2021energy,
  author  = {Pereira, Rui and Couto, Marco and Ribeiro, Francisco and Rua, Rui and
             Cunha, J{\'a}come and Fernandes, Jo{\~a}o Paulo and Saraiva, Jo{\~a}o},
  title   = {Ranking Programming Languages by Energy Efficiency},
  journal = {Science of Computer Programming},
  volume  = {205},
  pages   = {102609},
  year    = {2021},
  doi     = {10.1016/j.scico.2021.102609}
}

@inproceedings{costanzo2021rustc,
  author    = {Costanzo, Manuel and Rucci, Enzo and Naiouf, Marcelo and De Giusti, Armando},
  title     = {Performance vs Programming Effort between {Rust} and {C} on Multicore
               Architectures: Case Study in {N-Body}},
  booktitle = {2021 XLVII Latin American Computing Conference (CLEI)},
  pages     = {1--10},
  year      = {2021},
  doi       = {10.1109/CLEI53233.2021.9640225}
}
```

Two notes on entry types, following the convention set in sweep 1. `evans2006jemalloc` and
`tsandeadlock` are not peer-reviewed and the prose must say so where they are used, not only the
entry type. And `IEEEtran` renders `@misc` without the emphasis `@techreport` receives, so check
both in the compiled PDF before settling on the type.

---

# Fifth sweep, 19 August 2026 — adoption in industries that already had to decide

> **Status: candidates only. Nothing in this sweep has been applied.**
>
> **Repository note.** The canonical source is now `Ha_Vien_Mastersthesis_2026.tex`, renamed from
> `Thesis_POC.tex`. `bench/refresh_thesis.sh` was updated with the rename, but `AGENT.md`,
> `README.md` and `.cursor/rules/thesis-quality.mdc` still refer to `Thesis_POC.tex` throughout.
> Line references in the earlier sweeps in this file point at the old filename and are otherwise
> still valid.

The first four sweeps covered the argument, the domain, the research gap and the measurement
apparatus. This one goes after a question the thesis asks but does not source: what it costs a
process-heavy organisation to adopt Rust. §"Engineering guidelines for incremental adoption" carries
four citation groups and all four are about `unsafe` and interoperability. Nothing in it cites the
industries that have already had to answer the adoption question formally, which are the
certification-centric ones.

**The limit on this area, stated before the sources rather than after.** RAN control-plane software
is not certified to ISO 26262, IEC 61508 or DO-178C, and nothing below should be cited as though it
were. What transfers is the *adoption-cost reasoning* and the compile-time-versus-process argument.
The criticality levels do not transfer, and a sentence implying that they do would be a worse
over-claim than anything the thesis currently contains.

## A. Sommer et al., SE 2025 companion proceedings — VERIFIED, and refereed

"Viability of Rust for Avionics Software Development -- Current status and way forward". Jan Sommer,
Tamara Gutierrez Rojo, Andreas Lund, Hany Ibrahim Erfan Abdelmaksoud, Daniel Lüdtke (DLR Institute
of Software Technology). *Software Engineering 2025, Companion Proceedings*, Gesellschaft für
Informatik, Bonn. DOI 10.18420/se2025-ws-08. Presented at the 7th Workshop on Avionics Systems and
Software Engineering, Karlsruhe, 25 February 2025. The DLR repository record states "Refereed
publication: Yes", which is worth noting because a workshop paper in a companion volume would
otherwise be assumed not to be.

**The single most useful find in this sweep, and it is useful for an unobvious reason.** Its
contribution is a list of six requirements a new language must satisfy to justify its adoption cost
in a C-dominated, certification-centric industry, and two of them are the thesis's own scoping
decisions, argued independently and published.

- **REQ3 is the managed-language exclusion.** Performance "should also be stable, which generally
  rules out garbage-collected languages, since the garbage collector produces hard-to-predict
  delays." `Ha_Vien_Mastersthesis_2026.tex`:845--853 makes exactly this argument and supports it
  with `dean2013tail` plus the thesis's own reasoning. This is a second, independent, refereed
  statement of it from another latency-critical domain. **Highest-value single citation in the
  sweep**, because it converts a scoping decision an examiner could call arbitrary into one that
  another field reached separately.
- **REQ2 is the C-ABI seam.** The authors note that the C++ ABI "is undefined and compiler
  specific. However, it is possible to call Rust functions from C++ using the C calling
  conventions. This allows for a gradual introduction of Rust into small parts of an existing code
  base." That is RQ4's premise and the seam design of §`sec:interop`, stated by others.

Three further details are worth a clause each. The paper records that the AUTOSAR consortium has
started a Rust working group and published API bindings, that AdaCore and Ferrous Systems offer
qualified compilers, and that ESA has funded several Rust activities. It is also candid about the
gap: at the time of writing "there is currently no qualification to a relevant aerospace standard
such as DO-178C or ECSS". Cite the candour along with the rest, because it is what makes the paper
usable rather than promotional.

## B. The Rust Project's own account — VERIFIED as a project statement, not peer-reviewed

"What does it take to ship Rust in safety-critical?" Rust Blog, 14 January 2026.
<https://blog.rust-lang.org/2026/01/14/what-does-it-take-to-ship-rust-in-safety-critical/>

One sentence in it is the thesis's central argument in the Rust Project's own words: much of what
was historically process-based enforcement through coding standards such as MISRA C and CERT C
becomes a property checked by the compiler instead of by external static analysis or manual review.
The thesis argues precisely this contrast, between a guarantee the compiler enforces and detection
after the fact, and it argues it in its own voice throughout Chapter 2 and §`sec:rqdiscussion`.

The same post is unusually honest about the limits, which is what makes it citable rather than
promotional: "once you move beyond prototyping into the higher-criticality parts of a system, the
ecosystem support thins out fast", there is no Simulink code generation for Rust, and there is no
AUTOSAR-Classic-compatible RTOS written in Rust. It also records production deployment at IEC 61508
SIL 2 in mobile robotics and IEC 62304 Class B in medical devices.

**One further use, and it is a gap in the thesis rather than a bonus.** The post records that the
Ferrocene Language Specification began as an industry effort to make the compiler qualifiable and
now has a maintained home under the Rust Project, with a team created in 2025. The thesis carries a
careful paragraph on WG21 profiles because C++ is changing under its feet (sweep 1 §2). The mirror
of that paragraph is that the standard objection to Rust in this setting, that it has no
specification, has an answer as of 2025. The thesis pins its comparison to C++23 as a *standard*
and says nothing about whether its other arm has one. An examiner who knows the C++ side will know
the Rust side too.

## C. Ferrocene — VERIFIED as vendor documentation, one field PARTIAL and it matters

<https://ferrocene.dev/> and the release announcement for Ferrocene 26.02.0 at
<https://ferrous-systems.com/blog/ferrocene-26-02-0/>

A TÜV SÜD-qualified downstream Rust toolchain, open source under MIT or Apache-2.0 including the
qualification documents. The certified subset of `core` grew from 2,903 to 5,169 functions in the
February 2026 release, covering `core::slice`, `core::iter`, `core::ffi` and `core::result`.

**PARTIAL, and do not paper over it.** The qualification level is reported inconsistently across
primary sources. The vendor's own site and its February 2026 release post say ISO 26262 (ASIL D),
IEC 61508 (**SIL 3**), IEC 62304 (Class C), with support for customer certification *toward* IEC
61508 SIL 4 and DO-178C (DAL C). The project's own GitHub README says IEC 61508 (**SIL 4**), and
secondary coverage repeats SIL 4. Cite the conservative form, meaning SIL 3 qualified with SIL 4
supported, or verify against the current certificate before quoting a level at all.

Not peer-reviewed. Use it for existence and for dates, never as evidence of an effect.

## D. Zaeske et al., MC/DC for Rust — VERIFIED as a preprint, venue unconfirmed

"Towards Modified Condition/Decision Coverage of Rust". Wanja Zaeske, Pietro Albini, Florian
Gilcher, Umut Durak. arXiv 2409.08708, September 2024. Author affiliations span Ferrous Systems and
DLR.

Establishes that MC/DC, which DO-178C mandates at Level A, needed interpretive clarification for
Rust's pattern matching, and that no Rust-compatible MC/DC or even decision-coverage tool existed.
Read against §B above, which records that earlier MC/DC work in `rustc` stalled and is being
restarted through the Safety-Critical Rust Consortium as a 2026 Rust Project Goal, the two together
give a precise and dated account of one concrete tooling gap.

**Venue unconfirmed.** The formatting suggests an LNCS-style workshop or conference paper. Check
Ada-Europe and SAFECOMP before citing, and cite the preprint with a note if nothing is found. This is
optional material in any case: it matters only if the thesis chooses to discuss certification
tooling, which it currently does not.

## E. RQ4's learning cost: an upgrade in evidence quality, not in recency

### E.1 Coblenz, Mazurek and Hicks, ICSE 2022 — VERIFIED

"Garbage collection makes Rust easier to use: a randomized controlled trial of the Bronze garbage
collector". Michael Coblenz, Michelle L. Mazurek, Michael Hicks. ICSE 2022, pages 1021--1032.
DOI 10.1145/3510003.3510107. (Crossref splits the subtitle.)

A **randomised controlled trial** with 428 participants drawn from a 633-person class. On a task
requiring management of complex aliasing, participants using a library garbage collector were more
likely to finish in the time available, and those who did needed about a third of the time, four
hours against twelve. Surveys identified ownership, borrowing and lifetimes as the primary causes of
difficulty.

**Why this is worth adding even though it is 2022.** The thesis's learning-curve claim currently
rests on an interview and survey study~(`fulton2021adopting`), a study of learning
materials~(`crichton2024learning`) and a verbosity analysis~(`ardito2021verbosity`). Not one of them
is a controlled experiment. This is, the effect size is a factor of three, and the mechanism it
isolates is the same one the thesis names. Recency is the wrong axis here: an RCT from 2022 is
stronger evidence about the concepts than a survey from 2026 would be.

**State the caveat in the same sentence.** The participants were students, not professional systems
engineers, so the result bounds the difficulty of the *concepts* and says nothing about the ramp-up
time of a RAN team. Without that clause the citation over-claims.

It also pairs with `hughes2025gcrust`, already on record from sweep 3 §C.5. Both are about what
Rust's lack of a garbage collector costs, one in developer effort and one in data-structure
expressiveness, and together they support the reference-cycle-leak boundary class, which is one of
the two where the C++ tooling came back ahead.

## F. Where these go

1. **Background, the managed-language exclusion at `Ha_Vien_Mastersthesis_2026.tex`:845--853.** Add
   Sommer et al. Cheapest and highest-value item in the sweep, one citation, and it shores up a
   scoping decision currently carried by `dean2013tail` and the thesis's own argument.
2. **§"Engineering guidelines for incremental adoption".** The section has no citation on the
   process or qualification side. Sommer et al.'s requirement list and the
   MISRA-becomes-compiler-checked framing from §B are the two to add, with the domain caveat above
   stated explicitly.
3. **§`sec:interop`.** Sommer et al. on the undefined C++ ABI and gradual adoption through the C
   calling convention, alongside the RustMC sentence added from sweep 4.
4. **RQ4 discussion.** Coblenz et al. as controlled evidence on the learning cost, with the
   student-population caveat.
5. **Optional, and a judgement call.** The Ferrocene Language Specification as the mirror of the
   C++ profiles paragraph. Worth one sentence if the author wants the treatment of the two languages
   to be symmetric on the question of specification and qualification. Skip it if the chapter is
   already long.

## G. Negative results

- **The open item from sweep 3 cannot be closed by an agent, and this is now confirmed rather than
  assumed.** DiVA sits behind Anubis proof-of-work anti-scraping, so Emberg & Wadsten
  (`emberg2023asn1`) and Olsson & Stenström (`olsson2023asyncpackets`) cannot be fetched
  programmatically. Both are open access at the URNs recorded in sweep 3 §F and the author can
  download them directly. Until then the absence claims in §`sec:gap` and §`sec:relatedwork`, that
  neither reports tail behaviour past saturation and that neither holds a concurrency model fixed,
  still rest on abstracts. This remains the highest-risk unresolved item in the whole literature
  record, because an examiner with the PDFs can check it in an afternoon.
- **No peer-reviewed work on Rust in telecom certification exists.** The certification literature
  covers aerospace, automotive, industrial and medical. RAN does not appear, which is consistent
  with the thesis's own gap claim and is worth one sentence rather than a search.
- **The 2026 web result set on Rust onboarding cost is machine-generated SEO content, and it is
  dangerous rather than merely useless.** Several pages quote figures precise enough to look
  citable: $18,700 onboarding cost per engineer, an "O'Reilly 2024 Startup Engineering Survey" of
  1,200 teams, "72% of Series A startups" attributed to Gartner, and a 4-to-6-month ramp at 30%
  reduced productivity. None could be traced to a real publication. Recorded here so that a future
  sweep does not mistake the specificity for evidence.
- **Fulton et al.'s underlying dissertation** ("Understanding and Improving Secure Development from
  a Human-Centered Perspective", DOI 10.13016/dspace/u2ca-otbw) carries a longer drawback list than
  the paper the thesis cites: dependency bloat, slow compile times, hiring concerns, and the
  observation that much of the adoption cost falls up front while the benefits accrue later and less
  certainly. That last framing is the most useful sentence in the human-factors literature for RQ4.
  Check whether it also appears in `fulton2021adopting` and attribute it there if so, rather than
  adding a dissertation to the bibliography for one sentence.

## H. BibTeX

```bibtex
@inproceedings{sommer2025avionics,
  author    = {Sommer, Jan and Gutierrez Rojo, Tamara and Lund, Andreas and
               Abdelmaksoud, Hany Ibrahim Erfan and L{\"u}dtke, Daniel},
  title     = {Viability of {Rust} for Avionics Software Development: Current Status and Way
               Forward},
  booktitle = {Software Engineering 2025, Companion Proceedings},
  publisher = {Gesellschaft f{\"u}r Informatik},
  address   = {Bonn},
  year      = {2025},
  note      = {7th Workshop on Avionics Systems and Software Engineering (AvioSE), Karlsruhe},
  doi       = {10.18420/se2025-ws-08},
  url       = {https://doi.org/10.18420/se2025-ws-08}
}

@inproceedings{coblenz2022bronze,
  author    = {Coblenz, Michael and Mazurek, Michelle L. and Hicks, Michael},
  title     = {Garbage Collection Makes {Rust} Easier to Use: A Randomized Controlled Trial of the
               {Bronze} Garbage Collector},
  booktitle = {Proceedings of the 44th International Conference on Software Engineering (ICSE)},
  pages     = {1021--1032},
  year      = {2022},
  doi       = {10.1145/3510003.3510107},
  url       = {https://doi.org/10.1145/3510003.3510107}
}

@misc{rustproject2026safetycritical,
  author       = {{The Rust Project}},
  title        = {What Does It Take to Ship {Rust} in Safety-Critical?},
  howpublished = {Rust Blog},
  year         = {2026},
  month        = jan,
  url          = {https://blog.rust-lang.org/2026/01/14/what-does-it-take-to-ship-rust-in-safety-critical/}
}

@misc{ferrocene,
  author       = {{Ferrous Systems}},
  title        = {Ferrocene: A Qualified {Rust} Toolchain for Safety-Critical Development},
  note         = {Release 26.02.0. Qualified by T{\"U}V S{\"U}D for ISO 26262 (ASIL D),
                  IEC 61508 (SIL 3) and IEC 62304 (Class C). Accessed August 2026},
  url          = {https://ferrocene.dev/},
  year         = {2026}
}

@misc{zaeske2024mcdc,
  author       = {Zaeske, Wanja and Albini, Pietro and Gilcher, Florian and Durak, Umut},
  title        = {Towards Modified Condition/Decision Coverage of {Rust}},
  howpublished = {arXiv:2409.08708 [cs.SE]},
  year         = {2024},
  note         = {Venue unconfirmed at the time of the sweep},
  url          = {https://arxiv.org/abs/2409.08708}
}
```

Entry-type note, same as the earlier sweeps. `rustproject2026safetycritical`, `ferrocene` and
`zaeske2024mcdc` are not peer-reviewed, and the prose must say so where each is used. Of the five,
only `sommer2025avionics` and `coblenz2022bronze` can carry an argument on their own.

---

# Sixth sweep, 24 August 2026: does anyone else reach these conclusions?

> **Status: items 1 and 2 of §I applied, 24 August 2026.** Four entries added to
> `bibliography.bib`, which is now 109 entries with every one cited and no orphans:
> `lu2008mistakes`, `dietz2015overflow`, `cui2024rcanary`, `clangtidyuseaftermove`. Each is cited
> once, at the sentence it supports, in §`sec:safetyresults` and §`sec:rqdiscussion`. A new
> `\paragraph{Replication status}` closes §`sec:threats`, and the `Thesis_v2.tex` threats bullet now
> records that no peer-reviewed study reports the overload reversal. Both PDFs rebuild with zero
> errors and no undefined references or citations, and `.aitells.py` still reports four dash hits
> (the same legitimate four) and no semicolons. Declared length is unchanged at **108 pages**:
> rebuilding a reverted copy gives 108 as well, so this prose costs no page, and the 105 recorded in
> `AGENT.md` predates the same day's RQ2 catalogue work. Items 3 to 7 of §I are open and §F is
> untouched.
>
> The sweep asked one question of each result the thesis reports, and the answer differs sharply
> between them. Eleven additions are proposed and every field was read from a primary record. Three
> findings have no independent twin at all, which is a result in itself and belongs in the threats
> section rather than being quietly left as an absence.

## A. The question, and why it is not the question the first five sweeps asked

Sweeps 1 to 5 asked what would improve the argument: better sources, newer sources, sources for
claims carried by assertion. This sweep asks something narrower and more adversarial. **For each
conclusion the thesis states, has anybody published the same conclusion?** A finding no one has
reproduced is not thereby wrong, but the thesis has to say which of its results stand alone,
because an examiner reading Chapter 8 will ask exactly this.

Indexes queried: OpenAlex (`title_and_abstract.search`), DBLP, Crossref for verification,
Semantic Scholar for abstracts, and the general web. Three method notes, the third new:

1. **Sweep 3's warning holds and got worse.** Free-text `rust` in OpenAlex returns plant pathology
   and corrosion metallurgy above the language. `use-after-move` as a phrase returns 49,542 hits,
   led by vaccine suspension and frailty-scale papers, because the index splits it into common
   words.
2. **DBLP searches titles only and ANDs word prefixes.** `rust mutex`, `rust atomicity` and
   `memory allocator empirical study` all return zero, not because nothing exists but because no
   title carries every word. One distinctive term per query is the only reliable form.
3. **New: DBLP's publication API rate-limits at roughly one query in four seconds**, answering
   HTTP 429 and then closing connections without response for the rest of a batch. Any scripted
   sweep needs a delay and a backoff or it silently reports emptiness as absence.

## B. Verdict, one line per result

| # | Result | Corroboration | Best external witness |
| --- | --- | --- | --- |
| 1 | Median parity below saturation | **Strong.** Four independent studies, all already cited | `li2021ipc` (4 to 8%), `gonzalez2023rustudp` (+0.19%), `sundvisson2026drivers` (0.178%), `okawa2024ruststudy` |
| 2 | The handoff owns the end-to-end cost, the language is a fraction of a percent | **Strong for the mechanism.** Already cited | `zhou2025oltp` |
| 3 | The operation measured alone is $\BudgetCoreRatio\times$ faster in Rust, because of map layout | **Mechanism now sourceable, result not reproduced** | C.8 below, plus the two languages' own normative documents |
| 4 | Overload divergence, $\OverloadThrRatio\times$ throughput and $\OverloadCpuPerOpRatio\times$ CPU per completed operation | **No twin.** The regime and the signature are well studied, the language ordering is not | C.4 to C.6 for the regime, `arvidsson2025async` for the ordering, and it is grey literature |
| 5 | Seven in-guarantee classes rejected at compile time | **Strong.** Already cited | `qin2020rust`, `xu2021rustcve`, `andersson2026stdmemsafety` |
| 6 | Seven boundary classes compile and misbehave | **Strong, class by class, and mostly uncited** | C.1 (lost update), C.2 (overflow), C.3 (leak), C.10 (blast radius), C.9 (use-after-move caveat) |
| 7 | Rust carries $\RssLangDiffLo$ to $\RssLangDiffHi$ MiB more peak RSS | **Weak.** Three grey instances agree, one grey disagrees, and a PLDI 2026 paper reports no difference | `olsson2023ranmgmt`, `sundvisson2026drivers`, against `karlback2021ran` and E.1 |
| 8 | The allocator effect is the larger one | **Partial.** Allocator choice is a studied first-order variable. The ratio is not corroborated | van Kempen and Berger, ISMM 2026, and it is still not in the bibliography |
| 9 | The seam tax is bounded at $\FfiOpBoundPct\%$ | **No twin.** The thesis's own A/B remains the best evidence | Sweep 1 §6.3 already rejected the only circulating figure |
| 10 | Build time: most of the Rust clean build is third-party, first-party source is cheaper than g++ | **No twin, and the web set is actively dangerous** | See §G |
| 11 | The dependency surface is the thing to audit | **Strong, and newly citable** | C.7 |

Read the table as three groups. Results 1, 2, 5 and 6 are instances of published patterns, and the
thesis should say so rather than presenting them as discoveries. Results 3, 7 and 8 have partial
support where the mechanism is known but the measurement is not reproduced. Results 4, 9 and 10 are
the thesis's own, unreplicated, and two of them are its headline contributions.

## C. Proposed additions, all verified against a primary record

### C.1 Lu, Park, Seo and Zhou, ASPLOS 2008 -- VERIFIED

"Learning from Mistakes: A Comprehensive Study on Real World Concurrency Bug Characteristics".
ASPLOS 2008, pages 329-339. DOI 10.1145/1346281.1346323. Crossref record read, abstract read in
full.

105 concurrency bugs from MySQL, Apache, Mozilla and OpenOffice. The finding that matters here,
quoted from the abstract: "around one third of the examined non-deadlock concurrency bugs are
caused by violation to programmers' order intentions, which may not be easily expressed via
synchronization primitives like locks and transactional memories". A second one is directly about
detection: "around 34% of the examined non-deadlock concurrency bugs involve multiple variables,
which are not well addressed by existing bug detection tools".

**Why the thesis needs it.** The `lost_update` boundary class is currently defended by the
thesis's own reasoning: every access is correctly synchronised, so there is no unsynchronised
access for ThreadSanitizer to find and nothing for the borrow checker to reject. This is a
canonical, heavily cited paper saying that a third of real concurrency bugs are of exactly that
shape, and that they are not expressible as a locking discipline. It converts the thesis's most
easily doubted RQ2 row into an instance of a documented category. Cite it in §`sec:faultcat`
beside `natella2016fault` and in the RQ2 discussion where the lost update is explained.

**Caveat to state in the same sentence.** The sample is 2008-era C and C++ desktop and server
software, so it establishes the category and not its present-day frequency.

### C.2 Dietz, Li, Regehr and Adve, TOSEM 2015 -- VERIFIED

"Understanding Integer Overflow in C/C++". *ACM Transactions on Software Engineering and
Methodology* 25(1), 2015. DOI 10.1145/2743019. **One field to settle before use: Crossref's
deposit gives pages 1-29 while the journal numbers it as an article. Check the venue's expected
form.**

From the abstract: "intentional uses of wraparound behaviors are more common than is widely
believed", with "over 200 distinct locations in the SPEC CINT2000 benchmarks where overflow
occurs", and, orthogonally, "overflows are found in both well-defined and undefined flavors" with
applications having "been broken by improvements in compiler optimizations".

**Why the thesis needs it.** The `integer_overflow` row is one of the two boundary classes where
the C++ tooling came back ahead, and the thesis's own framing is that Rust *defines* release-mode
wrapping while C++ leaves signed overflow undefined, which is why UndefinedBehaviorSanitizer has
something to report. Dietz et al. is the peer-reviewed source for both halves of that: wrapping is
often deliberate, so a checker cannot treat every overflow as a bug, and undefined overflow has
broken real programs when optimisers improved. It also justifies why the class belongs in a defect
catalogue at all rather than being dismissed as a contrived case.

### C.3 Cui, Xu, Tian and Zhou, TSE 2024 -- VERIFIED

"rCanary: Detecting Memory Leaks Across Semi-Automated Memory Management Boundary in Rust". *IEEE
Transactions on Software Engineering* 50(9), pages 2472-2484, 2024. DOI 10.1109/TSE.2024.3443624.
Crossref and OpenAlex records read, abstract read in full.

The abstract states the thesis's own `leak_cycle` conclusion in the authors' words. Rust's
ownership model "is anticipated to eliminate memory leaks. However, we observed that user
intervention drives it into semi-automated memory management and makes it error-prone to cause
leaks. In contrast to violating memory-safety guarantees restricted by the `unsafe` keyword, **the
boundary of leaking memory is implicit, and the compiler would not emit any warnings for
developers**." Applied to more than 1,200 real crates, it found 19 with leaks.

**Why this is the single best find in the sweep.** The reference-cycle leak is the boundary class
an examiner is most likely to call artificial, and this is a 2024 journal paper whose entire
premise is that the class is real, silent and common enough to be worth a static checker. It also
supplies the exact framing the thesis wants: the leak boundary is implicit, where the `unsafe`
boundary is marked. Cite it in §`sec:faultcat`, in the RQ2 discussion where LeakSanitizer catches
what Rust misses, and in the future-work sentence about tooling, since rCanary is the Rust-side
answer the thesis notes is missing. It pairs with `hughes2025gcrust` exactly as sweep 5 §E.1
predicted.

### C.4 Mogul and Ramakrishnan, TOCS 1997 -- VERIFIED

"Eliminating receive livelock in an interrupt-driven kernel". *ACM Transactions on Computer
Systems* 15(3), pages 217-252, 1997. DOI 10.1145/263326.263335.

**This is the name for the thesis's overload signature.** §7.5.3 reports that past saturation the
slower variant "is not simply doing less work", drawing $\OverloadCpuPerOpRatio$ times the CPU per
completed operation, and calls that "the signature of effort spent without completing anything".
Livelock is the established term for a system that consumes CPU making no progress under offered
load beyond its capacity, and this is the paper that named and measured it. Using the standard
term, with its citation, moves the sentence from an observation the reader has to accept to a
recognised failure mode the measurement instantiates.

**Scope caveat.** The mechanism there is interrupt handling in a kernel, not a bounded queue in
user space. Cite it for the phenomenon and the term, not as a claim about the same cause.

### C.5 Welsh, Culler and Brewer, SOSP 2001 -- VERIFIED

"SEDA: An Architecture for Well-Conditioned, Scalable Internet Services". SOSP 2001, pages
230-243. DOI 10.1145/502034.502057.

The reference point for why a load sweep must continue past the knee: a service that is
well-behaved below saturation degrades in a qualitatively different way above it, and the
architecture rather than the code determines which way. Supports the methodological choice in
§`sec:workload` that the thesis currently argues from first principles, and it supports the
guideline in §8.5 that says to sweep past the point where the service stops coping.

### C.6 Cho et al., OSDI 2020 and NSDI 2023 -- VERIFIED

- "Overload Control for µs-scale RPCs with Breakwater". Inho Cho, Ahmed Saeed, Joshua Fried, Seo
  Jin Park, Mohammad Alizadeh, Adam Belay. OSDI 2020, pages 299-314. No DOI, USENIX page live at
  <https://www.usenix.org/conference/osdi20/presentation/cho>.
- "Protego: Overload Control for Applications with Unpredictable Lock Contention". Inho Cho,
  Ahmed Saeed, Seo Jin Park, Mohammad Alizadeh, Adam Belay. NSDI 2023, pages 725-738. No DOI,
  USENIX page live at <https://www.usenix.org/conference/nsdi23/presentation/cho>.

Two papers from the same group establishing that microsecond-scale services need explicit overload
control, which is to say that the regime past saturation is a first-class engineering condition and
not an edge case. Protego is the more useful of the two here because its subject is overload whose
severity depends on **lock contention inside the application**, which is the shape of the thesis's
own result: the divergence did not reproduce when the queue and the completion handle were isolated,
so it lives in the wider handoff path.

**What they do not do, and the prose must not imply otherwise.** Neither compares languages.
They corroborate that the thesis was right to sweep into overload and right to treat the far side
as a separate regime. The language ordering it found there remains uncorroborated.

### C.7 Hejderup et al., EMSE 2022, and Soto-Valero et al., EMSE 2021 -- VERIFIED

- "Präzi: from package-based to call-based dependency networks". Joseph Hejderup, Moritz Beller,
  Konstantinos Triantafyllou, Georgios Gousios. *Empirical Software Engineering* 27(5), 2022.
  DOI 10.1007/s10664-021-10071-9. **Crossref's deposit carries no page range, so cite by article
  number after checking it.**
- "A comprehensive study of bloated dependencies in the Maven ecosystem". César Soto-Valero,
  Nicolas Harrand, Martin Monperrus, Benoit Baudry. *Empirical Software Engineering* 26(3), 2021.
  DOI 10.1007/s10664-020-09914-8.

Präzi is the on-target one and it is about **Rust**: a function-level dependency network for
crates.io, whose headline result is that "packages call only 40% of their resolved dependencies".
That is peer-reviewed evidence for the RQ4 axis the thesis measures as $\BuildDepShareCpu\%$ of the
clean build being third-party code, and it strengthens the guideline that an organisation worried
about build time or footprint "should audit its dependency budget before blaming the compiler".
Soto-Valero et al. quantify the same thing in a different ecosystem, finding 57% of transitive
dependencies bloated and reduction to a quarter of the declared count feasible, and they are the
citation for treating dependency surface as a measurable cost rather than a complaint.

### C.8 Richter, Alvarez and Dittrich, PVLDB 2015 -- VERIFIED

"A seven-dimensional analysis of hashing methods and its implications on query processing".
*Proceedings of the VLDB Endowment* 9(3), pages 96-107, 2015. DOI 10.14778/2850583.2850585.

The mechanism support for result 3 in §B. From the abstract: picking a scheme and hash function
combination "may have considerable impact on insert and lookup performance, as well as memory
footprint", and the study explicitly examines "the effect of table memory layout and the use of
SIMD instructions".

**Why it is worth adding despite being a database paper.** §7.5.2 attributes the operation-level
gap to "the standard hash map's layout, not anything about safety", and that attribution currently
has no support of any kind. This paper is the peer-reviewed statement that layout choice between
chained and open-addressing schemes is a first-order performance factor. The rest of the mechanism
is documentable from normative sources rather than research: the C++ standard's bucket interface
and its reference-stability guarantees effectively require node-based separate chaining for
`std::unordered_map`, while Rust's `HashMap` has been a SwissTable-style open-addressing table with
SIMD probing since 1.36. Stated that way, the operation-level difference is an artefact of what the
two standard libraries are required to be, which is the same argument the fairness controls already
make about hashing in §`sec:fairness`, and it is emphatically not a safety effect.

**Do not overstate it.** It does not compare the two standard libraries, and sweep 4 §H recorded
that no source does. It supports the claim that layout matters, not the measured factor.

### C.9 clang-tidy `bugprone-use-after-move` documentation -- VERIFIED as tool documentation

<https://clang.llvm.org/extra/clang-tidy/checks/bugprone/use-after-move.html>, read 24 August 2026.

`use_after_move` is the one in-guarantee class no C++ sanitiser reports, and `AGENT.md` requires
the clang-tidy caveat wherever that is quoted. The caveat can now be cited rather than asserted,
and in the tool's own words: the check "currently only considers calls of `std::move` on local
variables or function parameters. It does not check moves of member variables or global variables",
it is flow-sensitive but not path-sensitive, and it flags a use-after-move even on types that
define no move operations, deliberately. Cite as project documentation exactly as `tsandeadlock` is
cited, and keep the sentence's claim to what the tool documents about itself.

### C.10 Candea and Fox, HotOS 2003 -- VERIFIED

"Crash-Only Software". George Candea, Armando Fox. HotOS IX, 2003, pages 67-72. No DOI, USENIX
page live at <https://www.usenix.org/conference/hotos-ix/crash-only-software>.

The `worker_failure_blast_radius` boundary class asks what a panicking worker takes down with it,
and the answer, a shard outage, is currently presented without reference to the reliability
literature that made failure-domain size a design variable. Crash-only software is the canonical
statement of the position that components should fail fast and be restartable, which is precisely
what the thesis's result says neither language gives you for free. Convenient bonus: George Candea
is already in the bibliography through `pirelli2023safelowlevel`, so the addition sits inside
existing lineage rather than opening a new one.

## D. Where the thesis stands alone, stated plainly

These three should be written into §`sec:threats` as replication status, not left as silence.

1. **The overload divergence.** No peer-reviewed study, in any venue, reports a load-dependent
   reversal between Rust and C++, and the general-web synthesis for the question returns the
   opposite prior: that no evidence supports Rust collapsing under load relative to C++. The one
   study reporting the same shape, `arvidsson2025async`, is a master's thesis, and it attributes
   the shape to stackless `async`, which the thesis's design excludes. Directional support from
   peer-reviewed work exists but is weaker than it looks: `suchert2023stamp` finds idiomatic safe
   Rust slower on concurrent transactional workloads, and `naylor2026cherisimt` reports 46%
   geometric-mean overhead on a like-for-like port with 34% from bounds checking. Both are about
   overhead in general, not about behaviour past saturation. **This is the thesis's most original
   result and also its least corroborated, and those two facts should appear in the same
   sentence.**
2. **The build-time decomposition.** Nothing peer-reviewed measures Rust against C++ on build
   time. See §G for why the web result set is worse than useless here.
3. **The ten-to-one split between the allocator and language effects on peak RSS.** The allocator
   half is supported as a first-order variable by ISMM 2026. The language half has three grey
   instances agreeing on sign and two published data points against it. The ratio itself is
   uncorroborated, which is consistent with the thesis's own position that the effect is
   established without being explained, and that position should stay.

## E. Contrary results found in this sweep

### E.1 Popescu et al., PLDI 2026, on peak memory -- VERIFIED, and it cuts against result 7

The Cpp2Rust paper that sweep 4 §F.0a already recommended for a different reason reports, in its
evaluation of WOFF2: "there are no meaningful differences in terms of peak memory consumption",
with a slight reduction after an optimiser pass removes reference counters, "which is expected
since using `Rc` incurs in additional heap allocations".

Scope limits the damage and should be stated when it is cited. The Rust side is machine-translated
rather than hand-written, it is two programs, and the translation inserts runtime ownership checks
that a hand-written core does not have. But it is a 2026 PLDI paper reporting no peak-memory
difference on a matched C++ and Rust pair, and criterion 2 is graded on naming results like this
rather than on collecting agreement. It belongs next to `karlback2021ran` in the contrary-results
passage, and the honest summary of the literature is then: on peak RSS the published record is
mixed, three grey studies agree with the sign found here, one grey study and one PLDI paper do not,
and none of the five isolates the allocator, which is the larger effect measured here.

### E.2 Already carried, and still the right neighbours

`naylor2026cherisimt`, `suchert2023stamp`, `emmerich2019drivers` and `karlback2021ran` are in the
bibliography and cover the contrary side of results 1 and 7. No change needed, but the RQ1
discussion should not read as though parity is the settled consensus when the same bibliography
carries a 46% figure.

## F. Earlier sweeps recommended these, and they are still absent

Verified by surname search over `bibliography.bib` on 24 August 2026. Each would corroborate a
result in §B, and each was already argued for in an earlier sweep, so the work of judging them is
done.

| Source | Sweep | Corroborates |
| --- | --- | --- |
| van Kempen and Berger, ISMM 2026, DOI 10.1145/3814942.3816132, pages 14-24 | 4 §D.0 | Result 8, allocator choice as a first-order variable. Abstract confirmed: it "revisits that work on a modern hardware platform with modern general-purpose allocators", covering "C, C++, or Rust" |
| Popescu et al., PLDI 2026, DOI 10.1145/3808266 | 4 §F.0a | Results 7 and 10, and see E.1 |
| Costanzo et al., CLEI 2021, DOI 10.1109/CLEI53233.2021.9640225 | 4 §F.2 | Result 1, matched pair with effort measured, and an independent instance of `jemalloc` treated as a variable |
| Coblenz et al., ICSE 2022, DOI 10.1145/3510003.3510107 | 5 §E.1 | RQ4's human cost, and the only randomised controlled trial available |
| Pereira et al., Sci. Comput. Program. 2021, DOI 10.1016/j.scico.2021.102609 | 4 §F.1 | Journal version of a citation already used, which retires `bugden2022rust` |
| Nguyen et al., MSWiM 2025, and Giustini et al., WiSec 2026 | 1 §7.3 | Result 4's regime, in the RAN control plane specifically |
| Liao et al., Pallas, USENIX ATC 2025, and Jia et al., Aquifer, IEEE TSC 2024 | 1 §7.5 | The thread-per-shard design choice, independent of the fairness argument |
| Xie et al., PLOS 2025, and Teper et al., IEEE TCAD 2024 | 1 §7.7 | The async mechanism behind `arvidsson2025async`, and the honesty check that thread-based C++ is not automatically starvation-free |

Recommended order if only some are taken: van Kempen and Berger, then Popescu, then Nguyen and
Giustini. The first two attach to results that are currently unsupported, and the third pair puts
the overload regime in the thesis's own domain.

## G. Negative results, recorded so they are not searched for again

- **No peer-reviewed study reports a load-dependent performance reversal between Rust and C++.**
  Searched OpenAlex, DBLP, Crossref and the general web under overload, saturation, throughput
  collapse, congestion collapse and knee phrasings. The web synthesis states the opposite prior
  explicitly, which is worth knowing: the received position is that any Rust deficit under load
  comes from allocator contention, lock choice or async runtime, and not from the language. That
  is compatible with the thesis's own mechanism claim and it is not evidence either way.
- **No peer-reviewed measurement of Rust against C++ build time exists, and the web set here is
  dangerous in the way sweep 5 §G warned.** Two pages on the same domain report Rust clean builds
  37% slower and 30 to 35% faster than C++ on comparably described premises, both with
  fabricated-looking precision (`8m12s (±12s)`), invented cost figures and named tool versions. A
  third, elsewhere, reports 3.2 times slower on a 47,000-file monorepo. Contradictory
  numbers at that precision are the signature of generated content. **The thesis's own paired
  measurement is the only real evidence in this area**, which raises rather than lowers the value
  of §7.6, and the decomposition requirement in `AGENT.md` §3 item 6a is what keeps it honest.
- **No peer-reviewed comparison of `std::unordered_map` against Rust's `HashMap` on speed either.**
  Sweep 4 §H recorded the same absence for footprint. The engineering benchmarks are extensive and
  consistent (open addressing beats node-based chaining on small keys, and the C++ standard's
  requirements effectively mandate chaining) but they are blog and benchmark-suite material. Cite
  the normative documents and C.8 for the mechanism, never a benchmark page for a number.
- **No peer-reviewed study of use-after-move detection in C++.** Only tool documentation and
  Chromium's own enablement discussion, which reports both real bugs found and a false-positive
  rate. C.9 is the citable form.
- **No Rust-specific atomicity-violation detector in the literature.** Searched OpenAlex, DBLP and
  Crossref. The atomicity-violation literature is general purpose (Park and Sen, FSE 2008, DOI
  10.1145/1453101.1453121, and Yoga and Nagarakatte, CGO 2016, DOI 10.1145/2854038.2854063) and
  none of it is about Rust. C.1 is the right citation for the category, and the absence is itself a
  small point in favour of the thesis's `lost_update` row being worth publishing.
- **NPB-Rust is not citable.** "NPB-Rust: NAS Parallel Benchmarks in Rust", Martins, Faé,
  Hoffmann, Bianchessi and Griebler, arXiv 2502.15536. A matched Rust, C++ and Fortran benchmark
  suite that reports peak memory per benchmark, so it looks ideal for results 1 and 7. DBLP lists
  it as CoRR only and Crossref has no published version, so it stays a preprint. Recheck once
  before submission in case a venue version appears.
- **Semantic Scholar returns empty abstracts for ACM-deposited papers.** OpenAlex's
  `abstract_inverted_index` had them in every case tested, so reconstruct from OpenAlex rather than
  concluding the abstract is unavailable.

## H. BibTeX

```bibtex
@inproceedings{lu2008mistakes,
  author    = {Lu, Shan and Park, Soyeon and Seo, Eunsoo and Zhou, Yuanyuan},
  title     = {Learning from Mistakes: A Comprehensive Study on Real World
               Concurrency Bug Characteristics},
  booktitle = {Proceedings of the 13th International Conference on Architectural
               Support for Programming Languages and Operating Systems (ASPLOS)},
  pages     = {329--339},
  year      = {2008},
  doi       = {10.1145/1346281.1346323},
  url       = {https://doi.org/10.1145/1346281.1346323}
}

@article{dietz2015overflow,
  author    = {Dietz, Will and Li, Peng and Regehr, John and Adve, Vikram},
  title     = {Understanding Integer Overflow in {C/C++}},
  journal   = {ACM Transactions on Software Engineering and Methodology},
  volume    = {25},
  number    = {1},
  pages     = {2:1--2:29},
  year      = {2015},
  doi       = {10.1145/2743019},
  note      = {Crossref deposits the page range as 1--29},
  url       = {https://doi.org/10.1145/2743019}
}

@article{cui2024rcanary,
  author    = {Cui, Mohan and Xu, Hui and Tian, Hongliang and Zhou, Yangfan},
  title     = {{rCanary}: Detecting Memory Leaks Across Semi-Automated Memory
               Management Boundary in {Rust}},
  journal   = {IEEE Transactions on Software Engineering},
  volume    = {50},
  number    = {9},
  pages     = {2472--2484},
  year      = {2024},
  doi       = {10.1109/TSE.2024.3443624},
  url       = {https://doi.org/10.1109/TSE.2024.3443624}
}

@article{mogul1997livelock,
  author    = {Mogul, Jeffrey C. and Ramakrishnan, K. K.},
  title     = {Eliminating Receive Livelock in an Interrupt-Driven Kernel},
  journal   = {ACM Transactions on Computer Systems},
  volume    = {15},
  number    = {3},
  pages     = {217--252},
  year      = {1997},
  doi       = {10.1145/263326.263335},
  url       = {https://doi.org/10.1145/263326.263335}
}

@inproceedings{welsh2001seda,
  author    = {Welsh, Matt and Culler, David and Brewer, Eric},
  title     = {{SEDA}: An Architecture for Well-Conditioned, Scalable Internet
               Services},
  booktitle = {Proceedings of the 18th ACM Symposium on Operating Systems
               Principles (SOSP)},
  pages     = {230--243},
  year      = {2001},
  doi       = {10.1145/502034.502057},
  url       = {https://doi.org/10.1145/502034.502057}
}

@inproceedings{cho2020breakwater,
  author    = {Cho, Inho and Saeed, Ahmed and Fried, Joshua and Park, Seo Jin and
               Alizadeh, Mohammad and Belay, Adam},
  title     = {Overload Control for $\mu$s-scale {RPCs} with {Breakwater}},
  booktitle = {Proceedings of the 14th USENIX Symposium on Operating Systems
               Design and Implementation (OSDI)},
  pages     = {299--314},
  year      = {2020},
  url       = {https://www.usenix.org/conference/osdi20/presentation/cho}
}

@inproceedings{cho2023protego,
  author    = {Cho, Inho and Saeed, Ahmed and Park, Seo Jin and
               Alizadeh, Mohammad and Belay, Adam},
  title     = {{Protego}: Overload Control for Applications with Unpredictable
               Lock Contention},
  booktitle = {Proceedings of the 20th USENIX Symposium on Networked Systems
               Design and Implementation (NSDI)},
  pages     = {725--738},
  year      = {2023},
  url       = {https://www.usenix.org/conference/nsdi23/presentation/cho}
}

@inproceedings{candea2003crashonly,
  author    = {Candea, George and Fox, Armando},
  title     = {Crash-Only Software},
  booktitle = {Proceedings of the 9th Workshop on Hot Topics in Operating
               Systems (HotOS IX)},
  pages     = {67--72},
  year      = {2003},
  url       = {https://www.usenix.org/conference/hotos-ix/crash-only-software}
}

@article{hejderup2022prazi,
  author    = {Hejderup, Joseph and Beller, Moritz and Triantafyllou, Konstantinos
               and Gousios, Georgios},
  title     = {{Pr{\"a}zi}: From Package-Based to Call-Based Dependency Networks},
  journal   = {Empirical Software Engineering},
  volume    = {27},
  number    = {5},
  year      = {2022},
  doi       = {10.1007/s10664-021-10071-9},
  note      = {Article number not confirmed, Crossref deposits no page range},
  url       = {https://doi.org/10.1007/s10664-021-10071-9}
}

@article{sotovalero2021bloat,
  author    = {Soto-Valero, C{\'e}sar and Harrand, Nicolas and
               Monperrus, Martin and Baudry, Benoit},
  title     = {A Comprehensive Study of Bloated Dependencies in the {Maven}
               Ecosystem},
  journal   = {Empirical Software Engineering},
  volume    = {26},
  number    = {3},
  year      = {2021},
  doi       = {10.1007/s10664-020-09914-8},
  note      = {Article number not confirmed, Crossref deposits no page range},
  url       = {https://doi.org/10.1007/s10664-020-09914-8}
}

@article{richter2015hashing,
  author    = {Richter, Stefan and Alvarez, Victor and Dittrich, Jens},
  title     = {A Seven-Dimensional Analysis of Hashing Methods and Its
               Implications on Query Processing},
  journal   = {Proceedings of the VLDB Endowment},
  volume    = {9},
  number    = {3},
  pages     = {96--107},
  year      = {2015},
  doi       = {10.14778/2850583.2850585},
  url       = {https://doi.org/10.14778/2850583.2850585}
}

@misc{clangtidyuseaftermove,
  author       = {{The LLVM Project}},
  title        = {clang-tidy check {\texttt{bugprone-use-after-move}}},
  note         = {Extra Clang Tools documentation. Accessed August 2026},
  url          = {https://clang.llvm.org/extra/clang-tidy/checks/bugprone/use-after-move.html},
  year         = {2026}
}
```

Entry-type note. `clangtidyuseaftermove` is tool documentation and the prose must present it as
such, in the same register as `tsandeadlock`. The two USENIX entries have no DOI by venue practice,
which is normal and not a defect. Every other entry is peer-reviewed. `bibliography.bib` is
currently 105 entries with no orphans, so anything taken from here has to be cited on the way in.

## I. Order of work

1. **§`sec:threats` and the RQ1 discussion: write down which results stand alone.** Costs one
   short paragraph, buys the honesty criterion 5 is graded on, and pre-empts the obvious question
   about the overload result. Nothing else here matters as much.
2. **RQ2, four citations, four sentences that stop being unsupported.** C.3 for the leak, C.1 for
   the lost update, C.2 for the overflow, C.9 for the use-after-move caveat. This is the cheapest
   real gain in the sweep, and RQ2 is the falsifiable core of the thesis.
3. **Result 4's regime: C.4, C.5 and C.6.** Livelock is the term the §7.5.3 sentence is reaching
   for, and naming it costs nothing.
4. **Result 7: add E.1 to the contrary-results passage** and rewrite the peak-RSS summary as mixed
   rather than as agreement with two of three theses.
5. **RQ4: C.7 for the dependency surface**, which is the one RQ4 axis where published work says
   what the thesis says.
6. **Result 3: C.8 plus the two normative documents**, if §7.5.2's attribution to map layout is to
   keep standing. Optional, and lowest risk of the six.
7. **Then reconsider §F.** Three of those eight were recommended a week ago and attach to results
   that currently have no support at all.
