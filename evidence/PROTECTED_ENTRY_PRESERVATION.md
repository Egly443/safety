# Selected protected-entry preservation case

**Native case: passed. Native false-removal control: expected failure. Kani
contract: inconclusive at the 180-second wall limit. No checked contract is
available for composition.**

The fixture and obligations were fixed in `verification/PROTECTED_ENTRY_CASE.md`:
root `file:///` read, protected child `file:///w/p` read, and an additional
workspace `file:///w` write grant. The implementation calls the real pinned
`effective_file_system_sandbox_policy`; it does not call access resolution.

## Native outcome

Both original entries were retained, including the original prefix order. The
result contains exactly three entries, exactly one workspace-write entry,
remains restricted, and preserves absent glob depth. Entry equality is the
actual Codex type's equality semantics, not an invented resolver or a statement
about arbitrary URI byte spellings.

The separate control claims `protected_entry_removed`. It reports that claim as
false and exits 1 while reporting `protected_retained: true`; the runner checks
both the exit code and structured observation. The positive case exits 0.
Native compilation completed in 4.007 seconds with the locked dependency graph.
The same Rust source is used for native execution and the Kani contract fixture;
its SHA256 is `de38b6f1e088a5ee60e432b56ff11ba3ddbfa83abd42060d3840c244166ec433`.

## Contract experiment and its limit

Kani's experimental `proof_for_contract` checks an `ensures` condition on a
no-argument boolean-result wrapper around this exact case. It does not annotate
or replace the production merge or collection operations. No contract is
assumed, no `stub_verified` is used, and no production call site is rewritten.
This is a direct check of this fixture's contract, not an established reusable
collection contract.

Annotations were accepted and compilation completed. The sampled live process
was CPU-active in `goto-instrument`; the log did not reach a selected-harness
line, a SAT-solving stage or a verification summary before termination. The
contract was not checked to completion. Its must-fail Kani companion was skipped,
so the native control does not establish formal-stage reachability.

The runner stopped after 180.261 seconds with
2.18 GiB peak sampled aggregate RSS,
within an 8 GiB cap, using unwind 16 and default checks. Underlying termination
was SIGTERM at the wall limit; resource runner exited 124 and batch runner
exited 2 for an incomplete experiment. Compile-time warnings about unsupported
constructs were retained; no successful reachability or safety verdict is
inferred from them or from compilation alone.

This attempt identifies a pre-verification instrumentation bottleneck for this
contract configuration. It does not prove that checked contracts are unavailable
in Kani, nor that this structural property is false. The contract must remain
unverified and unusable as a premise. Do not spend another unchanged long run
or substitute unchecked collection specifications on the strength of this test.

## Integrity and regression

The existing finite native matrix was replayed after this work and matched its
saved JSON exactly: 3,960 access observations and 1,800 structural checks, zero
mismatches. The temporary native example and additional Kani hook were removed
or restored. Production files, original smoke harness and corrected lockfile
passed the post-run manifest check. No commits or pushes were made.

## Artifacts and reproduction

- `verification/kani/protected_entry_preservation.rs`: shared fixture, contract
  proof harness and false-removal control.
- `scripts/run-protected-entry-case.py`: native build, run and control checks.
- `scripts/profile-kani-stages.py --preservation`: bounded contract attempt.
- `evidence/PROTECTED_ENTRY_PRESERVATION.json`: observations, commands, hashes,
  exit codes, resources and matrix replay result.
- `.tools/native-protected-preservation/`: native build log, outputs and snapshot.
- `.tools/kani-protected-preservation/`: contract log, resources, snapshot,
  worktree diff and instrumentation-process observation.

Source `.tools/activate.sh` from `/workspace/safety` before running either script.
Both runners refuse to overwrite prior output directories. Preserve those
results before repeating. Code targets Codex
`360319d8dee62d87e2d59fc0c21805d79519cfed`, with Rust 1.99.1 for native execution,
Kani 0.68.0, verifier nightly-2026-08-21 and CBMC 6.11.0.

The chosen milestone is structural preservation. Protected-descendant access,
resolver precedence and runtime sandbox enforcement remain outside this case.
The broader actual-code theorem remains open.
