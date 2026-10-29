//! Grant insertion only: no existing entries, URI parsing, or path resolution.
use crate::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{
    FileSystemAccessMode, FileSystemPath, FileSystemSandboxEntry,
    FileSystemSandboxKind, FileSystemSandboxPolicy, FileSystemSpecialPath,
};

fn insert(write: bool) -> FileSystemSandboxPolicy {
    let base = FileSystemSandboxPolicy::restricted(Vec::new());
    let additional = AdditionalPermissionProfile {
        network: None,
        file_system: Some(FileSystemPermissions {
            entries: vec![FileSystemSandboxEntry::new(
                FileSystemPath::Special { value: FileSystemSpecialPath::Root },
                if write { FileSystemAccessMode::Write } else { FileSystemAccessMode::Read },
            )],
            glob_scan_max_depth: None,
        }),
    };
    effective_file_system_sandbox_policy(&base, Some(&additional))
}

#[kani::proof]
#[kani::unwind(16)]
fn empty_base_grant_stage() {
    let write: bool = kani::any();
    let granted = insert(write);
    assert!(matches!(granted.kind, FileSystemSandboxKind::Restricted));
    assert!(granted.entries.len() == 1);
    assert!(matches!(granted.entries[0].path,
        FileSystemPath::Special { value: FileSystemSpecialPath::Root }));
    assert!(granted.entries[0].access.can_write() == write);
    assert!(granted.entries[0].access.can_read());
    assert!(granted.glob_scan_max_depth.is_none());
}

#[kani::proof]
#[kani::unwind(16)]
fn empty_base_grant_must_fail() {
    let granted = insert(true);
    // Deliberately false: the real transformation inserts the entry.
    assert!(granted.entries.is_empty());
}
