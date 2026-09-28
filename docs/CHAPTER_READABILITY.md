# Chapter readability: `Thesis_v4.tex`

Generated 2026-09-14 by `.chapter_readability.py`. Same counters as `.readability.py`.
Floats, tables, and lists are dropped. Syllables are vowel groups, so a few
technical words are over-counted.

Re-run:

```bash
python3 .chapter_readability.py Thesis_v4.tex -o docs/CHAPTER_READABILITY.md
```

## Whole document

- Sentences: 674
- Words: 8878
- **Flesch Reading Ease: 71.2** (fairly easy)
- Flesch-Kincaid grade: 6.6
- Gunning Fog: 9.0
- Mean sentence length: 13.1 words (stdev 6.4)
- Mean syllables per word: 1.446
- Short sentences (<15 words): 66.2%
- 3+ syllable words: 9.5%

## Per chapter

| # | Chapter | Flesch | Band | FK | Fog | Sent. | Words | ASL | ASW | Short | 3+ syl |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Introduction | 44.2 | difficult | 11.4 | 15.1 | 97 | 1698 | 17.3 | 1.715 | 46.4% | 20.3% |
| 2 | Background: Systems Languages for Latency-Critical Software | 72.9 | fairly easy | 6.0 | 8.7 | 70 | 817 | 11.6 | 1.444 | 71.4% | 10.3% |
| 3 | Research Methodology | 67.8 | standard | 6.9 | 9.4 | 113 | 1430 | 12.7 | 1.492 | 74.3% | 10.8% |
| 4 | Design and Implementation | 72.1 | fairly easy | 5.6 | 7.6 | 55 | 530 | 9.6 | 1.477 | 89.1% | 9.2% |
| 5 | Experimental Setup and Evaluation | 83.1 | easy (80+) | 4.7 | 6.8 | 159 | 1970 | 12.4 | 1.314 | 67.9% | 4.6% |
| 6 | Discussion | 80.7 | easy (80+) | 5.4 | 7.3 | 114 | 1543 | 13.5 | 1.330 | 62.3% | 4.7% |
| 7 | Conclusion and Future Work | 79.7 | fairly easy | 5.5 | 7.4 | 66 | 890 | 13.5 | 1.340 | 59.1% | 5.1% |

## What the columns are

- **Flesch** (Reading Ease): higher is easier. 80+ is the bar used for the
  recent results, discussion, and conclusion pass on `Thesis_v4.tex`.
- **FK**: Flesch-Kincaid grade level (US school grade). Lower is easier.
- **Fog**: Gunning Fog index. Lower is easier.
- **ASL**: average sentence length in words.
- **ASW**: average syllables per word. This is what usually caps Flesch in
  a CS thesis, not sentence length.
- **Short**: share of sentences under 15 words. `.readability.py` asks for
  25-35% as a recovery-point target. Higher than that is what Flesch 80 needs.

Captions inside `figure`/`table` environments are not counted. Neither is the
hypotheses `description` list in the discussion chapter.

## How the numbers are computed

Each Flesch cell is Rudolf Flesch's 1948 Reading Ease score. The script
does not look up a table. It counts words, sentences, and syllables in
that chapter's prose, then plugs the means into:

```
Flesch = 206.835 - 1.015 * ASL - 84.6 * ASW
```

- **ASL** is total words divided by total sentences.
- **ASW** is total syllables divided by total words.

The weights are the story. One extra word per sentence costs about one
point. One extra syllable per word costs about 85 points. In this thesis,
word length is what moves the score, not chopping sentences.

The sibling columns use the same counts:

```
FK  = 0.39 * ASL + 11.8 * ASW - 15.59
Fog = 0.4 * (ASL + 100 * share of 3+ syllable words)
```

Flesch bands in this file: 80+ easy, 70 fairly easy, 60 standard, 50 fairly
hard, 30 difficult, below 30 very difficult.

### Worked example from this table

Chapter 1 and chapter 7 can look similar on the page and still sit tens
of points apart, because the syllable term dominates:

| | ASL | ASW | Sentence term `1.015 * ASL` | Syllable term `84.6 * ASW` | Flesch |
| --- | ---: | ---: | ---: | ---: | ---: |
| Introduction | 17.3 | 1.715 | 17.6 | 145.1 | 44.2 |
| Conclusion | 13.5 | 1.340 | 13.7 | 113.4 | 79.7 |

Plug the introduction in:

```
206.835 - 17.6 - 145.1 = 44.2
```

The syllable term alone is 145 in the introduction and 113 in
the conclusion. That gap is almost the whole difference. The Flesch
column uses the unrounded means, so a calculator that starts from the
one-decimal ASL in the table can be off by 0.1.

### From `.tex` to those counts

1. Start at `\chapter{Introduction}`, stop at `\bibliography`.
2. Drop floats: `figure`, `table`, `tabular`, `tikzpicture`, `description`,
   and lists. Captions and the H1-H3 list do not count.
3. Strip LaTeX. `\cite{...}` becomes a dummy word `X`, math `$...$`
   becomes `N`, and macros such as `\TrackingLoadRust{}` vanish, so
   generated numbers are not spelled out and then counted as extra
   syllables.
4. Split on `. ? !`, ignoring `e.g.` and `i.e.`. A fragment shorter than
   three words is dropped.
5. Count syllables by vowel groups (`a e i o u y`), then drop a silent
   final `e`. That is a cheap heuristic, not a dictionary.

So `safety` is three syllables (`a`, `e`, `y`) even though you say two.
`measured` is three. `operation` is four. Hyphenated tags become one
word: `bare-metal` becomes `baremetal` (four vowel groups). Splitting a
compound into two short words raises Flesch because two short words beat
one long one on this counter.

### Same claim, two wordings

`The Rust variants hold their sent rate.` Seven words, seven syllables,
ASW 1.0.

`The variants maintain their offered throughput.` Six words, about 13
syllables on this counter (`variants` 3, `maintain` 3, `offered` 3,
`throughput` 2), ASW about 2.2.

The second sentence is much more expensive because 84.6 multiplies ASW.
Flesch 80 is conventionally easy, about a late-primary reading load.
Academic CS prose usually lands in the 30-50 difficult band, which is
where a chapter full of `predictability`, `concurrency`, and
`control-plane` still sits. The formula cannot see whether a claim is
still correct. That check is still a read.
