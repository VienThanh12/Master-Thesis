# Chapter readability: `Thesis_v3.tex`

Generated 2026-09-13 by `.chapter_readability.py`. Same counters as `.readability.py`.
Floats, tables, and lists are dropped. Syllables are vowel groups, so a few
technical words are over-counted.

Re-run:

```bash
python3 .chapter_readability.py Thesis_v3.tex -o docs/CHAPTER_READABILITY.md
```

## Whole document

- Sentences: 709
- Words: 9095
- **Flesch Reading Ease: 71.4** (fairly easy)
- Flesch-Kincaid grade: 6.5
- Gunning Fog: 9.0
- Mean sentence length: 12.8 words (stdev 6.3)
- Mean syllables per word: 1.448
- Short sentences (<15 words): 68.4%
- 3+ syllable words: 9.7%

## Per chapter

| # | Chapter | Flesch | Band | FK | Fog | Sent. | Words | ASL | ASW | Short | 3+ syl |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Introduction | 42.9 | difficult | 11.6 | 15.3 | 96 | 1694 | 17.5 | 1.728 | 45.8% | 20.8% |
| 2 | Background: Systems Languages for Latency-Critical Software | 72.3 | fairly easy | 5.8 | 8.7 | 98 | 1047 | 10.6 | 1.462 | 79.6% | 11.2% |
| 3 | Research Methodology | 69.0 | standard | 6.5 | 9.0 | 123 | 1437 | 11.7 | 1.489 | 78.9% | 10.7% |
| 4 | Design and Implementation | 71.8 | fairly easy | 5.6 | 7.6 | 55 | 530 | 9.6 | 1.481 | 89.1% | 9.4% |
| 5 | Experimental Setup and Evaluation | 83.9 | easy (80+) | 4.7 | 6.8 | 156 | 1951 | 12.5 | 1.303 | 67.3% | 4.5% |
| 6 | Discussion | 81.0 | easy (80+) | 5.3 | 7.3 | 114 | 1543 | 13.5 | 1.325 | 62.3% | 4.7% |
| 7 | Conclusion and Future Work | 80.2 | easy (80+) | 5.4 | 7.4 | 67 | 893 | 13.4 | 1.337 | 61.2% | 5.0% |

## What the columns are

- **Flesch** (Reading Ease): higher is easier. 80+ is the bar used for the
  recent results, discussion, and conclusion pass on `Thesis_v3.tex`.
- **FK**: Flesch-Kincaid grade level (US school grade). Lower is easier.
- **Fog**: Gunning Fog index. Lower is easier.
- **ASL**: average sentence length in words.
- **ASW**: average syllables per word. This is what usually caps Flesch in
  a CS thesis, not sentence length.
- **Short**: share of sentences under 15 words. `.readability.py` asks for
  25-35% as a recovery-point target. Higher than that is what Flesch 80 needs.

Captions inside `figure`/`table` environments are not counted. Neither is the
hypotheses `description` list in the discussion chapter.
