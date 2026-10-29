//! Tool diagnostic only. These records are not a replacement Codex model.
#[derive(Clone, PartialEq, Eq)]
enum Access { Read, Write }
#[derive(Clone, PartialEq, Eq)]
enum Path { Root, Protected, Workspace }
#[derive(Clone, PartialEq, Eq)]
struct Entry { path: Path, access: Access }

#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]
fn probe() -> bool {
    let base = vec![Entry { path: Path::Root, access: Access::Read },
                    Entry { path: Path::Protected, access: Access::Read }];
    let grant = Entry { path: Path::Workspace, access: Access::Write };
    let mut result = base.clone();
    if !result.contains(&grant) { result.push(grant.clone()); }
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
