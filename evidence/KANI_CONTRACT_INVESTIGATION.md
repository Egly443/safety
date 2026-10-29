# Contract pipeline investigation

**Confirmed generated-model inconsistencies in the installed Kani 0.68.0 /
CBMC 6.11.0 contract path. Reduced to a six-line constant-returning function.**
This is a tool-model failure, not a failing Codex policy assertion. No production
code or installed verifier files were modified. No false proof was observed.

## Minimal model-validation reproducer

```rust
#[kani::ensures(|r: &bool| *r)]
fn constant() -> bool { true }

#[kani::proof_for_contract(constant)]
fn check_constant() { let _ = constant(); }
```

Run with all default checks plus additional model validation:

```bash
kani contract.rs --exact --harness check_constant --keep-temps --run-sanity-checks --default-unwind 16 -Z function-contracts -Z unstable-options
```

Observed in about one second: Kani exits 1 after CBMC reports an invariant
failure, status 134, with `symbol_expr_type_matches_symbol_table`. In this
single-function reduction the mismatched symbol is `ContractClauseGuard::drop`.
The matched ordinary source (without ensures, with a proof harness asserting
`constant()`) passes one check with validation enabled. There is no heap,
loop, URI, vector, third-party dependency, or Codex code in this reproducer.

A slightly larger constant test also fails validation on a contract closure
symbol. Its deliberately false contract likewise hits a tool invariant rather
than reaching the intended assertion; that is not an expected-failure control.
The initial attempt omitted `-Z unstable-options`, which the sanity-check option
requires. Those three CLI errors were preserved separately and are excluded
from verification outcomes.

## Explanation of the argument-count warnings

The earlier vector artifact was inspected read-only with `goto-instrument`:

- `usize::saturating_add` and `saturating_sub` have generated signatures with
  **three parameters**: `self`, `rhs`, and `__write_set_to_check`.
- Calls from `__VERIFIER_kani_enter_contract_clause` and
  `__VERIFIER_kani_exit_contract_clause` still supply **two arguments**.
- CBMC explicitly reports that the missing argument is being replaced with a
  nondeterministic value. It is the extra instrumentation context, not evidence
  that an arithmetic operand or counter result was directly replaced.

This accounts for those warnings. The release source marks these internal
helpers with `__VERIFIER` names and explains their exemption from contract
side-effect instrumentation. Missed call rewriting at that internal/noninternal
boundary is a plausible implementation mechanism. The displayed signatures and
calls establish the arity mismatch; they do not independently establish every
cause within DFCC or prove that correcting those two calls fixes the system.

Additional validation of the vector's post-instrumentation GOTO binary exits 6
with a function-type inconsistency in an allocator helper. The minimal
constant reproducer shows that malformed type relationships are not dependent
on allocation. These are related symptoms in contract-instrumented models;
this investigation does not prove they share one repair.

## Default-mode controls and limits on the diagnosis

Without the additional validation option, the true constant contract reports
success and the false constant contract reports exactly one failed ensures
condition, both in about one second. Both emit the saturation-call warnings.
No false acceptance of the deliberately false contract was observed.

Thus the warning is **not sufficient by itself** to explain why the earlier
byte-vector contract used over 8 GiB, and it is not evidence that all default
contract results are false. The observed fact is a structural validation defect
and a separate measured scaling discrepancy. Treat contract-based project
results as blocked pending a validated repair; do not suppress model validation,
ignore arity warnings, add arbitrary dummy arguments, or assume unproved
contracts to advance the project.

The full preservation case's ordinary mode also timed out. A contract repair
would remove a tool blocker, not automatically prove that full property.

## Version and source checks

Installed versions remain Kani 0.68.0, CBMC 6.11.0 and verifier Rust
1.100.0-nightly (8925ea358, nightly-2026-08-21). The official Kani release source
was fetched at `0d2328a93f0e0ff66132d6bfa1a7d884877cf862`. Its toolchain pin
matches the installed verifier toolchain, and its contract macro `check.rs`
hash matches the installed source copy.

Official main was inspected at `744b3e84d6eb68fd5456826997568666791bd355`.
It still contains the saturation calls and pins CBMC 6.11.0 but uses
nightly-2026-10-23. Main was not built or tested; other changes could matter,
so its correctness cannot be inferred from this source inspection. No verified
upgrade or workaround was identified. The installed toolchain was left intact.

## Next action

Use the minimal validation failure as the primary maintainer report, with the
arity evidence and vector memory comparison as supporting observations. A repair
needs consistent post-contract function signatures, call sites and symbol-expression
types. Validate that repair on the constant positive/false controls and the vector
pair before returning to Codex proofs. Do not present an experimental IR edit or
unchecked replacement as a containment result.

A local report and source/log bundle are prepared; nothing was submitted
externally. Preserve the existing native matrix and ordinary component evidence
as separate results. Further unchecked-contract proof expansion remains paused.

Artifacts: `KANI_CONTRACT_INVESTIGATION.json`, the reproducer source in
`verification/diagnostics/minimal_constant_contract.rs`, raw files under
`.tools/kani-investigation`, and `kani-contract-validation-reproducer.tar.gz`.
