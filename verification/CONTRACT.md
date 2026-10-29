# First actual-code verification attempt

Status: actual-code compilation established; verifier feasibility remains
inconclusive under the first local resource budgets. See `../evidence/KANI_CHECKPOINT.md`.

The initial goal is a narrow, reproducible policy-plane result suitable as the
foundation for a defensible paper. Neither novelty nor publishability is yet
established. The existing 17 VM checks remain separate runtime evidence.

## Actual code and call path

Pinned Codex commit: `360319d8dee62d87e2d59fc0c21805d79519cfed`.

The transformation is `effective_file_system_sandbox_policy` in
`codex-rs/sandboxing/src/policy_transforms.rs`, including its private merge helper.
The observation is `FileSystemSandboxPolicy::can_write_path`, including
`resolve_access`, in `codex-rs/protocol/src/permissions.rs`. These use the actual
`PathUri` and policy types. No replacement resolver, path model, stubs, or
ignored unsupported operations are permitted in the first attempt.

The transformation is called by `effective_permission_profile`; the sandbox
manager invokes that function in `codex-rs/sandboxing/src/manager.rs`. Direct
callers also include the apply-patch permission handler. This is an
additional-permission grant operation, not a proof of every initial workspace
configuration constructor or of command execution.

## Intended bounded claim

For a restricted base policy with root read access and an explicit read-only
protected child P of workspace W, adding a write grant for ancestor W leaves
queries under P unwritable. Ordinary queries under W outside protected regions
become writable. Each result must state its precise generated input domain.

Initial assumptions:

- Lexically normalized local POSIX file URIs; proper component-prefix
  relationships. This does not assert filesystem canonicalization.
- One workspace and one explicit protected child; no globs or special-path tokens.
- The added grant targets W only, not P or a descendant of P.
- No competing explicit write grant at or beneath P.
- Initial ordinary names exclude the special metadata names `.git`, `.codex`,
  `.agents`, and `.aws`; their separate default-protection behavior is deferred.
- No filesystem lookup, symlinks, aliases, mount behavior, inherited FDs, or races.

Codex resolves specificity before access precedence. More-specific grants, and
some same-target grants, can intentionally override read restrictions. Thus the
unconditional denial predicate in the existing Lean model does not yet constitute
a refinement of Codex. That correspondence requires the assumptions above.

## Feasibility gate and resources

First compile and verify a fixed concrete instance through the actual public
transformation and observation. This is a smoke harness, not the bounded theorem.
Only after it works should symbolic inputs, coverage and deliberate counterexamples
be added. A compiler/verifier failure or exhausted budget is inconclusive.

Use a detached source worktree with a `cfg(kani)` harness hook only. Preserve the
production function bodies and the original source checkout. Record source hashes,
overlay, command, tool versions and dependency lock. The established release-lock
correction changes workspace versions only.

One build job, one harness, no concurrent VM or native CLI build. Initial run:
20 minutes wall time, 4 GiB sampled aggregate process-group RSS, and an 8 GiB
free-space consumption allowance with a 10 GiB minimum free-space floor. The RSS
guard is sampled, not a kernel-enforced hard limit. Do not ignore loop-unwinding
failures or unsupported operations to obtain a successful result.

Cloud execution is authorized as an option, but no cloud executor is attached in
this session. If the local gate fails, report the precise failure and options
before attempting a weaker extraction or changing the claim.
