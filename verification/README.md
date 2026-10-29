The first actual-code attempt is specified in `CONTRACT.md`. It targets the
additional-permission merge and URI-based write-access check in pinned Codex.
`kani/narrow_policy.rs` is currently a fixed concrete feasibility harness, not
yet the bounded symbolic proof. No replacement policy implementation is used.

Run `bash scripts/kani-feasibility.sh` from the project root after prerequisites
and pinned sources are installed. A detached `.tools/kani-source` worktree gets
only a `cfg(kani)` harness hook and the documented lockfile version correction.
The verified production function files are checked against the pinned commit.
`evidence/kani-source-manifest.json` records the source and harness hashes.

The run guard stops at 20 minutes, 4 GiB sampled aggregate RSS, or its disk-space
allowance. Compilation uses one job and a separate target directory. Do not run
the VM or native CLI build concurrently. Resource stops and compiler failures
are inconclusive, not failed safety properties. Raw output and resource records
are in `evidence/kani-feasibility.log` and `evidence/kani-feasibility-resources.json`.
Network access may be needed for locked dependencies on the first run; set
`CARGO_NET_OFFLINE=true` when the required cache is populated.

An offline metadata attempt initially stopped because `alsa 0.11.0` was not
cached. That outcome is retained separately as attempt 1. It did not reach
compilation or proof checking. The subsequent large-path attempt compiled the
actual crate, reached checking, and hit the 4 GiB RSS guard. The current shorter
fixture, with unwind 16 and all unwinding checks retained, reached checking but
hit a five-minute follow-up limit. Neither produced a proof or counterexample.
The large fixture is retained in `attempts/large_path_smoke.rs`.

See `../evidence/KANI_CHECKPOINT.md` for measurements and limitations, and
`CLOUD_RETRY.md` for a controlled larger-resource retry. No Cloud job has started.
