#[kani::ensures(|r: &bool| *r)]
fn constant() -> bool { true }

#[kani::proof_for_contract(constant)]
fn check_constant() { let _ = constant(); }
