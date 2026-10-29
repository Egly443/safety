//! Actual-code feasibility check, not yet a symbolic bounded proof.
use crate::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{
    FileSystemAccessMode, FileSystemPath, FileSystemSandboxEntry,
    FileSystemSandboxPolicy, FileSystemSandboxPolicyContext,
};
use codex_utils_path_uri::PathUri;

fn entry(uri: &str, access: FileSystemAccessMode) -> FileSystemSandboxEntry {
    FileSystemSandboxEntry::new(
        FileSystemPath::Path { path: PathUri::parse(uri).unwrap() }, access,
    )
}

#[kani::proof]
#[kani::unwind(64)]
fn actual_policy_smoke() {
    let workspace = PathUri::parse("file:///workspace").unwrap();
    let protected = PathUri::parse("file:///workspace/protected/file").unwrap();
    let ordinary = PathUri::parse("file:///workspace/ordinary").unwrap();
    let roots = [workspace.clone()];
    let context = FileSystemSandboxPolicyContext {
        cwd: &workspace, workspace_roots: &roots,
        user_home_dir: None, temporary_directories: None,
    };
    let base = FileSystemSandboxPolicy::restricted(vec![
        entry("file:///", FileSystemAccessMode::Read),
        entry("file:///workspace/protected", FileSystemAccessMode::Read),
    ]);
    let additional = AdditionalPermissionProfile {
        network: None,
        file_system: Some(FileSystemPermissions {
            entries: vec![entry("file:///workspace", FileSystemAccessMode::Write)],
            glob_scan_max_depth: None,
        }),
    };
    assert!(!base.can_write_path(&ordinary, &context));
    let granted = effective_file_system_sandbox_policy(&base, Some(&additional));
    assert!(!granted.can_write_path(&protected, &context));
    assert!(granted.can_write_path(&ordinary, &context));
}
