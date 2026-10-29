//! The selected fixed structural case. No resolver or containment claim.
#[cfg(kani)]
use crate::policy_transforms::effective_file_system_sandbox_policy;
#[cfg(not(kani))]
use codex_sandboxing::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{FileSystemAccessMode as Mode, FileSystemPath,
    FileSystemSandboxEntry, FileSystemSandboxKind, FileSystemSandboxPolicy};
use codex_utils_path_uri::PathUri;

struct Observation {
    root_retained: bool,
    protected_retained: bool,
    original_prefix_retained: bool,
    workspace_grants: usize,
    entry_count: usize,
    restricted: bool,
    depth_unchanged: bool,
}

fn entry(uri: &str, access: Mode) -> FileSystemSandboxEntry {
    FileSystemSandboxEntry::new(
        FileSystemPath::Path { path: PathUri::parse(uri).unwrap() }, access,
    )
}

fn observe() -> Observation {
    let base = FileSystemSandboxPolicy::restricted(vec![
        entry("file:///", Mode::Read),
        entry("file:///w/p", Mode::Read),
    ]);
    let additional = AdditionalPermissionProfile {
        network: None,
        file_system: Some(FileSystemPermissions {
            entries: vec![entry("file:///w", Mode::Write)],
            glob_scan_max_depth: None,
        }),
    };
    let result = effective_file_system_sandbox_policy(&base, Some(&additional));
    let grant = &additional.file_system.as_ref().unwrap().entries[0];
    Observation {
        root_retained: result.entries.contains(&base.entries[0]),
        protected_retained: result.entries.contains(&base.entries[1]),
        original_prefix_retained: result.entries.starts_with(&base.entries),
        workspace_grants: result.entries.iter().filter(|e| *e == grant).count(),
        entry_count: result.entries.len(),
        restricted: matches!(result.kind, FileSystemSandboxKind::Restricted),
        depth_unchanged: result.glob_scan_max_depth == base.glob_scan_max_depth,
    }
}

impl Observation {
    fn preserves(&self) -> bool {
        self.root_retained && self.protected_retained && self.original_prefix_retained
            && self.workspace_grants == 1 && self.entry_count == 3
            && self.restricted && self.depth_unchanged
    }
}

// The contract is checked on this concrete no-argument fixture. It is not a
// contract for arbitrary policies and must not be substituted into production.
#[cfg_attr(kani, kani::ensures(|result: &bool| *result))]
fn fixed_preservation_contract() -> bool {
    observe().preserves()
}

#[cfg(kani)]
#[kani::proof_for_contract(fixed_preservation_contract)]
#[kani::unwind(16)]
fn check_preservation_contract() {
    let _ = fixed_preservation_contract();
}

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(16)]
fn protected_removed_must_fail() {
    let observed = observe();
    assert!(!observed.protected_retained);
}

#[cfg(not(kani))]
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let control = args == ["--claim-protected-removed"];
    assert!(args.is_empty() || control, "unknown arguments");
    let observed = observe();
    let actual_claim = if control { !observed.protected_retained } else { fixed_preservation_contract() };
    println!("{}", serde_json::json!({
        "case": "protected_entry_preservation_v1",
        "claim": if control { "protected_entry_removed" } else { "entries_preserved" },
        "claim_holds": actual_claim,
        "root_retained": observed.root_retained,
        "protected_retained": observed.protected_retained,
        "original_prefix_retained": observed.original_prefix_retained,
        "workspace_grants": observed.workspace_grants,
        "entry_count": observed.entry_count,
        "restricted": observed.restricted,
        "depth_unchanged": observed.depth_unchanged,
    }));
    if !actual_claim { std::process::exit(1); }
}
