# Staged actual-code verification diagnostics

The end-to-end containment smoke harness remains inconclusive. Its earlier one-hour run stopped in symbolic execution with 14.87 GiB peak sampled RSS and approximately one core of CPU use. No SAT-solving stage was observed. More cores or a different SAT solver do not directly address that observed phase.

We split the workflow into diagnostic stages without replacing production functions, stubbing libraries, disabling safety checks, suppressing unsupported-operation checks, or disabling unwinding assertions. Every harness retains unwind 16. Original `verification/kani/narrow_policy.rs` is unchanged.

## Results

| Variant / harness | Outcome | Wall seconds | Peak sampled GiB | Reported checks |
|---|---|---:|---:|---:|
| baseline / `merge_entries_stage` | inconclusive: wall_limit | 180.19 | 5.49 | uncompleted |
| baseline / `merge_entries_must_fail` | inconclusive: wall_limit | 180.22 | 5.51 | uncompleted |
| baseline / `parse_one_uri` | passed | 51.06 | 2.18 | 20693 |
| -plain / `merge_entries_stage` | inconclusive: wall_limit | 180.20 | 5.59 | uncompleted |
| -plain / `merge_entries_must_fail` | inconclusive: wall_limit | 180.26 | 5.59 | uncompleted |
| -plain / `parse_one_uri` | passed | 52.07 | 2.18 | 20693 |
| -identity / `no_grant_identity_stage` | passed | 12.02 | 0.78 | 5728 |
| -identity / `no_grant_must_fail` | expected failure | 12.02 | 0.78 | 5714 |
| -grant / `empty_base_grant_stage` | passed | 16.02 | 1.18 | 5744 |
| -grant / `empty_base_grant_must_fail` | expected failure | 15.02 | 0.78 | 5710 |

Reported check totals include unreachable checks. Parsing had 1,894 unreachable checks; identity had 705; grant insertion had 703. Each completed run selected and completed exactly one harness. Each expected-failure control had exactly one failing check at its deliberately false assertion, with no other failed checks. Timeout controls did not establish reachability. Resource limits were 180 seconds and 8 GiB per stage, one build job, sequential execution. All runs used the shared warm compilation target. Wall time includes compilation and Kani setup.

## What this establishes

- **URI prerequisite:** parsing the single concrete string `file:///w` yields encoded path `/w`. This is a concrete check, not arbitrary URI correctness.
- **Identity control:** with zero entries, depth `Some(2)`, no additional permissions, and a symbolic choice spanning all three policy kinds, the actual public transformation preserves kind, empty entries and depth. An inverted depth assertion fails as expected.
- **Grant insertion:** for an empty restricted base, one special-root entry with a symbolic read/write mode is inserted by the actual public transformation. The result stays restricted, contains one root entry, preserves read/write mode, and has no glob depth. An inverted empty-result assertion fails as expected. This does not query path access.

These are separate properties, not a composition proof. They do not establish protected-subtree denial, ancestor grant behavior, path specificity, symlink containment, or runtime sandbox behavior. No symbolic containment theorem is claimed.

## Profiling findings and limits

The one-hour log repeatedly visits allocation checks, string scanning, formatting, and path operations. These are log-event counts, not timed function samples or proof that any one function dominates wall time. Two merge stages eliminate URI construction from the fixture but retain the actual merge and entry comparisons; both still time out. Replacing `assert_eq!` with equivalent `assert!` predicates also times out. The URI probe takes approximately the same 51–52 seconds in both variants. Thus diagnostic formatting alone does not explain the cost.

Empty-base grant insertion completes in 16 seconds, while merging against an existing entry exceeds three minutes, even with special-root entries. This narrows the investigation toward the cloning/equality/deduplication path and its reachable library code, but the stages differ in both input shape and assertions, so this is not a controlled timing attribution to a single function. The next useful experiment is an isolated real entry-equality/clone probe, followed by a staged pre-existing-entry merge. Prove any component contracts before using them to simplify an end-to-end proof; do not replace URI or policy implementations with unverified assumptions.

## Reproduction and evidence

From `/workspace/safety`, source `.tools/activate.sh`, then run:

```
python3 scripts/profile-kani-stages.py
python3 scripts/profile-kani-stages.py --plain
python3 scripts/profile-kani-stages.py --identity
python3 scripts/profile-kani-stages.py --grant
```

Each variant writes to its own `.tools/kani-stages*` directory and refuses to overwrite existing results; preserve the old directory outside that exact output path before rerunning. Logs, resource records, selected commands, harness copies/hashes and worktree diffs are retained there. The runner records underlying command exit codes. Current runner exits 2 for incomplete or unexpected experiments and 0 only when each stage passes or its deliberate assertion fails as expected. The initially executed batch driver returned 0 when the batch completed even if a stage timed out; individual recorded runner exit codes and this report preserve those timeouts as inconclusive. The driver has since been hardened to classify results explicitly.

`evidence/KANI_STAGES.json` records exact commands, harness hashes, log hashes, individual resource outcomes, failed-check descriptions and the production source manifest. Production function files were checked against the pinned commit before and after each batch. Only an additional cfg(kani) module hook was temporarily appended to the existing prepared worktree and restored in finally; the post-run original manifest check passed. No commits or pushes were made.

Toolchain: Kani 0.68.0, CBMC 6.11.0, verifier Rust 1.100.0-nightly (8925ea358, nightly-2026-08-21), host Rust 1.99.1. All code targets Codex commit `360319d8dee62d87e2d59fc0c21805d79519cfed`.
