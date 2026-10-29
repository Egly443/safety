# Next actual-code milestone

Target: an ancestor workspace write grant preserves a more-specific explicit
read-only child, while permitting ordinary workspace writes. Assume normalized
local POSIX URIs, a restricted base, one workspace, one protected child, no globs,
no metadata defaults, and no explicit write grant at/beneath the protected child.
Explicit protected-path overrides are separate behavior, not counterexamples to
this scoped claim. The original Lean denial-precedence model remains abstract;
no refinement correspondence is claimed without separately justified semantics.

Execute these gates against pinned, unchanged Codex functions:

1. Real entry equality and clone operations on special-root read/write entries.
2. Clone and equality on one parsed `file:///w` URI.
3. One-entry base plus one root-write grant, asserting scalar/variant fields
   rather than whole-entry equality in the postcondition. Symbolic base access
   covers insertion and deduplication. This intentionally narrower postcondition
   does not claim full policy equivalence or containment.
4. Fixed resolver decision using read `/w/p` and write `/w`, without merging.
   Check protected-root denial and workspace-root permission. This fixture omits
   the original root-read entry and does not cover protected descendants.
5. Attempt composition/symbolic widening only after merge and resolver gates
   complete. No unchecked contracts, stubs, reduced unwind bounds, or disabled
   safety checks. Stop at a concrete unresolved gate rather than call it proved.

Each selected operation has an intentionally false assertion. Run its control
after a successful positive stage; a timeout does not establish reachability.
Use 180 seconds and 8 GiB sampled aggregate RSS per probe, one compilation job,
cached target directory, and all default checks with unwind 16. Preserve earlier
results. Record exact commands, hashes, resource outcomes and check summaries.

Keep the existing native matrix as a regression baseline. Run its retained
executable and compare all observations to saved evidence after harness work.
This regression replay does not establish a new symbolic proof.
