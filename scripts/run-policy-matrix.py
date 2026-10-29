#!/usr/bin/env python3
"""Build and execute the finite matrix against the pinned, unmodified Codex code."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[1]
tree = root / '.tools/kani-source'
source = root / 'verification/policy_matrix.rs'
out = root / '.tools/policy-matrix'
out.mkdir(exist_ok=True)
if any(out.iterdir()):
    sys.exit(f'Preserve {out} before rerunning; refusing to overwrite evidence')
for name in ('policy-matrix.json', 'policy-matrix-provenance.json'):
    if (root / 'evidence' / name).exists():
        sys.exit(f'Preserve evidence/{name} before rerunning')
subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'], check=True)
example = tree / 'codex-rs/sandboxing/examples/policy_matrix.rs'
if example.exists():
    sys.exit(f'Refusing to overwrite {example}')
target = root / '.tools/native-policy-target'
env = os.environ.copy()
env.update(CARGO_BUILD_JOBS='2', CARGO_PROFILE_DEV_DEBUG='0', CARGO_INCREMENTAL='0')
build = ['cargo', '+1.99.1', 'build', '--locked', '--manifest-path',
         str(tree / 'codex-rs/Cargo.toml'), '--target-dir', str(target),
         '-p', 'codex-sandboxing', '--example', 'policy_matrix']
meta = {'started_utc': datetime.now(timezone.utc).isoformat(),
        'source_manifest': json.loads((root / 'evidence/kani-source-manifest.json').read_text()),
        'matrix_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'build_command': build,
        'rustc': subprocess.check_output(['rustup', 'run', '1.99.1', 'rustc', '--version'], text=True).strip()}
exit_code = 2
try:
    example.parent.mkdir(exist_ok=True)
    example.write_bytes(source.read_bytes())
    (out / 'worktree.diff').write_bytes(subprocess.check_output(['git', '-C', str(tree), 'diff', '--binary']))
    guarded = [sys.executable, str(root / 'scripts/run-limited.py'), '--seconds', '900',
               '--rss-gib', '12', '--cwd', str(tree / 'codex-rs'),
               '--record', str(out / 'build-resources.json'),
               '--log', str(out / 'build.log'), '--', *build]
    compiled = subprocess.run(guarded, env=env)
    meta['build_runner_exit_code'] = compiled.returncode
    if compiled.returncode == 0:
        binary = target / 'debug/examples/policy_matrix'
        meta['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        executed = subprocess.run([str(binary)], capture_output=True, text=True, timeout=60)
        (out / 'stderr.log').write_text(executed.stderr)
        (out / 'stdout.json').write_text(executed.stdout)
        meta['execution_exit_code'] = executed.returncode
        data = json.loads(executed.stdout)
        assert data['fixtures'] == 36
        assert data['scenarios_per_fixture'] == 10
        assert len(data['observations']) == 3960
        assert len(data['structural_checks']) == 1800
        failed = sum(not r['passed'] for r in data['observations'] + data['structural_checks'])
        assert failed == data['failures']
        assert (executed.returncode == 0) == (failed == 0)
        (root / 'evidence/policy-matrix.json').write_text(json.dumps(data, indent=2) + '\n')
        meta['observations'] = len(data['observations'])
        meta['structural_checks'] = len(data['structural_checks'])
        meta['failures'] = failed
        exit_code = executed.returncode
    else:
        exit_code = compiled.returncode
finally:
    if example.exists():
        assert example.read_bytes() == source.read_bytes(), 'Temporary example changed; preserving it'
        example.unlink()
    checked = subprocess.run([sys.executable, str(root / 'scripts/prepare-kani.py'), '--check'])
    meta['source_check_exit_code'] = checked.returncode
    meta['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (root / 'evidence/policy-matrix-provenance.json').write_text(json.dumps(meta, indent=2) + '\n')
    if checked.returncode:
        exit_code = checked.returncode
print(json.dumps(meta, indent=2))
sys.exit(exit_code)
