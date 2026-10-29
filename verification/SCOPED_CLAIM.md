# Intended actual-code claim and current evidence boundary

Pinned implementation: Codex `360319d8dee62d87e2d59fc0c21805d79519cfed`.
Transformation: `effective_file_system_sandbox_policy`; observation:
`FileSystemSandboxPolicy::can_write_path`, with real `PathUri` semantics.

## Claim to establish

Let W be a workspace URI, P a proper component-descendant of W, Q a path at or
below P, and O an ordinary path at/below W outside P. Start with a restricted
policy containing root read access and an explicit read entry for P. Add only
a write grant for W. The intended result is that Q remains unwritable and O
becomes writable. No additional entries, globs, missing-path behaviors or glob
depth overrides are included in this first domain.

Assume normalized local POSIX file URIs; component ancestry rather than string
prefixes; one workspace; no user-home or temporary-directory context; no explicit
write grant at or below P; no special metadata names `.git`, `.codex`, `.agents`
or `.aws`. Filesystem canonicalization, symlinks, aliases, races, actual sandbox
enforcement, Windows/UNC paths and arbitrary URI encodings are outside this claim.
Any symbolic result must state its finite path/domain bounds explicitly.

## Overrides and the Lean model

The separate native matrix confirms that explicit writes at P or beneath P can
override read restrictions. Those cases violate this claim's grant assumptions;
they are not counterexamples to this scoped ancestor-only claim.

The existing Lean `denied` predicate always takes precedence over `writable`.
Codex instead resolves specificity and access precedence. The existing Lean
theorem remains a theorem about that abstract model. The assumptions above do
not by themselves prove a refinement relation. A source-aligned resolver model,
or separately verified actual-code contracts connecting both semantics, is
still required. Do not describe the current Lean proof as a Codex proof.

## Evidence that must stay distinct

- The native matrix exhausts its 36 fixtures, ten grant scenarios and eleven
  query categories. It supplies implementation regression evidence only for
  that domain, including explicit override cases outside the claim above.
- Component Kani results cover their declared entry/URI fixtures and symbolic
  choices. They do not compose automatically into a transformation/resolver
  proof. Intentionally false controls establish reachability for completed
  stages only; skipped or timed-out controls do not establish it.
- A nonempty special-root merge is a diagnostic gate, not a POSIX protected-path
  theorem. The fixed-resolver probe intentionally omits root read access and
  queries the protected root and workspace root, not arbitrary descendants.
- Resource exhaustion and an absent verifier summary are inconclusive. No
  contracts may be assumed as a replacement for the actual implementation
  unless separately checked with their exact preconditions and applicable
  input domain. Retain unwinding and safety checks.
