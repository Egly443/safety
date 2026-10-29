//! Exhaustive only over the finite domain declared here, not a universal proof.
use codex_sandboxing::policy_transforms::effective_file_system_sandbox_policy;
use codex_protocol::models::{AdditionalPermissionProfile, FileSystemPermissions};
use codex_protocol::permissions::{FileSystemAccessMode as Mode, FileSystemPath,
    FileSystemSandboxEntry, FileSystemSandboxPolicy, FileSystemSandboxPolicyContext};
use codex_utils_path_uri::PathUri;
use serde_json::{json, Value};

fn path(native: &str) -> PathUri {
    PathUri::parse(&format!("file://{native}")).expect("valid fixture URI")
}
fn entry(native: &str, access: Mode) -> FileSystemSandboxEntry {
    FileSystemSandboxEntry::new(FileSystemPath::Path { path: path(native) }, access)
}

fn main() {
    // Columns: workspace, ordinary root/file, protected root/file/deep/file-child,
    // similar-name sibling root/file, outside root, similar-name workspace sibling.
    let denied = [false; 11];
    let workspace = [true,true,true,false,false,false,false,true,true,false,false];
    let protected = [false,false,false,true,true,true,true,false,false,false,false];
    let both = [true,true,true,true,true,true,true,true,true,false,false];
    let descendant = [true,true,true,false,true,false,true,true,true,false,false];
    let scenarios = [
        ("none", denied, 2), ("empty", denied, 2),
        ("workspace", workspace, 3), ("duplicate_workspace", workspace, 3),
        ("reapply_workspace", workspace, 3), ("protected_only", protected, 3),
        ("workspace_then_protected", both, 4), ("protected_then_workspace", both, 4),
        ("workspace_then_descendant", descendant, 4),
        ("descendant_then_workspace", descendant, 4),
    ];
    let mut observations: Vec<Value> = Vec::new();
    let mut structure: Vec<Value> = Vec::new();
    let mut fixtures = 0;
    for w in ["/w", "/work", "/a/w"] {
        for p_name in ["p", "protected", "keep"] {
            for ordinary in ["q", "free"] {
                for reverse_base in [false, true] {
                    fixtures += 1;
                    let p = format!("{w}/{p_name}");
                    let protected_file = format!("{p}/f");
                    let w_uri = path(w);
                    let roots = [w_uri.clone()];
                    let context = FileSystemSandboxPolicyContext {
                        cwd: &w_uri, workspace_roots: &roots,
                        user_home_dir: None, temporary_directories: None,
                    };
                    let mut entries = vec![entry("/", Mode::Read), entry(&p, Mode::Read)];
                    if reverse_base { entries.reverse(); }
                    let base = FileSystemSandboxPolicy::restricted(entries);
                    let queries = [
                        ("workspace", w.to_string()),
                        ("ordinary_root", format!("{w}/{ordinary}")),
                        ("ordinary_file", format!("{w}/{ordinary}/f")),
                        ("protected_root", p.clone()),
                        ("protected_file", protected_file.clone()),
                        ("protected_deep", format!("{p}/d/f")),
                        ("protected_file_child", format!("{p}/f/z")),
                        ("similar_protected_root", format!("{p}2")),
                        ("similar_protected_file", format!("{p}2/f")),
                        ("outside", "/outside/f".to_string()),
                        ("similar_workspace", format!("{w}2/f")),
                    ];
                    for (scenario, expected, count) in scenarios {
                        let targets: Vec<&str> = match scenario {
                            "none" | "empty" => vec![],
                            "workspace" | "reapply_workspace" => vec![w],
                            "duplicate_workspace" => vec![w, w],
                            "protected_only" => vec![&p],
                            "workspace_then_protected" => vec![w, &p],
                            "protected_then_workspace" => vec![&p, w],
                            "workspace_then_descendant" => vec![w, &protected_file],
                            "descendant_then_workspace" => vec![&protected_file, w],
                            _ => unreachable!(),
                        };
                        let additional = AdditionalPermissionProfile {
                            network: None,
                            file_system: Some(FileSystemPermissions {
                                entries: targets.iter().map(|t| entry(t, Mode::Write)).collect(),
                                glob_scan_max_depth: None,
                            }),
                        };
                        let grant = if scenario == "none" { None } else { Some(&additional) };
                        let original = base.clone();
                        let mut granted = effective_file_system_sandbox_policy(&base, grant);
                        if scenario == "reapply_workspace" {
                            granted = effective_file_system_sandbox_policy(&granted, grant);
                        }
                        let checks = [
                            ("base_unchanged", base == original),
                            ("entry_count", granted.entries.len() == count),
                            ("base_entries_retained", base.entries.iter().all(|e| granted.entries.contains(e))),
                            ("policy_kind", granted.kind == base.kind),
                            ("glob_depth", granted.glob_scan_max_depth == base.glob_scan_max_depth),
                        ];
                        for (check, passed) in checks {
                            structure.push(json!({"fixture":fixtures,"scenario":scenario,
                                "check":check,"passed":passed}));
                        }
                        for (index, (category, query)) in queries.iter().enumerate() {
                            let actual = granted.can_write_path(&path(query), &context);
                            observations.push(json!({"fixture":fixtures,"workspace":w,
                                "protected":p,"ordinary":ordinary,"reverse_base":reverse_base,
                                "scenario":scenario,"category":category,"query":query,
                                "expected":expected[index],"actual":actual,
                                "passed":actual == expected[index]}));
                        }
                    }
                }
            }
        }
    }
    let failures = observations.iter().chain(structure.iter())
        .filter(|v| v["passed"] == false).count();
    println!("{}", json!({"domain_version":1,"fixtures":fixtures,
        "scenarios_per_fixture":scenarios.len(),"queries_per_scenario":11,
        "observations":observations,"structural_checks":structure,"failures":failures}));
    if failures != 0 { std::process::exit(1); }
}
