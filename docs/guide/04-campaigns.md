# 04 Campaigns and hosts

Three campaigns exist. The **LaTeX macro prefix** is what keeps them apart. A
sentence that quotes the wrong prefix is wrong in a way no build gate catches.

Source of truth: [`AGENT.md` §1, "Which dataset is which"](../../AGENT.md).

## The three live datasets

| Campaign log | Macros | File | Role |
| --- | --- | --- | --- |
| `campaign-20260827-151927.jsonl` | **unprefixed** | `figures/gen_macros.tex` | **Canonical. Every result the thesis reports.** Bare metal, AMD EPYC 7443, SMT off, `performance` + boost off, `nohz_full`, no hypervisor. 7 shards, 7 producers, 20 repeats, 14 loads. Toolchain pinned in the Rocky container: `g++` `\MainGpp` (15.2.1), `rustc` 1.97.1. |
| `campaign-20260812-154528.jsonl` | `\Guest*` | `figures/gen_guest.tex` | KVM guest, identical design. The measurement-validity comparison in the host-compare section. Could not resolve the far tail. `g++` is `\GuestGpp` (15.1.1). `rustc` matches. |
| `campaign-20260826-*.jsonl` | `\Bm*` | `figures/gen_baremetal.tex` | Second bare-metal host. Whether findings survive a change of shard count (8/8), load grid, repeat count, and compiler. |

Host descriptions are generated too: `\Main*` from the reported campaign's own
environment capture (matched by timestamp, not "newest file"), `\Guest*` and
`\Bm*` from theirs.

**`\MainDistro` is the container image** (Rocky Linux 8.10). **`\MainHostDistro`
is the machine** (Ubuntu). The capture beside the reported campaign was written
inside the container. `bench/plot_figures.py` reads the host name from the
capture taken *outside* the container in the same session.

## Where the logs live

| Directory | Role | Git |
| --- | --- | --- |
| `bench/results/` | Live working copy. `refresh_thesis.sh` takes the newest log here unless `--campaign` is passed. | **Gitignored** |
| `bench/results-canonical2/` | Tracked copy of the reported 27 August campaign and its captures. | Tracked |
| `bench/results-baremetal/` | Confirmation-host campaign. | Tracked (partially) |
| `bench/results-canonical/` | **Invalid** 1120-run campaign. Kept as a worked example. **Never quote it.** | Tracked |

Because `bench/results/` is gitignored, a fresh checkout does not have the
working copy. Copy from `results-canonical2/` (or pass
`--campaign bench/results-canonical2/campaign-20260827-151927.jsonl`). Some
environment captures need `git add -f` to survive. `AGENT.md` names them.

## The invalid campaign (`isolcpus`)

`bench/results-canonical/` holds a 27 August 2026 campaign collected with
`isolcpus` set. That flag removes those cores from every scheduling domain.
`campaign.sh` pins with `taskset -c 2-17` and relies on the kernel to spread
threads. With no balancer, every thread inherited `cpu2`. All 1120 runs sat on
one core. Every record looked individually plausible. It was caught only by
comparing three campaigns.

**Never boot a measurement host with `isolcpus`.** Use `nohz_full` and
`rcu_nocbs`. Run `bench/canonical_repeat.sh check-spread` before a long
campaign: it refuses to start below 150% `cpu_pct` on a probe (broken reads
~100%, healthy ~688%).

## What is resolved where

- The **far tail below saturation** is resolved on bare metal and favours Rust.
  It is **pooled** over operations (`*.hist.pooled.csv`), never a median of
  per-run p99.99 values. `tab:latency`'s p99.99 column and every `\FarTail*`
  macro read the pooled file. They print without an interval. The caption
  carries a dagger. Do not add a fallback to the per-run `p9999` field.
- The earlier KVM guest could not resolve that tail. It is retained only for
  the host comparison.
- Past saturation the languages diverge. They stop meeting the offered rate at
  different loads: quote `\TrackingLoadRust` and `\TrackingLoadCpp`, not
  `\SatKnee` (a `min` across variants) for where a variant stops coping.
- Peak RSS: a real **language** effect (about 1.4-3.5 MiB on all three hosts)
  plus a real **allocator** effect. Never write that the allocator effect is
  the larger one. On both bare-metal hosts they are comparable. The guest's
  order-of-magnitude allocator gap belonged to that machine. Transparent
  hugepages (`always` on the guest, `madvise` on both bare-metal hosts) are
  the named candidate. The study must not claim causation.
- Do not claim the guest and reported campaigns share a toolchain.
  `\GuestGpp` is 15.1.1, `\MainGpp` is 15.2.1. The container pins the
  `gcc-toolset` major, not the point release. The kernels differ too
  (`\GuestKernel` vs `\MainKernel`). Quote the macros.

## Pinned operating point

`ReprLoad` is **pinned**, not derived. `REPR_LOAD_OPS = 56000` in
`bench/plot_figures.py`. An older helper took the busiest load holding p99
under 5 ms. That located the noise floor on the guest and the saturation knee
on a quiet host. Do not restore it as the operating point.

## A container is not a testbed

`docker/run.sh` pins the **compiler**. It shares the host kernel. Scheduler,
governor, hugepage policy, and hypervisor stay whatever the host's are.
WSL2 remains WSL2. See [`docker/README.md`](../../docker/README.md) and
[`bench/TESTBED.md`](../../bench/TESTBED.md).

## Regenerating numbers from a campaign

```bash
bench/refresh_thesis.sh --campaign bench/results/campaign-20260827-151927.jsonl
```

Without `--campaign`, the newest log in `bench/results/` is used. Then rebuild
`Thesis_v4.tex` by hand if the skeleton should show the new macros.
