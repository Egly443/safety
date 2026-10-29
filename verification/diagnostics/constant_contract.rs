//! Tool reduction: a contract with no heap, loops, or Codex dependencies.
#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]
fn constant() -> bool { true }

#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]
fn false_constant() -> bool { false }

#[cfg(kani)]
#[kani::proof_for_contract(constant)]
#[kani::unwind(16)]
fn positive_contract() { let _ = constant(); }

#[cfg(kani)]
#[kani::proof_for_contract(false_constant)]
#[kani::unwind(16)]
fn false_contract_control() { let _ = false_constant(); }

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(16)]
fn ordinary_positive() { assert!(constant()); }
