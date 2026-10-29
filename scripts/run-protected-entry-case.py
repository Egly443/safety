#!/usr/bin/env python3
"""Run the selected fixture and false-removal control against actual Codex."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
tree = root / '.tools/kani-source'
source = root / 'verification/kani/protected_entry_preservation.rs'
out = root / '.tools/native-protected-preservation'
out.mkdir(exist_ok=True)
if any(out.iterdir()):
    sys.exit(f'Preserve {out} before rerunning')
subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'], check=True)
example = tree / 'codex-rs/sandboxing/examples/protected_entry_preservation.rs'
if example.exists():
    sys.exit(f'Refusing to overwrite {example}')
target = root / '.tools/native-policy-target'
env = os.environ.copy()
env.update(CARGO_BUILD_JOBS='2', CARGO_PROFILE_DEV_DEBUG='0', CARGO_INCREMENTAL='0')
meta = {'fixture_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_manifest': json.loads((root / 'evidence/kani-source-manifest.json').read_text()),
        'runs': []}
(out / 'fixture.rs').write_bytes(source.read_bytes())
exit_code = 2
try:
    example.parent.mkdir(exist_ok=True)
    example.write_bytes(source.read_bytes())
    build = ['cargo', '+1.99.1', 'build', '--locked', '--manifest-path',
             str(tree / 'codex-rs/Cargo.toml'), '--target-dir', str(target),
             '-p', 'codex-sandboxing', '--example', 'protected_entry_preservation']
    meta['build_command'] = build
    meta['build_exit_code'] = subprocess.run([
        sys.executable, str(root / 'scripts/run-limited.py'), '--seconds', '180',
        '--rss-gib', '8', '--cwd', str(tree / 'codex-rs'),
        '--record', str(out / 'build-resources.json'), '--log', str(out / 'build.log'),
        '--', *build], env=env).returncode
    if meta['build_exit_code'] == 0:
        binary = target / 'debug/examples/protected_entry_preservation'
        meta['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        for name, args, expected_exit in [('positive', [], 0),
            ('false_removal_control', ['--claim-protected-removed'], 1)]:
            command = [str(binary), *args]
            run = subprocess.run(command, capture_output=True, text=True, timeout=30)
            (out / f'{name}.stdout.json').write_text(run.stdout)
            (out / f'{name}.stderr.log').write_text(run.stderr)
            result = json.loads(run.stdout)
            assert run.returncode == expected_exit, (run.returncode, run.stderr)
            assert result['case'] == 'protected_entry_preservation_v1'
            assert result['claim_holds'] == (expected_exit == 0)
            assert result['entry_count'] == 3 and result['workspace_grants'] == 1
            for field in ('root_retained', 'protected_retained', 'original_prefix_retained',
                          'restricted', 'depth_unchanged'):
                assert result[field] is True, (field, result)
            assert result['claim'] == ('entries_preserved' if expected_exit == 0 else 'protected_entry_removed')
            meta['runs'].append({'name': name, 'command': command,
                'exit_code': run.returncode, 'outcome': 'passed' if expected_exit == 0 else 'expected_failure',
                'observed': result})
        exit_code = 0
    else:
        exit_code = meta['build_exit_code']
finally:
    if example.exists():
        assert example.read_bytes() == source.read_bytes(), 'Example changed; preserving it'
        example.unlink()
    checked = subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'])
    meta['source_check_exit_code'] = checked.returncode
    (out / 'results.json').write_text(json.dumps(meta, indent=2) + '\n')
    if checked.returncode:
        exit_code = checked.returncode
print(json.dumps(meta, indent=2))
sys.exit(exit_code)
