# Runtime containment checks

Run `source scripts/env.sh`, `make build-sandbox`,
`python3 scripts/extract-vm-kernel.py`, then `make containment`.
The runner packages the actual Codex Linux sandbox helper built from the pinned
release source, bubblewrap 0.13.1, required shared libraries, and strace onto a
read-only ISO. Cloud-init installs executables root-owned under `/usr/local/bin`
and libraries outside the writable fixture. Each run uses a disposable disk
snapshot of the checksum-pinned Ubuntu image, QEMU TCG, and no network device.
No host directory is shared with the guest.

Use `make build-cli` to build the full CLI as well as the helper. If `.tools/bin/codex`
is present, the runner also installs it root-owned and checks its version, producing
17 checks in total. The CLI build captures temporary link inputs and deliberately
exits the capture linker with status 99; `scripts/link-cli.py` then runs the actual
link without retaining the compiler in memory and verifies the executable version.

The test commands run as UID/GID 1000 without supplementary groups. They receive
root read access, write access to one workspace, read-only access to an explicit
protected child, and restricted networking. The default helper PID isolation is
retained. A raw outside-workspace write establishes that ordinary DAC permissions
would permit writes before applying the sandbox. A sandboxed workspace write is
the positive control for successful startup. Denial cases catch permission-related
OS errors inside the sandbox, so a startup crash cannot count as a passing denial.
Other cases cover existing protected contents, symlink aliases, new paths,
descendant execution, socket creation, PID namespace identity, invalid-profile
startup failure, and actual bubblewrap unavailability. Removing PATH alone does
not remove a discoverable sibling bubblewrap fallback; the latter test also
renames the guest's bubblewrap temporarily and restores it afterwards.

The pinned image's kernel is extracted without mounting it and booted directly.
The command line masks `systemd-networkd-wait-online.service`, which otherwise
hangs the offline fixture. AppArmor's unprivileged user namespace restriction is
disabled inside this disposable guest to permit bubblewrap's namespace creation;
that setting and the namespace limit are recorded with the results.

`evidence/containment-results.json` contains individual results, arguments,
stdout/stderr, executable hashes, ownership, kernel and sysctl settings. The
permitted write records inherited descriptors inside the command. A separate
strace run records actual exec arguments including bubblewrap's generated mount
arguments. Assertions run without strace; instrumentation is diagnostic only.
`evidence/containment-vm.log` contains the full serial transcript.

This is a finite runtime regression suite for this configuration, not a general
containment proof. It does not establish a Kani-to-Lean refinement, verify C or
the Linux kernel, exhaust path normalization or rename races, test every inherited
file descriptor, or cover other kernels, privilege configurations, architectures,
or network-enabled policies. The Kani smoke harness only checks installation.
