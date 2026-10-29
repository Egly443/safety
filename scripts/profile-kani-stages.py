#!/usr/bin/env python3
"""Bounded diagnostic runs; preserve the original harness and worktree hook."""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import argparse

parser = argparse.ArgumentParser()
variant = parser.add_mutually_exclusive_group()
variant.add_argument('--plain', action='store_true', help='Use equivalent predicates without assert_eq formatting')
variant.add_argument('--identity', action='store_true', help='Check the no-grant control across all policy kinds')
variant.add_argument('--grant', action='store_true', help='Check insertion into an empty base policy')
variant.add_argument('--components', action='store_true', help='Run the next equality, clone, merge and resolver gates')
variant.add_argument('--vectors', action='store_true', help='Isolate vector cloning and contains after the merge timeout')
variant.add_argument('--duplicate-merge', action='store_true', help='Check only the concrete nonempty duplicate-grant case')
variant.add_argument('--preservation', action='store_true', help='Check the selected protected-entry preservation contract')
parser.add_argument('--output-dir', type=Path, help='Fresh result directory beneath .tools for a repeat run')
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
tree = root / '.tools/kani-source'
lib = tree / 'codex-rs/sandboxing/src/lib.rs'
out = root / ('.tools/kani-stages-plain' if args.plain else '.tools/kani-stages')
if args.identity:
    out = root / '.tools/kani-stages-identity'
if args.grant:
    out = root / '.tools/kani-stages-grant'
if args.components:
    out = root / '.tools/kani-components'
if args.vectors:
    out = root / '.tools/kani-vectors'
if args.duplicate_merge:
    out = root / '.tools/kani-duplicate-merge'
if args.preservation:
    out = root / '.tools/kani-protected-preservation'
if args.output_dir:
    out = (root / args.output_dir).resolve()
    tools_root = (root / '.tools').resolve()
    if out == tools_root or not out.is_relative_to(tools_root):
        parser.error('--output-dir must be a fresh subdirectory beneath .tools')
out.mkdir(exist_ok=True)
if any(out.iterdir()):
    sys.exit(f'Preserve previous {out} results before rerunning')
subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'], check=True)
before = lib.read_bytes()
harness = root / 'verification/kani/staged_policy.rs'
if args.plain:
    harness = root / 'verification/kani/staged_policy_plain.rs'
if args.identity:
    harness = root / 'verification/kani/policy_identity.rs'
if args.grant:
    harness = root / 'verification/kani/single_grant.rs'
if args.components or args.vectors or args.duplicate_merge:
    harness = root / 'verification/kani/policy_components.rs'
if args.preservation:
    harness = root / 'verification/kani/protected_entry_preservation.rs'
hook = '\n#[cfg(kani)]\n#[path = ' + json.dumps(str(harness)) + ']\nmod staged_policy_verification;\n'
env = os.environ.copy()
env.update(CARGO_BUILD_JOBS='1', CARGO_PROFILE_DEV_DEBUG='0', CARGO_INCREMENTAL='0')
results = {
    'harness_sha256': hashlib.sha256(harness.read_bytes()).hexdigest(),
    'production_source_manifest': json.loads((root / 'evidence/kani-source-manifest.json').read_text()),
    'runs': [],
}
(out / 'harness.rs').write_bytes(harness.read_bytes())
(out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
try:
    lib.write_bytes(before + hook.encode())
    (out / 'worktree.diff').write_bytes(subprocess.check_output(['git', '-C', str(tree), 'diff', '--binary']))
    names = ('no_grant_identity_stage', 'no_grant_must_fail') if args.identity else ('merge_entries_stage', 'merge_entries_must_fail', 'parse_one_uri')
    if args.grant:
        names = ('empty_base_grant_stage', 'empty_base_grant_must_fail')
    if args.components:
        names = [name + suffix for name in ('special_entry_equality', 'special_entry_clone',
                 'uri_clone', 'uri_equality', 'nonempty_merge_fields', 'fixed_resolver')
                 for suffix in ('', '_must_fail')]
    if args.vectors:
        names = [name + suffix for name in ('entry_vector_clone', 'entry_vector_contains')
                 for suffix in ('', '_must_fail')]
    if args.duplicate_merge:
        names = ('duplicate_merge_only', 'duplicate_merge_only_must_fail')
    if args.preservation:
        names = ('check_preservation_contract', 'protected_removed_must_fail')
    for name in names:
        if (args.components or args.vectors or args.duplicate_merge or args.preservation) and name.endswith('_must_fail') and results['runs'][-1]['outcome'] != 'passed':
            results['runs'].append({'harness': name, 'outcome': 'skipped_positive_incomplete',
                                    'runner_exit_code': None, 'command': None})
            (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
            continue
        command = [sys.executable, str(root / 'scripts/run-limited.py'),
                   '--seconds', '180', '--rss-gib', '8', '--cwd', str(tree / 'codex-rs'),
                   '--record', str(out / f'{name}.resources.json'),
                   '--log', str(out / f'{name}.log'), '--',
                   'cargo', 'kani', '--manifest-path', str(tree / 'codex-rs/Cargo.toml'),
                   '--target-dir', str(root / '.tools/kani-target'),
                   '-p', 'codex-sandboxing', '--exact', '--harness', 'staged_policy_verification::' + name]
        if args.preservation:
            command += ['-Z', 'function-contracts']
        print('Running', name, flush=True)
        run = subprocess.run(command, env=env)
        log = (out / f'{name}.log').read_text()
        summary = re.search(r'\*\* (\d+) of (\d+) failed', log)
        expected = {
            'no_grant_must_fail': 'assertion failed: granted.glob_scan_max_depth != Some(2)',
            'empty_base_grant_must_fail': 'assertion failed: granted.entries.is_empty()',
            'merge_entries_must_fail': 'assertion failed: granted.entries.len() == 1',
            'special_entry_equality_must_fail': 'assertion failed: root(false) == root(true)',
            'special_entry_clone_must_fail': 'assertion failed: !cloned.access.can_write()',
            'uri_clone_must_fail': 'assertion failed: cloned.encoded_path() != "/w"',
            'uri_equality_must_fail': 'assertion failed: original != cloned',
            'nonempty_merge_fields_must_fail': 'assertion failed: result.entries.len() == 1',
            'fixed_resolver_must_fail': 'assertion failed: protected',
            'entry_vector_clone_must_fail': 'assertion failed: cloned.is_empty()',
            'entry_vector_contains_must_fail': 'assertion failed: entries.contains(&root(true))',
            'duplicate_merge_only_must_fail': 'assertion failed: result.entries.len() != 1',
            'protected_removed_must_fail': 'assertion failed: !observed.protected_retained',
        }.get(name)
        outcome = 'inconclusive'
        if run.returncode == 0 and summary and int(summary[1]) == 0 and int(summary[2]) > 0 and '1 total.' in log:
            outcome = 'unexpected_success' if name.endswith('_must_fail') else 'passed'
        elif (run.returncode == 1 and summary and int(summary[1]) == 1
              and expected and f'Failed Checks: {expected}' in log):
            outcome = 'expected_failure'
        elif run.returncode not in (0, 124):
            outcome = 'unexpected_failure'
        results['runs'].append({'harness': name, 'runner_exit_code': run.returncode,
                                'outcome': outcome, 'command': command,
                                'checks_failed': int(summary[1]) if summary else None,
                                'checks_total': int(summary[2]) if summary else None,
                                'log_sha256': hashlib.sha256(log.encode()).hexdigest()})
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
finally:
    lib.write_bytes(before)
    subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'], check=True)
if any(run['outcome'] not in ('passed', 'expected_failure') for run in results['runs']):
    sys.exit(2)
