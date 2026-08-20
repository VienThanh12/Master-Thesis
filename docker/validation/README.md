# Harness-validation outputs, not thesis data

Everything in this directory came from a **10-repeat campaign run in the container on
the WSL2 development laptop** on 20 August 2026. It is kept so the numbers quoted in
`docker/VALIDATION.md` can be checked against their source.

**None of it may be copied into `figures/`.** The filenames deliberately match the
generated ones, because these files *are* what `bench/plot_figures.py` writes, which is
the point: the analysis pipeline was exercised end to end. That also makes a careless
`cp` into `figures/` the one thing that would do real damage, since it would replace
every number the thesis quotes with numbers from a host the protocol forbids quoting.

The thesis's own generated macros come from `bench/refresh_thesis.sh` reading the
campaign in `bench/results/`, and that campaign is unchanged.

| File | What it is |
| --- | --- |
| `campaign-*.agg.csv` | bootstrap median and 95% CI per variant and offered load |
| `campaign-*.hist.pooled.csv` | far tail pooled across the 10 repeats |
| `env-*.txt` | environment capture from inside the container, including the image manifest |
| `container-*.txt` | the outside view: image id, cpuset, the full docker command |
| `gen_macros.tex` | every macro the thesis would quote, computed from this run |
| `tab_*.tex` | the generated tables, including `tab_jitter.tex`, which no reported campaign has produced |
