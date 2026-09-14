# Container harness validation, 20 August 2026

A full campaign was run through `docker/run.sh` on the WSL2 development laptop to find
out whether the containerised harness works end to end. It does, and it produced two
results worth acting on plus one open question.

**This is not measurement evidence and cannot become any.** The host is WSL2, which
`bench/TESTBED.md` §6 rules out for RQ1 and RQ3, and the container shares that kernel.
The run was made with `--smoke`, so it wrote to `docker/.scratch` and never into
`bench/results`, which is what `bench/plot_figures.py` and `build_deck.py` read when no
campaign is named. Nothing in the thesis was regenerated and no tracked number moved.
The artefacts are preserved under `docker/validation/` so the figures below can be
checked, with a warning in that directory about the one mistake that would matter.

## What was run

```bash
docker/run.sh --smoke campaign --repeats 10 --shards 7 --producers 7 \
    --duration 3 --warmup-s 1 --workload mixed --active-ues 5000 --preload 5000 \
    --rates "1000 4000 16000 48000 112000"
```

200 runs in 32 minutes wall clock, image `uecm-bench:el8-gcc15-rust1.97.1`, cores 2 to 13,
seccomp off, no CPU quota, no memory limit, network off. Shard and producer counts match
the reported campaign so the two are comparable in shape, and the rate ladder was trimmed
to five points that still reach the reported overload load of 784 kops/s offered.

One deviation from the protocol is unavoidable on this laptop and it matters: 14 benchmark
threads on a 12-core cpuset. The measurement host gives 14 threads 16 cores. Everything
below that looks like contention should be read with that in mind first.

## What the run validated

The whole pipeline, for the first time in one pass, and this is the part that transfers to
the testbed visit.

- All four variants built inside the container from the pinned toolchain, interleaved by
  repeat then rate then variant, 200 runs with no failure.
- The HDR sidecar is lossless. `bench/pool_hist.py --verify` recomputed every percentile of
  all 200 runs from the persisted buckets and matched what the binaries printed, confirmed
  1.82 million persisted values, and confirmed both languages landed on the same lattice.
  The pooled far tail has about 21 samples past p99.99 in its smallest group.
- The analysis half runs too. `bench/plot_figures.py` produced all nine figures, every
  generated table, and a complete `gen_macros.tex`, with `NTests` still 14.
- **The jitter and far-tail macros exist for the first time.** `tab_jitter.tex`,
  `JitterRange`, `JitterSpread`, `JitterVsMedian`, `FarTailRange`, `FarTailSpread`,
  `IqrRange`, `IqrSpread` and `JitterPNineNineRange` are all written by this run and by no
  reported campaign, which is exactly the hole `docs/TODO.md` Phase 11 item 2 describes.
  Their names and shapes are now known, so the float, caption and prose in §7.5 can be
  written before the testbed visit instead of during it.
  *(Four of those names were retired on 27 August 2026 and this paragraph is left as written,
  because it records what that run produced. `JitterRange` and `JitterPNineNineRange` became
  Lo/Hi pairs after a range macro wrapped in math mode typeset as two minus signs, `IqrRange`
  followed for the same reason, and `JitterVsMedian` became `JitterVsMedianPct` after the prose
  read a percentage as a multiple. The far-tail macros are now read from the pooled sidecar
  rather than the per-run field.)*
- The environment record carries its own provenance: image manifest, `container: docker`,
  `virtualisation: microsoft`, no cgroup quota, seccomp 0, cpuset 2 to 13.

## What reproduced, and what did not

Compared against the reported campaign (`campaign-20260812-154528`, KVM Xeon guest, 20
repeats). Both columns are computed by the same code from the same macro names.

| | Reported, KVM, 20 rep | This run, WSL container, 10 rep |
| --- | --- | --- |
| Peak RSS, language effect (Rust higher) | 1.9 to 3.4 MiB | 3.9 to 4.1 MiB, CI 3.8 to 4.2 |
| Peak RSS, allocator effect (jemalloc higher) | 32.9 to 34.4 MiB | 1.8 to 2.1 MiB |
| Overload, faster sustained | C++ | C++ |
| Overload throughput ratio at 784 kops/s | 1.8x | 1.4x |
| Repeats agreeing on the overload sign | 20/20 | 8/10 |
| Overload throughput, Holm-corrected p | 0.000027 | 0.123 |
| Tail intervals excluding zero | 0 | 0 |
| Median equivalence bound | 2.0 µs | 33.3 µs |

Three readings.

**The overload divergence reproduces in direction and not in significance.** C++ sustains
more than Rust past saturation here as well, and it does so at every point in the overload
region rather than only at the quoted one: the plateau is 39.7 against 29.0 kops/s at 112
kops/s offered, 40.5 against 29.9 at 336, and 38.5 against 28.3 at 784, a ratio of 1.36 to
1.37 throughout. That the corrected p is 0.123 at 10 repeats on a contended host is what
the protocol predicts and is not evidence against the reported result.

**The peak-RSS language effect reproduces with the same sign** and a slightly larger
separation, on an interval that excludes zero. This is the campaign's one solid
quantitative result and it survived a change of host, kernel, core count and compiler
patch level.

**The allocator effect did not reproduce in magnitude and that is unexplained.** The
reported campaign separates the jemalloc variants from the system variants by about 33 MiB, and
here the same two variants sit 2 MiB apart. It is not a configuration slip: the environment
capture shows `MALLOC_CONF` and `_RJEM_MALLOC_CONF` both pinned to
`thp:never,narenas:16`, the C++ variant links `/lib64/libjemalloc.so.2` and the Rust variant
builds its own, exactly as on the measurement host. The leading suspect is the host
hugepage policy, `always` on the KVM guest against `madvise` here, since jemalloc's own
`thp:never` governs its advice and not what the kernel does with a mapping it was never
advised about. Worth resolving, because the reported allocator effect is an order of
magnitude larger than the language effect it is meant to contextualise, and if most of it
is a host property then §7.5.4 is describing the guest and not the allocator.

## What this run says about the host, which is the point of the protocol

The below-saturation numbers are not usable and the harness shows why rather than hiding
it. At 28 kops/s offered the reported campaign puts all four variants at about 90 µs median
with 63 to 65% CPU. The same point here gives medians of 200, 467, 1123 and 212 µs across
the four variants, with 235 to 335% CPU. A spread of five times between variants that the
measurement host separates by a percent, at three to five times the CPU for identical
work, is a host artefact and nothing else. Read `tab_latency.tex` in
`docker/validation/` as a demonstration of what the protocol excludes, not as a result.

## Follow-ups this created

1. `docs/TODO.md` Phase 11 item 2 asked for a campaign carrying the jitter and HDR
   sidecars. The harness for it is now proven, so what remains is running it on the KVM
   guest rather than on this laptop. That is an afternoon and it needs no testbed.
2. The §7.5 float and caption for `tab_jitter.tex` can be written now against the real
   macro names, and the §8.6 paragraph saying the two metrics are instrumented but not
   reported will need revising once the KVM run lands.
3. The allocator-effect question above deserves a check on the measurement host, and
   `stats.metadata` from the `je` fields is the instrument for it. That is
   `docs/TODO.md` Phase 11 item 3, and this run gives it a sharper reason to exist.
