//! Actual operations only; no stubs or replacement path/policy semantics.
use crate::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{FileSystemAccessMode as Mode, FileSystemPath,
    FileSystemSandboxEntry, FileSystemSandboxPolicy, FileSystemSandboxPolicyContext,
    FileSystemSpecialPath};
use codex_utils_path_uri::PathUri;

fn root(write: bool) -> FileSystemSandboxEntry {
    FileSystemSandboxEntry::new(
        FileSystemPath::Special { value: FileSystemSpecialPath::Root },
        if write { Mode::Write } else { Mode::Read },
    )
}

#[kani::proof]
#[kani::unwind(16)]
fn special_entry_equality() {
    let a: bool = kani::any();
    let b: bool = kani::any();
    assert!((root(a) == root(b)) == (a == b));
}

#[kani::proof]
#[kani::unwind(16)]
fn special_entry_equality_must_fail() {
    assert!(root(false) == root(true));
}

#[kani::proof]
#[kani::unwind(16)]
fn special_entry_clone() {
    let write: bool = kani::any();
    let original = root(write);
    let cloned = original.clone();
    assert!(cloned.access.can_write() == write);
    assert!(matches!(cloned.path, FileSystemPath::Special { value: FileSystemSpecialPath::Root }));
    assert!(cloned.missing_path_behavior.is_none());
}

#[kani::proof]
#[kani::unwind(16)]
fn special_entry_clone_must_fail() {
    let cloned = root(true).clone();
    assert!(!cloned.access.can_write());
}

#[kani::proof]
#[kani::unwind(16)]
fn uri_clone() {
    let original = PathUri::parse("file:///w").unwrap();
    let cloned = original.clone();
    assert!(original.encoded_path() == "/w");
    assert!(cloned.encoded_path() == "/w");
}

#[kani::proof]
#[kani::unwind(16)]
fn uri_clone_must_fail() {
    let cloned = PathUri::parse("file:///w").unwrap().clone();
    assert!(cloned.encoded_path() != "/w");
}

#[kani::proof]
#[kani::unwind(16)]
fn uri_equality() {
    let original = PathUri::parse("file:///w").unwrap();
    let cloned = original.clone();
    assert!(original == cloned);
}

#[kani::proof]
#[kani::unwind(16)]
fn uri_equality_must_fail() {
    let original = PathUri::parse("file:///w").unwrap();
    let cloned = original.clone();
    assert!(original != cloned);
}

fn nonempty_merge(write: bool) -> FileSystemSandboxPolicy {
    let base = FileSystemSandboxPolicy::restricted(vec![root(write)]);
    let additional = AdditionalPermissionProfile {
        network: None,
        file_system: Some(FileSystemPermissions {
            entries: vec![root(true)], glob_scan_max_depth: None,
        }),
    };
    effective_file_system_sandbox_policy(&base, Some(&additional))
}

#[kani::proof]
#[kani::unwind(16)]
fn nonempty_merge_fields() {
    let write: bool = kani::any();
    let result = nonempty_merge(write);
    assert!(result.entries.len() == if write { 1 } else { 2 });
    assert!(result.entries[0].access.can_write() == write);
    assert!(result.entries.last().unwrap().access.can_write());
    assert!(matches!(result.entries[0].path, FileSystemPath::Special { value: FileSystemSpecialPath::Root }));
    assert!(matches!(result.entries.last().unwrap().path, FileSystemPath::Special { value: FileSystemSpecialPath::Root }));
}

#[kani::proof]
#[kani::unwind(16)]
fn nonempty_merge_fields_must_fail() {
    let result = nonempty_merge(false);
    assert!(result.entries.len() == 1);
}

fn resolver_fixture() -> (bool, bool) {
    let workspace = PathUri::parse("file:///w").unwrap();
    let protected = PathUri::parse("file:///w/p").unwrap();
    let roots = [workspace.clone()];
    let context = FileSystemSandboxPolicyContext {
        cwd: &workspace, workspace_roots: &roots,
        user_home_dir: None, temporary_directories: None,
    };
    // Direct fixed policy, without the merge. Root-read entry omitted intentionally.
    let policy = FileSystemSandboxPolicy::restricted(vec![
        FileSystemSandboxEntry::new(FileSystemPath::Path { path: protected.clone() }, Mode::Read),
        FileSystemSandboxEntry::new(FileSystemPath::Path { path: workspace.clone() }, Mode::Write),
    ]);
    (policy.can_write_path(&protected, &context), policy.can_write_path(&workspace, &context))
}

#[kani::proof]
#[kani::unwind(16)]
fn fixed_resolver() {
    let (protected, workspace) = resolver_fixture();
    assert!(!protected);
    assert!(workspace);
}

#[kani::proof]
#[kani::unwind(16)]
fn fixed_resolver_must_fail() {
    let (protected, _) = resolver_fixture();
    assert!(protected);
}

#[kani::proof]
#[kani::unwind(16)]
fn entry_vector_clone() {
    let write: bool = kani::any();
    let original = vec![root(write)];
    let cloned = original.clone();
    assert!(cloned.len() == 1);
    assert!(cloned[0].access.can_write() == write);
    assert!(matches!(cloned[0].path, FileSystemPath::Special { value: FileSystemSpecialPath::Root }));
}

#[kani::proof]
#[kani::unwind(16)]
fn entry_vector_clone_must_fail() {
    let cloned = vec![root(true)].clone();
    assert!(cloned.is_empty());
}

#[kani::proof]
#[kani::unwind(16)]
fn entry_vector_contains() {
    let a: bool = kani::any();
    let b: bool = kani::any();
    let entries = vec![root(a)];
    assert!(entries.contains(&root(b)) == (a == b));
}

#[kani::proof]
#[kani::unwind(16)]
fn entry_vector_contains_must_fail() {
    let entries = vec![root(false)];
    assert!(entries.contains(&root(true)));
}

#[kani::proof]
#[kani::unwind(16)]
fn duplicate_merge_only() {
    let result = nonempty_merge(true);
    assert!(result.entries.len() == 1);
    assert!(result.entries[0].access.can_write());
}

#[kani::proof]
#[kani::unwind(16)]
fn duplicate_merge_only_must_fail() {
    let result = nonempty_merge(true);
    assert!(result.entries.len() != 1);
}
