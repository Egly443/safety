//! Small control on the actual public transformation, not containment.
use crate::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::permissions::{FileSystemSandboxKind, FileSystemSandboxPolicy};

fn fixture() -> FileSystemSandboxPolicy {
    let choice: u8 = kani::any();
    FileSystemSandboxPolicy {
        kind: match choice % 3 {
            0 => FileSystemSandboxKind::Restricted,
            1 => FileSystemSandboxKind::Unrestricted,
            _ => FileSystemSandboxKind::ExternalSandbox,
        },
        entries: Vec::new(),
        glob_scan_max_depth: Some(2),
    }
}

#[kani::proof]
#[kani::unwind(16)]
fn no_grant_identity_stage() {
    let base = fixture();
    let granted = effective_file_system_sandbox_policy(&base, None);
    assert!(granted.kind == base.kind);
    assert!(granted.entries.is_empty());
    assert!(granted.glob_scan_max_depth == Some(2));
}

#[kani::proof]
#[kani::unwind(16)]
fn no_grant_must_fail() {
    let base = fixture();
    let granted = effective_file_system_sandbox_policy(&base, None);
    // Deliberately false for every input: a clone preserves the depth.
    assert!(granted.glob_scan_max_depth != Some(2));
}
