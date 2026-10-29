# Cloud retry: 60 minutes, 16 GiB

Outcome: **inconclusive**. The wall-time guard stopped symbolic execution; no completed assertion summary, proof, or counterexample was produced. One harness (`actual_policy_smoke`) was selected and reached checking; zero harnesses completed. Safety and unwinding checks remained enabled. No SAT-solving stage was observed in the log.

| Metric | Previous cold run | This warm run |
|---|---:|---:|
| Wall limit | 20 minutes | 60 minutes |
| Observed elapsed | 1200.174 s | 3600.511 s |
| RSS cap | 8 GiB | 16 GiB |
| Peak sampled aggregate RSS | 5.76 GiB | 14.87 GiB |
| Stop reason | wall_limit | wall_limit |

Compilation reused the existing target directory and finished in 0.48 seconds. The previous run spent approximately seven minutes compiling, so this run also had substantially more time for symbolic execution. Sampled cumulative CPU time was 3598.65 seconds, or approximately 0.999 CPU cores on average. CPU time and RSS were sampled from the process group through `/proc`; these are observations, not exact kernel accounting. RSS can count shared pages more than once. CPU samples can miss very short-lived processes.

The machine had a 32 GiB cgroup memory limit and four-core CPU quota. Extra cores would primarily help compilation or independent harnesses, while this check consumed approximately one core. The higher memory cap allowed continued exploration beyond 8 GiB but did not produce completion. Switching SAT solvers would not address the observed pre-solver bottleneck. A further time/memory increase has no established completion bound; profiling and a separately designed, smaller verification scope are better next investigations. Do not disable safety or unwinding checks to obtain a pass.

The fixture, unwind bound (16), and production functions were unchanged. `python3 scripts/prepare-kani.py --check` passed after termination. Only expected evidence files changed in the project checkout; the sampling helper lives in ignored `.tools/run-limited-sampled.py`. The worktree diff is in `.tools/cloud-retry-worktree.diff`. Prior 20-minute evidence is preserved in `.tools/cloud-retry-20m/`.

Artifacts:
- `evidence/kani-feasibility.log`
- `evidence/kani-feasibility-resources.json` (exact command, limits, stop reason)
- `evidence/kani-feasibility-resources.samples.jsonl` (10-second CPU/RSS samples)
- `evidence/kani-source-manifest.json`
- `.tools/cloud-retry-versions.txt`

Versions:
```
rustc 1.99.1 (58cf8f9c3 2026-10-13)
rustc 1.100.0-nightly (8925ea358 2026-08-20)
Kani Rust Verifier 0.68.0 (cargo plugin)
CBMC 6.11.0
6.11.0 (cbmc-6.11.0)
```

No commit, push, PR, full CLI build, or VM run was performed.
