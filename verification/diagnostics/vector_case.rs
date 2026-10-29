//! Tool diagnostic only. No Codex policy semantics are represented.
#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]
fn probe() -> bool {
    let base = vec![1u8, 2];
    let grant = 3u8;
    let mut result = base.clone();
    if !result.contains(&grant) { result.push(grant); }
    result.len() == 3 && result.starts_with(&base)
        && result.iter().filter(|entry| **entry == grant).count() == 1
}

#[cfg(kani)]
#[kani::proof_for_contract(probe)]
#[kani::unwind(16)]
fn check_probe() { let _ = probe(); }

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(16)]
fn probe_must_fail() { assert!(!probe()); }

#[cfg(not(kani))]
fn main() { assert!(probe()); }
