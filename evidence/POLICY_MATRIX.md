# Finite actual-code policy matrix result

**Passed: 3,960 access observations and 1,800 structural checks; zero mismatches.**
This is current-instance finite native execution evidence for the central policy
behavior. It is not a symbolic or universal containment proof.

## Fixed domain and results

The pre-run plan is `verification/POLICY_MATRIX_PLAN.md`; executable expectations
are explicit boolean tables in `verification/policy_matrix.rs`. No expected values
were changed after the run. All 36 fixtures, ten scenarios, and eleven query
categories executed. Coverage validation checked uniqueness of every
(fixture, scenario, query category), all 110 observations per fixture, all 396
observations per scenario, and both allowed and denied outcomes.

| Grant scenario | Allowed observations | Denied observations | Mismatches |
|---|---:|---:|---:|
| `none` | 0 | 396 | 0 |
| `empty` | 0 | 396 | 0 |
| `workspace` | 180 | 216 | 0 |
| `duplicate_workspace` | 180 | 216 | 0 |
| `reapply_workspace` | 180 | 216 | 0 |
| `protected_only` | 144 | 252 | 0 |
| `workspace_then_protected` | 324 | 72 | 0 |
| `protected_then_workspace` | 324 | 72 | 0 |
| `workspace_then_descendant` | 252 | 144 | 0 |
| `descendant_then_workspace` | 252 | 144 | 0 |

Total: 1836 allowed and 2124 denied observations.
Every scenario also passed five structural checks per fixture: original policy
preservation, expected entry count, original-entry retention, policy kind, and
glob-depth preservation. Duplicate and reapplied workspace grants produced the
same expected behavior and no extra entries.

## Meaning of the result

For every declared fixture, adding write permission for the workspace ancestor
left the protected child, its file, its deeper descendant, and its file-child
unwritable. Ordinary descendants and similarly named unprotected siblings were
writable. Outside paths and similarly named workspace siblings stayed
unwritable. No-grant and empty-grant scenarios supplied negative baseline controls;
ordinary-write observations supplied positive controls. Both base-entry orders
were exercised.

Explicit write grants at the protected path allowed writes there and beneath it;
explicit grants to its `f` descendant allowed writes under `f` while leaving the
protected root and a different descendant unwritable. Reversing the added-grant
order preserved these outcomes. These are documented override cases, deliberately
separate from the ancestor-only claim. They reinforce why unconditional protected
path precedence in the abstract Lean model is not yet a refinement of Codex.

## Actual code and provenance

The example calls `effective_file_system_sandbox_policy` from the real
`codex-sandboxing` crate and `FileSystemSandboxPolicy::can_write_path`, with the
real `PathUri` parser. There are no stubs, replacement prefix resolvers, or
modified production function bodies. Code is pinned to
`360319d8dee62d87e2d59fc0c21805d79519cfed`.

Native build used Rust 1.99.1, `cargo build --locked`, the previously documented
workspace-version-only lock correction, two compiler jobs, and debug information
disabled. Build completed in 194.302 seconds with
2.37 GiB peak sampled process-group RSS.
The build guard allowed 900 seconds and 12 GiB. Native execution completed
successfully within its 60-second limit. Both build and executable exited 0.

The temporary example file was removed afterward. The original production hashes,
Kani hook, lockfile and original harness passed the post-run manifest check. No
production source changes, commits, pushes, or new project worktrees were made.

- `evidence/policy-matrix.json`: every query, expected/actual result and structural check.
- `evidence/policy-matrix-provenance.json`: commands, source hashes, matrix hash, executable hash and exit codes.
- `.tools/policy-matrix/build.log` and `build-resources.json`: build evidence.
- `scripts/run-policy-matrix.py`: bounded runner and completeness checks.

Output SHA256: `ea3d60797d2d0e011eedfe400c4c9f7e2025d80c5849b7c2db3b2eb5f923b9f0`.

## Reproduction and limits

Use the commands and preservation instructions in
`verification/POLICY_MATRIX_PLAN.md`. Existing evidence is protected against
accidental overwrite. The executable is retained at
`.tools/native-policy-target/debug/examples/policy_matrix` for inspection.

The result exhausts only the enumerated normalized POSIX URI fixtures, not all
paths or all policy shapes. Filesystem lookup, symlinks, aliases, races, native
sandbox enforcement, globs, metadata defaults, Windows/UNC paths, encodings and
arbitrary depths remain outside the domain. Read-only entries here are not
unconditionally overriding denials: explicit same-target or descendant grants
can override them, as the matrix confirms. The unresolved end-to-end Kani run
remains inconclusive. The next formal-verification target can now be checked
against this finite behavioral oracle while isolating equality and deduplication.
