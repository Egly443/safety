#!/usr/bin/env python3
"""Matched, bounded verifier diagnostics. Never substitutes contracts in Codex."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
out = root / '.tools/kani-contract-diagnostics'
out.mkdir(exist_ok=True)
if any(out.iterdir()):
    sys.exit(f'Preserve {out} before rerunning')
tree = root / '.tools/kani-source'
lib = tree / 'codex-rs/sandboxing/src/lib.rs'
checker = [sys.executable, str(root / 'scripts/prepare-kani.py'), '--check']
subprocess.run(checker, check=True)
env = os.environ.copy()
env.update(CARGO_BUILD_JOBS='1', CARGO_PROFILE_DEV_DEBUG='0', CARGO_INCREMENTAL='0')
record = {'source_manifest': json.loads((root / 'evidence/kani-source-manifest.json').read_text()),
          'budget_seconds': 180, 'rss_gib': 8, 'unwind': 16, 'runs': []}

def save():
    (out / 'results.json').write_text(json.dumps(record, indent=2) + '\n')

def snapshot(ancestor, cpu_seen):
    procs = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            raw = path.read_text()
            end = raw.rfind(')')
            fields = raw[end + 2:].split()
            pid = int(path.parent.name)
            procs[pid] = {'pid': pid, 'ppid': int(fields[1]),
                          'name': raw[raw.find('(') + 1:end], 'state': fields[0],
                          'cpu_seconds': (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK'),
                          'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE'),
                          'start_ticks': fields[19]}
        except (OSError, ValueError, IndexError):
            continue
    selected = {ancestor}
    while True:
        extended = selected | {pid for pid, p in procs.items() if p['ppid'] in selected}
        if extended == selected:
            break
        selected = extended
    live = [p for pid, p in procs.items() if pid in selected]
    for p in live:
        cpu_seen[(p['pid'], p['start_ticks'])] = p['cpu_seconds']
    return live

def run_one(case, mode, source, manifest_name, control=False):
    directory = out / case / mode
    directory.mkdir(parents=True, exist_ok=True)
    label = 'control' if control else 'positive'
    harness = ('protected_removed_must_fail' if case == 'preservation' else 'probe_must_fail') if control else manifest_name
    full = case in ('preservation', 'uri_entries')
    if full:
        command = ['cargo', 'kani', '--manifest-path', str(tree / 'codex-rs/Cargo.toml'),
                   '--target-dir', str(root / '.tools/kani-target'), '-p', 'codex-sandboxing',
                   '--exact', '--harness', 'staged_diagnostic::' + harness, '-Z', 'function-contracts']
        cwd = tree / 'codex-rs'
    else:
        command = ['kani', str(source), '--exact', '--harness', harness, '-Z', 'function-contracts']
        cwd = directory
    guarded = [sys.executable, str(root / 'scripts/run-limited.py'), '--seconds', '180',
               '--rss-gib', '8', '--cwd', str(cwd), '--record', str(directory / f'{label}.resources.json'),
               '--log', str(directory / f'{label}.log'), '--', *command]
    print(f'Running {case} / {mode} / {label}', flush=True)
    start = time.monotonic()
    cpu_seen = {}
    child = subprocess.Popen(guarded, env=env)
    with (directory / f'{label}.samples.jsonl').open('w') as samples:
        while child.poll() is None:
            processes = snapshot(child.pid, cpu_seen)
            samples.write(json.dumps({'elapsed_seconds': time.monotonic() - start,
                'sampled_cpu_seconds': sum(cpu_seen.values()), 'processes': processes}) + '\n')
            samples.flush()
            time.sleep(1)
    code = child.wait()
    log = (directory / f'{label}.log').read_text()
    summary = re.search(r'\*\* (\d+) of (\d+) failed', log)
    failed = re.findall(r' - Status: FAILURE\n\s* - Description: "(.*?)"\n\s* - Location:', log)
    expected = 'assertion failed: !observed.protected_retained' if case == 'preservation' else 'assertion failed: !probe()'
    outcome = 'inconclusive'
    if code == 0 and summary and int(summary[1]) == 0 and int(summary[2]) > 0 and '1 total.' in log:
        outcome = 'unexpected_success' if control else 'passed'
    elif control and code == 1 and summary and int(summary[1]) == 1 and failed == [expected]:
        outcome = 'expected_failure'
    elif code not in (0, 124):
        outcome = 'unexpected_failure'
    result = {'case': case, 'mode': mode, 'label': label, 'outcome': outcome,
              'runner_exit_code': code, 'command': command,
              'snapshot_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'resources': json.loads((directory / f'{label}.resources.json').read_text()),
              'sampled_cpu_seconds': sum(cpu_seen.values()),
              'checks_failed': int(summary[1]) if summary else None,
              'checks_total': int(summary[2]) if summary else None,
              'failed_descriptions': failed,
              'log_sha256': hashlib.sha256(log.encode()).hexdigest(),
              'checking_harness_logged': bool(re.search(r'^Checking harness', log, re.M)),
              'solver_logged': bool(re.search(r'^Solving with', log, re.M)),
              'directory': str(directory)}
    record['runs'].append(result)
    save()
    return outcome

cases = [
    ('preservation', root / 'verification/kani/protected_entry_preservation.rs', 'fixed_preservation_contract', 'check_preservation_contract'),
    ('bytes', root / 'verification/diagnostics/vector_case.rs', 'probe', 'check_probe'),
    ('small_entries', root / 'verification/diagnostics/small_entry_case.rs', 'probe', 'check_probe'),
    ('uri_entries', root / 'verification/diagnostics/uri_entry_collections.rs', 'probe', 'check_probe'),
]
save()
for case, original, function, manifest_name in cases:
    original_text = original.read_text()
    successful_modes = []
    for mode in ('ordinary', 'contract'):
        directory = out / case / mode
        directory.mkdir(parents=True, exist_ok=True)
        text = original_text
        if mode == 'ordinary':
            attr = '#[cfg_attr(kani, kani::ensures(|result: &bool| *result))]' if case == 'preservation' else '#[cfg_attr(kani, kani::ensures(|r: &bool| *r))]'
            for before, after in [(attr, ''),
                (f'#[kani::proof_for_contract({function})]', '#[kani::proof]'),
                (f'let _ = {function}();', f'assert!({function}());')]:
                assert text.count(before) == 1, before
                text = text.replace(before, after)
        source = directory / 'fixture.rs'
        source.write_text(text)
        (directory / 'mode.diff').write_text(''.join(difflib.unified_diff(
            original_text.splitlines(True), text.splitlines(True), fromfile=str(original), tofile=str(source))))
        before_lib = lib.read_bytes()
        full = case in ('preservation', 'uri_entries')
        try:
            if full:
                hook = '\n#[cfg(kani)]\n#[path = ' + json.dumps(str(source)) + ']\nmod staged_diagnostic;\n'
                lib.write_bytes(before_lib + hook.encode())
                (directory / 'worktree.diff').write_bytes(subprocess.check_output(['git', '-C', str(tree), 'diff', '--binary']))
            outcome = run_one(case, mode, source, manifest_name)
            successful_modes.append(outcome == 'passed')
            if outcome == 'passed':
                control = run_one(case, mode, source, manifest_name, control=True)
                successful_modes[-1] = control == 'expected_failure'
            else:
                record['runs'].append({'case': case, 'mode': mode, 'label': 'control',
                                       'outcome': 'skipped_positive_incomplete'})
                save()
        finally:
            if full:
                lib.write_bytes(before_lib)
                subprocess.run(checker, check=True)
    if case in ('bytes', 'small_entries') and not all(successful_modes):
        record['stop_reason'] = f'Stop type growth: {case} did not complete with its controls'
        save()
        break
subprocess.run(checker, check=True)
record['completed'] = True
save()
if any(r['outcome'] not in ('passed', 'expected_failure') for r in record['runs']):
    sys.exit(2)
