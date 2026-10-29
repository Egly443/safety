Pinned sources and a disposable offline Linux VM are available. Source
`scripts/env.sh` for the installed tools; run `bash scripts/vm-smoke.sh` from
the project root for a fresh snapshot boot and automatic shutdown.
The boot smoke test passed on 2026-10-28 with Ubuntu kernel 6.8.0-147-generic,
ext4, QEMU 8.2.2 TCG emulation, and no network devices. The kernel configuration
SHA256 is cf8454bc2e67effab87a5bff3c39042f2d8d106b6a777c4302e52f50d23b7400.
The image and tools are pinned in `prerequisites.lock.json`; serial output is
in `evidence/vm-boot.log`. VM bootstrap inputs are in `integration/vm-seed/`.
The runtime suite passed all 16 containment assertions and the installed CLI
version check: 17/17 checks on 2026-10-29. See `TESTING.md` for the exact
configuration and reproduction commands, and `../evidence/containment-results.json`
for per-case results and the generated bubblewrap execution trace.
Required cases: permitted write control; denied outside-workspace write;
protected subtree; symlinks; missing paths; setup failure; descendant writes.
Record executable hashes, generated arguments, inherited descriptors, kernel
build/configuration, filesystem type, network denial and PID isolation.
Run against disposable fixtures in the VM. Existing host bubblewrap 0.9.0 is
not the verification target. Bubblewrap 0.13.1 and the pinned Codex Linux sandbox
helper are built locally and installed root-owned in the disposable test VM,
along with the source-built full Codex CLI. The final VM shut down cleanly.
