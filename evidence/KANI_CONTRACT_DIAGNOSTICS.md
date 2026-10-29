# Matched contract diagnostics

**Stopped Kani proof expansion at a small standalone reproducer.** An ordinary
three-element byte-vector property passed in four seconds, while checking its
contract exceeded the 8 GiB sampled RSS cap after about 40 seconds. This occurs
without Codex, PathUri, or any third-party crate. Its contract log reports
argument-count mismatches in Kani's internal contract bookkeeping and insertion
of nondeterministic values. These observations warrant tool investigation; they
are not a definitive root-cause diagnosis or proof of an upstream bug.

## Matched outcomes

| Case | Mode | Outcome | Wall seconds | Peak sampled GiB | Stop reason |
|---|---|---|---:|---:|---|
| preservation | ordinary | inconclusive | 180.275 | 4.36 | wall_limit |
| preservation | contract | inconclusive | 180.263 | 2.23 | wall_limit |
| bytes | ordinary | passed | 4.006 | 0.08 | none |
| bytes | contract | inconclusive | 40.069 | 8.19 | rss_limit |

The ordinary byte-vector false companion completed with exactly one failure at
`assert!(!probe())`; the positive completed one harness with zero of 569 checks
failed, including 16 reported unreachable checks. All other failure controls
were skipped because their corresponding positive checks were incomplete.

Both modes use exactly the same fixture body, unwind 16, default safety checks,
`-Z function-contracts`, exact selection of one harness, one compiler job, and
180 seconds / 8 GiB resource budgets. Ordinary mode removes only the ensures
annotation, replaces `proof_for_contract` with `proof`, and asserts the same
boolean result. The generated source snapshots and three-part diffs are saved.
Within each case the build context is fixed. The small source is standalone;
the full case builds in the pinned Codex crate. This is a bounded diagnostic
comparison, not a statistically controlled benchmark. Wall time includes setup
and compilation. RSS is sampled aggregate process-group RSS, not a kernel hard
limit; one-second sampling explains the observed overshoot above 8 GiB.

## Where the time and memory went

The full ordinary preservation case reached CBMC and symbolic execution. The
full contract case spent its budget in `goto-instrument` and did not log a
selected-harness line or verification summary. Therefore contract instrumentation
adds a distinct pre-verification obstacle, but it is not the only obstacle to
proving the full property: ordinary mode also timed out.

The small byte-vector contract did reach CBMC. It reported symbolic execution
complete and generated verification conditions, then hit the memory cap before
logging SAT solving or a result. Its slowdown is therefore a different observed
phase from the full contract's instrumentation timeout. Do not conflate the two
or claim that one warning explains both.

The relevant warning text is:

```
enter_contract_clause: ... saturating_add ... not enough arguments, inserting non-deterministic value
exit_contract_clause: ... saturating_sub ... not enough arguments, inserting non-deterministic value
```

Full messages and per-second process names, CPU time and RSS samples are retained
in the machine-readable evidence and raw logs. CPU accounting is sampled from
`/proc` descendants, includes the resource runner, and can miss short-lived
processes. It is diagnostic evidence, not exact kernel accounting.

## Stopping rule and recommendation

The first small contract failed to complete, so the runner stopped type growth.
The prepared small-entry and actual-URI-entry templates were **not run**. No
budgets were raised, checks disabled, contracts assumed, or production calls
replaced. No larger proof campaign or symbolic path widening was attempted.

Pause using checked contracts as a scaling strategy for the project until the
standalone discrepancy is explained or a supported workaround is independently
validated on the positive and deliberate-failure cases. Do not infer that fixing
it would solve the full ordinary-mode timeout. Retain the successful native
matrix as implementation evidence. A source-aligned abstract policy model can be
pursued separately, with correspondence to Rust explicitly left open.

## Artifacts and integrity

- `evidence/KANI_CONTRACT_DIAGNOSTICS.json`: raw outcomes, exact commands,
  source/log hashes, resource limits, CPU/phase summaries and regression replay.
- `.tools/kani-contract-diagnostics/`: source snapshots, mode diffs, complete
  logs and per-second samples. `driver-executed.py` preserves the exact executed
  driver. A later defensive fix labels an unexpectedly passing false control
  `unexpected_success`; the observed control failed correctly, so results do
  not depend on that fix.
- `verification/diagnostics/vector_case.rs`: dependency-free reproducer source.
- `evidence/KANI_CONTRACT_REPRODUCER.md`: draft report and reproduction details.
- `evidence/kani-contract-reproducer.tar.gz`: standalone sources, guard, logs,
  resource evidence and versions. It excludes Codex sources and credentials.

The original production manifest passed after every temporary full-case hook
and at completion. The native matrix replay matched saved JSON exactly: 3,960
access observations plus 1,800 structural checks, zero mismatches. Original
production functions and the original Kani fixture remain unchanged. No report
was sent externally, and no commit or push was performed.
