//! Diagnostic of collections holding actual Codex entries. This does not call
//! the production policy transformation and is not used as its specification.
use codex_protocol::permissions::{FileSystemAccessMode as Mode, FileSystemPath,
    FileSystemSandboxEntry};
use codex_utils_path_uri::PathUri;

fn entry(uri: &str, access: Mode) -> FileSystemSandboxEntry {
    FileSystemSandboxEntry::new(
        FileSystemPath::Path { path: PathUri::parse(uri).unwrap() }, access,
    )
}

#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]
fn probe() -> bool {
    let base = vec![entry("file:///", Mode::Read), entry("file:///w/p", Mode::Read)];
    let grant = entry("file:///w", Mode::Write);
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
