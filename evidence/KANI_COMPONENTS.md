# Equality, cloning, merge and resolver milestone

**Six positive probes passed, six deliberate controls failed as expected. Three
composed probes timed out; their three controls were skipped.** No new
nonempty-merge or protected-path resolver theorem was obtained.

The intended claim and assumptions are in `verification/SCOPED_CLAIM.md`; the
pre-run gates are in `verification/NEXT_MILESTONE_PLAN.md`. All probes call actual
pinned Codex operations. There are no stubs, replacement path models or assumed
component contracts. All retain unwind 16 and default safety/unwinding checks.
Limits were 180 seconds and 8 GiB per selected harness, sequential, one compiler
job and a cached target. Exact fully qualified harness selection prevents a
positive name from accidentally selecting its must-fail companion.

## Outcomes

| Harness | Outcome | Wall seconds | Peak sampled GiB |
|---|---|---:|---:|
| `special_entry_equality` | passed | 12.02 | 0.74 |
| `special_entry_equality_must_fail` | expected_failure | 12.02 | 1.14 |
| `special_entry_clone` | passed | 3.00 | 0.76 |
| `special_entry_clone_must_fail` | expected_failure | 3.00 | 0.75 |
| `uri_clone` | passed | 53.07 | 2.18 |
| `uri_clone_must_fail` | expected_failure | 52.07 | 2.12 |
| `uri_equality` | passed | 53.08 | 2.20 |
| `uri_equality_must_fail` | expected_failure | 54.08 | 2.15 |
| `nonempty_merge_fields` | inconclusive | 180.21 | 5.58 |
| `nonempty_merge_fields_must_fail` | skipped_positive_incomplete | — | — |
| `fixed_resolver` | inconclusive | 180.22 | 3.31 |
| `fixed_resolver_must_fail` | skipped_positive_incomplete | — | — |
| `entry_vector_clone` | passed | 8.01 | 0.64 |
| `entry_vector_clone_must_fail` | expected_failure | 7.01 | 0.72 |
| `entry_vector_contains` | passed | 13.02 | 0.99 |
| `entry_vector_contains_must_fail` | expected_failure | 13.02 | 1.03 |
| `duplicate_merge_only` | inconclusive | 180.24 | 5.47 |
| `duplicate_merge_only_must_fail` | skipped_positive_incomplete | — | — |

Every completed run selected and completed exactly one harness. Reported check
totals and unreachable counts, commands, exit codes, log hashes and resource
records are retained in `evidence/KANI_COMPONENTS.json`. Each expected failure
had exactly one failing check at its deliberately false assertion; there were
no other failed checks. Skipped controls did not establish reachability for
incomplete stages. The batch runner returns 2 for incomplete experiments.

## Exact scope of the passing checks

- Entry equality: two special-root entries, each independently choosing read
  or write, compare equal exactly when their access choices agree (four cases).
- Entry clone: cloning a special-root entry preserves its variant, absent
  missing-path behavior and symbolic read/write mode (two cases).
- URI clone: parsing `file:///w` and cloning it leaves the encoded path `/w`
  on both instances (one concrete URI). This does not check full URI equivalence.
- URI equality: the real `PathUri` equality regards that parsed URI and its
  clone as equal (one concrete URI, not general equality correctness).
- Vector clone: a one-entry special-root vector preserves length, path variant
  and symbolic read/write access after cloning.
- Vector membership: a one-entry special-root vector contains another root
  entry exactly when their independently symbolic access modes agree.

These are separate local results. They are not verified replacement contracts
for arbitrary entries or arbitrary URIs and do not compose automatically.

## What the unresolved gates tell us

The nonempty merge still timed out when its postcondition used only scalar
fields and variant matches, avoiding whole-entry equality assertions. The
strictly smaller concrete duplicate-write merge also timed out. The fixed
resolver probe checked `/w/p` read protection and `/w` workspace permission in
a directly constructed two-entry policy, intentionally omitting the original
root-read entry; it timed out too. Neither is a completed failure of the safety
property.

Standalone equality, cloning and membership are tractable for the tested small
domains. Their composition with the actual policy functions remains expensive.
This rules out treating either standalone operation as a demonstrated sole
bottleneck; it does not identify a definitive cause. No further hardware or
long-run experiment was performed.

The composition gate remains closed: no end-to-end recombination or symbolic
path widening was claimed. A next formal-methods experiment should investigate
checked contracts or verifier simplification at the composition boundary,
without applying a contract beyond its proved input domain. Another unchanged
longer run is not justified by these outcomes alone.

## Regression, integrity and reproducibility

The retained native executable was replayed after the harness work. Its JSON
matched the saved finite matrix exactly: all 3,960 access observations and 1,800
structural checks passed. This is a replay of the native baseline, not a new
symbolic proof or a rebuild against changed production code.

Each batch keeps its exact harness snapshot in `.tools/<batch>/harness.rs` and
its worktree diff, logs, resource records and results alongside it. Later probes
were appended to `verification/kani/policy_components.rs`; the older snapshot
hashes intentionally differ from the final source file. Every run log hash and
snapshot hash was validated when assembling the combined evidence.

Run from `/workspace/safety` after sourcing `.tools/activate.sh`:

```
python3 scripts/profile-kani-stages.py --components
python3 scripts/profile-kani-stages.py --vectors
python3 scripts/profile-kani-stages.py --duplicate-merge
```

Outputs are `.tools/kani-components`, `.tools/kani-vectors` and
`.tools/kani-duplicate-merge`; the runner refuses to overwrite them. Preserve a
batch directory before rerunning. To reproduce a historical source snapshot,
use its retained `harness.rs`; the combined evidence records its SHA256.

The temporary additional module hook was restored after every batch. The
original smoke harness, dependency lock and production function files passed
`prepare-kani.py --check` afterward. Production code remains pinned to
`360319d8dee62d87e2d59fc0c21805d79519cfed`. Kani 0.68.0, CBMC 6.11.0,
nightly-2026-08-21 verifier Rust, and Rust 1.99.1 host tooling were used.
No commits or pushes were made.
