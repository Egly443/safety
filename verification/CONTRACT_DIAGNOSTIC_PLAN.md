# Bounded contract-instrumentation diagnosis

1. Compare the selected actual protected-entry preservation case in ordinary
   and contract-proof modes. Keep the property body, checks, unwind, feature
   flag and resource budget identical. Ordinary mode removes the ensures
   annotation and changes the contract harness to assert the same returned
   boolean; contract mode uses the existing source unchanged.
2. Run a small dependency-free vector-of-bytes program in both modes, then
   a vector of small entry records. These are tooling diagnostics, not Codex
   policy models or contracts that may be assumed about production.
3. If small cases finish, repeat the collection shape using actual Codex URI
   entry types, but without the production policy transformation. This tests
   whether the data/library composition alone reproduces the cost. It is not
   a proof or replacement implementation of that transformation.
4. After a positive proof completes, run its deliberately false companion.
   A skipped or incomplete control does not establish reachability.

Use exact harness selection, unwind 16, all default checks, one compiler job,
the same feature flag `-Z function-contracts`, and 180 seconds / 8 GiB per job.
Retain source snapshots and hashes, generated ordinary-mode changes, exact
commands, exit codes, selected harness summaries, CPU/RSS samples and live tool
process names. Note that standalone and full-Codex build contexts differ;
ordinary-vs-contract comparisons within each case keep context fixed.

Stop type growth if a small stage cannot complete. Do not raise budgets, weaken
checks, install an unverified replacement toolchain, introduce assumptions,
publish a bug report, or alter production functions in this experiment.
If it does not yield a tractable route, pause further Kani proof expansion and
report the specific unresolved boundary. Do not label a timeout a correctness
failure or claim an upstream bug solely from a slow run.

Run `python3 scripts/diagnose-kani-contracts.py` from `/workspace/safety` after
sourcing `.tools/activate.sh`. The runner preserves prior evidence and refuses
to overwrite `.tools/kani-contract-diagnostics`.
