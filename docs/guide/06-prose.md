# 06 Prose screens

Prose reaches a reader on three surfaces. Each has a gate, because none of
them can see the other two.

| Surface | Gate |
| --- | --- |
| Thesis `.tex` | `.aitells.py`, `.vocab.py`, `.b2.py`, `.readability.py`, `.acronyms.py` |
| Diagram labels | `diagrams/check_labels.py` |
| Slide deck | `build_deck.py` → `check_prose_style` |

After a prose edit, run the screens on the file you touched. If the edit
introduced a term, run `.acronyms.py` as well. Suggested wording in chat is
held to the same bar: write a candidate to `.prose-scratch/candidate.tex`
(gitignored) with `\chapter{Introduction}` first and `\bibliography{bibliography}`
last, then run all three of `.readability.py`, `.aitells.py`, `.vocab.py`.

Internal `.md` notes are exempt. Never paste them into a `.tex` file unrewritten.

## House style (zero is the target)

- **No em dash** anywhere a reader sees one. Not `---`, not `—`, not `\u2014`
  in `build_deck.py`. Use a comma, a colon, parentheses, or two sentences.
- **No semicolon** in thesis prose or on a slide. Source code shown verbatim
  would be the exception. No slide shows any.
- **`--`** is legitimate only for numeric ranges (`$2$--$15$`) and compound
  proper names (Herfindahl--Hirschman). TikZ `--` is path syntax.
- **Capital after a colon** only when the words after it begin a unit of their
  own: a run-in label (`\textbf{H1:}` For this workload …) or a colon
  introducing a question. Everything else stays lowercase.
- Write every listed acronym out at first use: `AddressSanitizer (ASan)`. Add
  the row to the front-matter `longtable` in the same edit. The skeleton's list
  is a subset of the draft's.

`.aitells.py` also counts (not gates) transition openers, hedge preambles,
promotional adjectives, signature verbs, counting stubs, and A-A-A triads.
Frequency is the signal. Aim low rather than at zero.

## The scripts

### `.aitells.py` — machine-prose fingerprints

```bash
./.aitells.py Ha_Vien_Mastersthesis_2026.tex
./.aitells.py Thesis_v3.tex
```

Looks for dash asides, antithesis frames, transition openers, promotional
adjectives, counting stubs, uniform sentence length, and the two colon rules.
Nothing except the house-style zeros is "wrong" on its own. A counting stub
is a count subject inside four words that announces a list the next sentences
then give (`Three are results.`). Deleting it would cost no claim.

`$a$--$b$` numeric ranges can show as dash hits. Those are false positives on
this script. Judge them rather than sweeping.

### `.vocab.py` — hard Latinate words

Hand-written REPLACE list (`utilise` → `use`, …). Terms of art are listed
separately at the bottom so their first-use gloss can be checked by hand.
This script does not gate.

### `.b2.py` — rare words by corpus frequency

Needs `wordfreq`. Companion to `.vocab.py`: it can report words nobody put on
the REPLACE list. Terms of art, acronyms, and `\texttt` identifiers are split
out. Produces a list to read, not a verdict.

```bash
python3 .b2.py Thesis_v3.tex
python3 .b2.py Thesis_v3.tex --band c1
```

### `.readability.py` — whole-document load

```bash
python3 .readability.py Thesis_v3.tex
python3 .readability.py Ha_Vien_Mastersthesis_2026.tex
```

Reports Flesch Reading Ease, Flesch-Kincaid grade, Gunning Fog, mean sentence
length and its stdev, share of sentences under 15 words, and 3+ syllable words.

`.readability.py` asks for 25-35% of sentences under 15 words as a recovery
point. A paragraph of three or more sentences with **no** sentence under 15
words goes back. A suggestion whose Flesch is below the host document's own
figure is harder than the thesis it would join.

### `.chapter_readability.py` — same counters, per chapter

```bash
python3 .chapter_readability.py Thesis_v3.tex -o docs/CHAPTER_READABILITY.md
```

Writes [`docs/CHAPTER_READABILITY.md`](../CHAPTER_READABILITY.md). That file
includes the formula, a worked example from the current table, and what the
script includes and drops.

### `.acronyms.py` — gate, not a count

```bash
./.acronyms.py                         # full draft
./.acronyms.py Thesis_v3.tex
```

The front-matter list is the source of truth. Exits non-zero if a listed
acronym is not written out at first use, or if a listed acronym is never used.
Prints its waivers rather than hiding them. First use is from `\mainmatter` to
the bibliography. Citation keys are stripped first.

## How Flesch is computed

Each Flesch cell is Rudolf Flesch's 1948 Reading Ease score:

```
Flesch = 206.835 - 1.015 * ASL - 84.6 * ASW
```

- **ASL** = words / sentences
- **ASW** = syllables / words

One extra word per sentence costs about one point. One extra syllable per
word costs about 85 points. In this thesis, **word length caps the score**.

Siblings from the same counts:

```
FK  = 0.39 * ASL + 11.8 * ASW - 15.59
Fog = 0.4 * (ASL + 100 * share of 3+ syllable words)
```

Bands used in the chapter table: 80+ easy, 70 fairly easy, 60 standard, 50
fairly hard, 30 difficult, below 30 very difficult.

### What is counted

1. Start at `\chapter{Introduction}`, stop at `\bibliography`.
2. Drop `figure`, `table`, `tabular`, `tikzpicture`, `description`, lists.
   Captions and the H1-H3 list do not count.
3. Strip LaTeX. `\cite{...}` → dummy word `X`, math `$...$` → `N`, macros
   vanish, so generated numbers are not spelled out as extra syllables.
4. Split on `. ? !`, ignoring `e.g.` and `i.e.`. Fragments under three words
   are dropped.
5. Syllables are **vowel groups** (`aeiouy`), minus a silent final `e`. Not a
   dictionary. `safety` scores three. `bare-metal` becomes `baremetal` (four).

The formula cannot see whether a claim is still correct. That check is a read.

The full walkthrough, including a worked Introduction vs Conclusion plug-in
from the current table, lives in [`CHAPTER_READABILITY.md`](../CHAPTER_READABILITY.md).

## Offering prose in chat

Write the candidate to `.prose-scratch/candidate.tex`, run the three screens,
then read it three times (argument, sentence, house style). Say what the
screens reported. A suggestion presented as "clearer" cannot be judged.
