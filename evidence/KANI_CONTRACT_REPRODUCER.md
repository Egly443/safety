# Candidate Kani contract performance issue: tiny byte-vector check

This is a local draft, not an externally submitted issue. No root cause is
claimed. The reproducer has no third-party or Codex dependencies.

Observed environment: Linux x86-64, 32 GiB memory cgroup, four-core CPU quota.
Kani 0.68.0, verifier Rust nightly-2026-08-21 (1.100.0-nightly, 8925ea358),
CBMC 6.11.0. See versions.txt for exact output. The Kani distribution bundle
was previously verified against its repository-pinned SHA256.

The source clones a two-element Vec<u8>, inserts a third element if absent,
and checks length, original-prefix retention and uniqueness of the grant.
Ordinary mode asserts the returned boolean; contract mode verifies an ensures
condition on the same boolean. Neither has preconditions or replacement stubs.
The exact three changes are in ordinary/mode.diff. Both retain unwind 16 and
all default checks and use the same experimental feature flag.

Observed:
- Ordinary check: 4.006 seconds, zero of 569 checks failed (16 unreachable).
- Ordinary false control: 4.009 seconds, exactly its intended assertion failed.
- Contract check: 40.069 seconds, guard stopped at 8.19 GiB sampled RSS; no
  verification result. The 8 GiB guard samples once a second, so overshoot is
  expected. A selected harness and CBMC symbolic execution are logged.
- Contract control: unrun because the positive contract did not complete.

Contract-only log messages include:
```
kani::internal::enter_contract_clause: ... saturating_add ... not enough arguments, inserting non-deterministic value
kani::internal::exit_contract_clause: ... saturating_sub ... not enough arguments, inserting non-deterministic value
```
The contract log ends after symbolic execution and postprocessing; it does not
reach a SAT-solving result. These warnings may be relevant but causation is
unproven. Please investigate whether this contract shape is expected to exhibit
this behavior and whether the internal call-signature diagnostics indicate a
lowering/modeling issue.

## Reproduce

Install/select the exact Kani and verifier toolchain above. Keep normal TLS and
artifact verification when installing; installation is outside this package.
Use a Linux workspace with at least 10 GiB free disk for the supplied resource
guard and sufficient memory for the 8 GiB test. Preserve proxy/trust settings.
Use a fresh copy of this package for each run to retain evidence. From its root:

```bash
python3 scripts/run-limited.py --seconds 180 --rss-gib 8 --cwd "$PWD/ordinary" --record "$PWD/ordinary/repeat.resources.json" --log "$PWD/ordinary/repeat.log" -- kani "$PWD/ordinary/fixture.rs" --exact --harness check_probe -Z function-contracts
python3 scripts/run-limited.py --seconds 180 --rss-gib 8 --cwd "$PWD/ordinary" --record "$PWD/ordinary/control-repeat.resources.json" --log "$PWD/ordinary/control-repeat.log" -- kani "$PWD/ordinary/fixture.rs" --exact --harness probe_must_fail -Z function-contracts
python3 scripts/run-limited.py --seconds 180 --rss-gib 8 --cwd "$PWD/contract" --record "$PWD/contract/repeat.resources.json" --log "$PWD/contract/repeat.log" -- kani "$PWD/contract/fixture.rs" --exact --harness check_probe -Z function-contracts
```

The false control is expected to exit 1. A resource stop exits 124 and is
inconclusive. A selected/completed harness and its check summary are required;
a bare zero exit or zero-test run is insufficient. Do not disable unwinding or
safety checks to make a comparison pass. The minimal source is retained in
ordinary/fixture.rs and contract/fixture.rs alongside original raw evidence.
