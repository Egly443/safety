# Runtime verification results — 2026-10-29

Codex 0.165.0 CLI and Linux sandbox helper were built from the pinned source.
Bubblewrap 0.13.1 was built from its pinned source. All three were installed
root-owned, mode 0755, outside the writable fixture in a disposable offline VM.
Guest executable hashes match the recorded host build hashes.

All 17 checks passed. The separate execution trace also completed successfully
and records the generated bubblewrap mount and namespace arguments.

| Check | Result |
| --- | --- |
| installed-cli-version | PASS |
| unsandboxed-outside-positive-control | PASS |
| permitted-workspace-write | PASS |
| outside-workspace-denied | PASS |
| protected-subtree-denied | PASS |
| symlink-outside-denied | PASS |
| symlink-protected-denied | PASS |
| missing-workspace-path-created | PASS |
| missing-outside-path-denied | PASS |
| descendant-write-denied | PASS |
| network-socket-denied | PASS |
| pid-namespace-isolated | PASS |
| setup-failure-does-not-execute | PASS |
| missing-bwrap-does-not-execute | PASS |
| missing-bwrap-no-side-effect | PASS |
| setup-failure-no-side-effect | PASS |
| protected-sentinel-unchanged | PASS |

Configuration: Ubuntu Minimal image 20261027, Linux 6.8.0-147-generic,
ext4, QEMU TCG, no network device, UID/GID 1000 for test commands, restricted
network policy, default helper PID isolation, one writable workspace and an
explicit read-only protected subtree. AppArmor's unprivileged-user-namespace
restriction is disabled in this fixture. The pinned kernel is booted directly
with the offline network-wait service masked. The VM shut down cleanly.

The release lock correction changes only local workspace package versions;
external records and every other field match upstream. The original upstream
lockfile is restored. The CLI is stripped and linked with one LLD thread after
the compiler exits; the complete link command is retained.

These are finite runtime checks of the actual helper with an explicit profile,
not a general containment proof or proof of CLI configuration translation.
Kani verification of Codex policy code, C/kernel verification, exhaustive path
and race analysis, and a refinement to the Lean model remain outside this result.

Detailed evidence: `containment-results.json`, `containment-vm.log`,
`build-provenance.json`, `Cargo.lock.build`, and `cli-link-command.json`.
Reproduction and coverage: `../integration/TESTING.md`.
