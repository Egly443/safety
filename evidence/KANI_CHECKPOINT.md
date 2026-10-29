# Actual-code verification checkpoint — 2026-10-29

Outcome: **inconclusive**. Actual pinned Codex code compiled under Kani 0.68.0,
and the selected harness reached symbolic execution. No completed property proof
or safety counterexample was obtained. No verification job is currently running.
The earlier 17 passing VM checks are separate evidence.

| Attempt | Harness | Wall time | Peak sampled aggregate RSS | Outcome |
| --- | --- | ---: | ---: | --- |
| Offline metadata | original fixture | 12.026 s | 0.159 GiB | uncached locked dependency; no compilation |
| Actual code | long paths, unwind 64 | 777.761 s | 4.019 GiB | RSS guard |
| Bounded follow-up | short paths, unwind 16 | 300.36 s | 2.364 GiB | wall-time guard |

The cargo phase of the large attempt reported 8m35s. Its final output was
unwinding standard-library byte-search code. The short attempt also remained in
symbolic execution. These observations do not establish the exact root cause of
cost. Path lengths and unwind bound changed together; cold/warm compilation differs.
No controlled attribution or extrapolated proof-completion estimate is justified.

The transformation is `effective_file_system_sandbox_policy`; the observation
is `FileSystemSandboxPolicy::can_write_path`. Source files match commit
`360319d8dee62d87e2d59fc0c21805d79519cfed`. The harness hook is isolated in a
separate worktree. All production function bodies and dependency records are
unchanged; only the established local workspace version correction is applied.
There are no stubs, replacement policy/path implementations, or disabled safety
or unwinding checks. The harness is a fixed concrete instance, not the intended
bounded symbolic theorem. A must-fail reachability control remains to be run
before accepting a future successful smoke result as non-vacuous evidence.

The sampler guard was separately exercised for normal completion, timeout, and
memory termination. It is a sampled operational guard, not a hard kernel limit.
Logs and JSON records retain the measured resource stops. The source and harness
hashes are in `kani-source-manifest.json` and the archived large-path manifest.

Next recommendation: run the identical short fixture on a confirmed 16 GiB or
larger Codex Cloud environment, capped at 8 GiB sampled RSS and 20 minutes. This
changes operational budgets, not the claim. More memory is not guaranteed to
solve the symbolic-execution cost. If still inconclusive, review compositional
verification options before extracting code, introducing contracts/stubs, or
weakening the goal.

The Cloud CLI was reachable but exposed no selectable environment, and this
session has no attached Cloud execution tool. No Cloud task or paid external
compute resource was created. `verification/CLOUD_RETRY.md` describes the retry.
Paper novelty, the bounded theorem, and a Lean-to-code refinement remain open.
