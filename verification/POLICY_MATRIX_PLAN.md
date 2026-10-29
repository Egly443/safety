# Finite policy regression matrix

Use the actual `effective_file_system_sandbox_policy` and `can_write_path` at
Codex commit `360319d8dee62d87e2d59fc0c21805d79519cfed`. Do not stub path parsing,
policy merging, or access resolution. Preserve the original Kani smoke fixture.

1. Enumerate 36 fixtures: workspace `/w`, `/work`, or `/a/w`; protected name `p`,
   `protected`, or `keep`; ordinary name `q` or `free`; both base-entry orders.
   Base is restricted, with root read access and protected-child read access.
2. For each fixture, enumerate ten grant scenarios: no profile, empty profile,
   workspace grant, duplicate workspace grant, reapplied workspace grant,
   protected-only grant, workspace and protected grants in either order, and
   workspace and protected-descendant grants in either order.
3. Query eleven named categories: workspace, ordinary root/file, protected
   root/file/deep descendant/file-child, similar-name protected sibling
   root/file, outside path, and similar-name workspace sibling. Use explicit
   expected boolean tables, not a replacement path-prefix resolver.
4. Require 3,960 access observations and 1,800 structural checks. Baseline
   denials and ordinary-write controls must execute. For explicit protected
   grants, expect the documented same-target/more-specific write overrides;
   these are separate cases outside the original ancestor-grant-only claim.
5. Build a native example in the existing prepared dependency worktree using
   the corrected locked workspace versions. Do not modify production code.
   Use two compiler jobs, 12 GiB sampled RSS and 15 minutes for a cold build.
   Run the resulting executable with a 60-second limit. Remove only our
   temporary example afterward and recheck source integrity.
6. Save all actual/expected observations, counterexamples if any, commands,
   source and executable hashes, tool version, and build/resource evidence.
   A compile failure, partial matrix, or timeout is not a passing result.

Scope: finite, normalized local POSIX URI policy-plane behavior. This excludes
filesystem lookup, symlinks, races, actual sandbox execution, globs, special-path
tokens, metadata defaults, Windows/UNC paths, arbitrary depths and arbitrary
Unicode/encoded spellings. This is exhaustive enumeration of the declared
fixture domain, not a symbolic theorem or a refinement proof of the Lean model.

Run from `/workspace/safety`:

```bash
source .tools/activate.sh
python3 scripts/run-policy-matrix.py
```

The runner refuses to overwrite prior matrix evidence. Preserve previous output
files and `.tools/policy-matrix` before repeating a run.
