# Codex–bubblewrap write-confinement verification

Target: Codex 0.165.0 plus upstream bubblewrap 0.13.1, native Linux x86-64,
workspace-write, one workspace with protected subtrees, network disabled,
default PID isolation, trusted system bubblewrap outside the writable workspace.
Exact source commits are in `sources.lock.json`.
Both HEADs and tags were independently checked against upstream on 2026-10-28
using `make fetch`; both match the locked commits.

## Current verification results (2026-10-29)

The actual-code finite policy matrix passed **3,960 access observations and
1,800 structural checks** across 36 fixtures. It checks ancestor grants,
protected descendants, similar-name siblings, duplicate grants and explicit
protected-path overrides using the pinned Codex transformation and resolver.
See [the matrix report](evidence/POLICY_MATRIX.md),
[complete observations](evidence/policy-matrix.json), and
[the scoped claim](verification/SCOPED_CLAIM.md). This exhausts its declared
finite domain; it is not a universal containment proof.

Small ordinary Kani probes completed for URI parsing, selected equality and
cloning operations, empty-policy grant insertion, and identity cases, with
deliberate failure controls. Nonempty merges and fixed resolver checks remain
inconclusive. The end-to-end retry reached its 60-minute wall limit at 14.87 GiB
sampled RSS. See [staged results](evidence/KANI_STAGES.md),
[component results](evidence/KANI_COMPONENTS.md), and
[the cloud retry](evidence/CLOUD_RETRY_60M.md).

The experimental contract path has a standalone model-validation reproducer:
a constant-returning function triggers an internal function-type inconsistency
under Kani 0.68.0 / CBMC 6.11.0. Default-mode positive and false controls behave
as expected, so no false proof is claimed. Contract-based composition is paused
pending a validated tool repair. See [the investigation](evidence/KANI_CONTRACT_INVESTIGATION.md)
and [reproducer archive](evidence/kani-contract-validation-reproducer.tar.gz).
The earlier 17 VM checks below are historical runtime evidence from another
environment, not checks rerun in this cloud instance.

## Cloud workflow

After the environment's saved installation script has prepared repository-local
tools, select them with `source scripts/cloud-env.sh`. That tracked helper is
equivalent to the generated `.tools/activate.sh` used in recorded cloud runs.
For global tool installations, use `source scripts/env.sh` instead.

The native and diagnostic runners require the prepared pinned dependency
worktree at `.tools/kani-source`. To initialize it when absent:

```bash
source scripts/cloud-env.sh
make fetch
mkdir -p .tools
git -C upstream/codex worktree add --detach "$PWD/.tools/kani-source" 360319d8dee62d87e2d59fc0c21805d79519cfed
python3 scripts/prepare-kani.py
```

This initialization applies only the documented workspace-version lockfile
correction and original Kani harness hook in the dependency worktree. It does
not change production function bodies. Skip worktree creation when it already
exists; `python3 scripts/prepare-kani.py --check` checks prepared inputs.

Then choose a bounded workflow:

```bash
python3 scripts/run-policy-matrix.py
python3 scripts/run-protected-entry-case.py
python3 scripts/profile-kani-stages.py --components
python3 scripts/diagnose-kani-contracts.py
```

These commands are alternatives, not a required all-suites run. See each plan
under `verification/` for budgets and scope. Runners refuse to overwrite prior
output directories; the matrix runner also protects saved evidence files.
Preserve those files before a repeat. Contract diagnostics intentionally record
tool failures and do not establish a policy proof. Local tools, caches and raw
working logs remain ignored; summaries and standalone report bundles are tracked.
For a repeated staged probe, `--output-dir .tools/<fresh-name>` keeps the
original stage evidence in place.

## Local commands

```
make doctor
make proof
make fetch
source scripts/env.sh
make doctor
bash scripts/vm-smoke.sh
make build-sandbox
make build-cli
python3 scripts/extract-vm-kernel.py
make containment
```

Lean is pinned to the locally available 4.34.1 and has no external dependencies.
The `.venv` Python environment is isolated; pytest 9.2.0 is installed.
Reproduce its package versions with `.venv/bin/python -m pip install -r requirements-dev.lock`.
`make fetch` requires GitHub access and validates both HEAD and tag against the
expected commits. It refuses mismatches and does not overwrite existing trees.

## Assurance boundary

The Lean proof states that granting workspace writes preserves protected-subtree
denials for every path in that subtree. A positive-control theorem establishes
that an unprotected granted path is writable. These are proofs about an abstract
policy whose semantics give protected paths precedence. They do not establish
that Codex constructs that policy or that bubblewrap/Linux enforce it.

Path normalization, symlinks, renames, races, mount construction, inherited file
descriptors and kernel behavior remain outside the model. The runtime suite now
provides finite integration evidence for selected cases; it is not a containment
proof. Small actual-code Kani component checks have completed, but the intended
nonempty-merge and path-containment theorem and C verification remain open.

## Open verification work

- Complete verification of the selected real policy transformation and connect its Kani contract to the model.
- The actual Codex crate compiles under Kani, but the smoke harness remains
  inconclusive after resource-limited runs. See `evidence/KANI_CHECKPOINT.md`
  and the current reports above for the results and limitations. Additional
  unchanged long runs are not the recommended next step.

## Historical environment check (2026-10-28)

GitHub and PyPI DNS and HTTPS checks succeeded with TLS verification enabled.
No proxy variables or managed `/etc/codex/network-policy.json` are present;
the managed environment-status tool is unavailable, so managed policy and
credential readiness could not be established.
`make fetch` verified both pins and `make proof` completed successfully.

Installed Rust 1.99.1 with clippy, rustfmt and rust-src. Kani 0.68.0 uses its own
nightly-2026-08-21 toolchain (Rust 1.100.0-nightly); its installation smoke harness
passes. The selected actual Codex crate also compiles under Kani; verification
of its policy smoke harness remains inconclusive.
Meson 1.12.1 and libcap 2.66 development files are installed locally, and the
pinned bubblewrap 0.13.1 builds into `.tools/bin/bwrap` with SELinux disabled.
Source `scripts/env.sh` to select local tools; `make doctor` then passes all checks.
The local binary is a build artifact, not the trusted system binary required for
containment verification. The host bubblewrap remains 0.9.0.

Ubuntu Minimal 24.04 image build 20261027 is downloaded and SHA256-checked.
`scripts/vm-smoke.sh` starts a disposable snapshot with no network devices, using
QEMU 8.2.2 software emulation because `/dev/kvm` is absent. The cloud-init seed
records kernel, root filesystem type and kernel configuration hashes to the
serial log, then powers off. VM files live in ignored `.tools/vm/`.
The boot smoke test passed; exact image, kernel and configuration hash are recorded
in `prerequisites.lock.json`. Bootstrap inputs are in `integration/vm-seed/`.
The full Codex CLI and Linux sandbox helper have built successfully from source.
The release lockfile needs
only local package version corrections from 0.0.0 to 0.165.0; all external records
and other fields are unchanged. The adjusted lock and provenance are recorded in
`evidence/Cargo.lock.build` and `evidence/build-provenance.json`.
The CLI build retains object files before linking, allowing the Rust compiler to
exit before a single-threaded LLD link. The capture stage deliberately returns 99;
the build command succeeds only after the standalone link and version check.
The CLI is stripped of symbols. Its exact link arguments are recorded in
`evidence/cli-link-command.json`.

All 16 runtime containment assertions passed in the disposable VM, with trusted
root-owned helper and bubblewrap executables outside the workspace. These cover
positive write controls, outside/protected-path denials, symlinks, missing paths,
descendants, network socket denial, PID isolation, and startup failures.
Results and generated bubblewrap arguments are in
`evidence/containment-results.json`; see `integration/TESTING.md` for configuration,
reproduction commands and limitations. Full policy verification remains pending.
The full CLI was also installed root-owned and its version check passed: the
final run completed 17/17 checks on 2026-10-29 and shut down cleanly. A concise
summary is in `evidence/RESULTS.md`; guest binary hashes match the host build.

The supplied transcript is ignored by default to keep conversation material out
of future commits.
