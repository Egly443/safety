//! Same diagnostic predicates as staged_policy.rs, without assert_eq formatting.
use crate::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{
    FileSystemAccessMode, FileSystemPath, FileSystemSandboxEntry,
    FileSystemSandboxKind, FileSystemSandboxPolicy, FileSystemSpecialPath,
};
use codex_utils_path_uri::PathUri;

#[kani::proof]
#[kani::unwind(16)]
fn parse_one_uri() {
    let path = PathUri::parse("file:///w").unwrap();
    assert!(path.encoded_path() == "/w");
}

fn merge_fixture(base_is_write: bool) -> (FileSystemSandboxPolicy, FileSystemSandboxPolicy) {
    let base = FileSystemSandboxPolicy::restricted(vec![FileSystemSandboxEntry::new(
        FileSystemPath::Special { value: FileSystemSpecialPath::Root },
        if base_is_write { FileSystemAccessMode::Write } else { FileSystemAccessMode::Read },
    )]);
    let additional = AdditionalPermissionProfile {
        network: None,
        file_system: Some(FileSystemPermissions {
            entries: vec![FileSystemSandboxEntry::new(
                FileSystemPath::Special { value: FileSystemSpecialPath::Root },
                FileSystemAccessMode::Write,
            )],
            glob_scan_max_depth: None,
        }),
    };
    let granted = effective_file_system_sandbox_policy(&base, Some(&additional));
    (base, granted)
}

#[kani::proof]
#[kani::unwind(16)]
fn merge_entries_stage() {
    // Exactly two cases: duplicate write entry, or distinct read/write entries.
    let base_is_write: bool = kani::any();
    let (base, granted) = merge_fixture(base_is_write);
    assert!(matches!(granted.kind, FileSystemSandboxKind::Restricted));
    assert!(base.entries.len() == 1);
    assert!(granted.entries.len() == if base_is_write { 1 } else { 2 });
    assert!(granted.entries[0] == base.entries[0]);
    assert!(granted.entries.last().unwrap().access == FileSystemAccessMode::Write);
    assert!(granted.glob_scan_max_depth == None);
}

#[kani::proof]
#[kani::unwind(16)]
fn merge_entries_must_fail() {
    let (_, granted) = merge_fixture(false);
    // Deliberately false: the real merge appends a distinct write entry.
    assert!(granted.entries.len() == 1);
}
