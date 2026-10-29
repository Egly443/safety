# Selected milestone: protected-entry preservation

The fixture is fixed before execution:

| Role | URI | Access |
|---|---|---|
| Base root | `file:///` | Read |
| Base protected child | `file:///w/p` | Read |
| Additional workspace grant | `file:///w` | Write |

Call the actual pinned `effective_file_system_sandbox_policy`. Require that the
result remains restricted, contains both original entries in their original
prefix order, contains exactly one copy of the workspace grant, has three
entries total, and preserves the absent glob depth. Entry preservation uses
the actual type's equality semantics, including access and missing-path fields;
it is not a claim about arbitrary equivalent URI spellings.

The companion control falsely claims the protected read entry was removed.
It must fail at that assertion. A native control is regression evidence; a
Kani control establishes formal-stage reachability only if it completes.

First build and run the fixture natively, checking both exit codes and JSON.
Then check its no-argument boolean-result contract with Kani's experimental
`proof_for_contract` mechanism, 180 seconds, 8 GiB and unwind 16, retaining all
default checks. Run the Kani false-removal control only if the positive contract
proof completes. Do not use `stub_verified`, assume the contract, replace
production collection operations, or alter production function bodies.

This checks contract support and the concrete preservation property together;
it does not yet create reusable contracts at collection call sites. A timeout
leaves this contract unverified and unusable as a premise for composition.

This milestone deliberately excludes access resolution, descendant queries,
runtime sandbox behavior and arbitrary policies. The broader scoped claim in
`SCOPED_CLAIM.md` remains separate. No longer run or hardware increase is part
of this experiment.

The shared native/Kani fixture is `kani/protected_entry_preservation.rs`.
Run the native case using `scripts/run-protected-entry-case.py`; run the formal
gate with `python3 scripts/profile-kani-stages.py --preservation` after sourcing
`.tools/activate.sh`. Preserve previous output directories before rerunning.
