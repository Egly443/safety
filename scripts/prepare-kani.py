#!/usr/bin/env python3
"""Install only a cfg(kani) harness hook in an isolated pinned worktree."""
import hashlib
import argparse
import json
import re
import tomllib
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
checking = parser.parse_args().check
tree = root / '.tools/kani-source'
pin = json.loads((root / 'sources.lock.json').read_text())['codex']['commit']
assert subprocess.check_output(['git', '-C', str(tree), 'rev-parse', 'HEAD'], text=True).strip() == pin
lib = tree / 'codex-rs/sandboxing/src/lib.rs'
original = subprocess.check_output(['git', '-C', str(tree), 'show', 'HEAD:codex-rs/sandboxing/src/lib.rs'])
harness = root / 'verification/kani/narrow_policy.rs'
hook = '\n#[cfg(kani)]\n#[path = ' + json.dumps(str(harness)) + ']\nmod confinement_verification;\n'
assert lib.read_bytes() in (original, original + hook.encode()), 'Unexpected worktree changes'
if checking:
    assert lib.read_bytes() == original + hook.encode()
else:
    lib.write_bytes(original + hook.encode())
lock = subprocess.check_output(['git', '-C', str(tree), 'show', 'HEAD:codex-rs/Cargo.lock']).decode()
parts = lock.split('[[package]]')
for index in range(1, len(parts)):
    package = tomllib.loads('[[package]]' + parts[index])['package'][0]
    if 'source' not in package:
        assert package['version'] == '0.0.0'
        parts[index] = re.sub(r'(?m)^version = "0\.0\.0"$',
                              'version = "0.165.0"', parts[index], count=1)
corrected = '[[package]]'.join(parts).encode()
assert hashlib.sha256(corrected).hexdigest() == 'a646d4b01a0e8c62f6af9b74fb965c1bd6d3cf27a547984de09730d50e0e64da'
if checking:
    assert (tree / 'codex-rs/Cargo.lock').read_bytes() == corrected
else:
    (tree / 'codex-rs/Cargo.lock').write_bytes(corrected)
changed = set(subprocess.check_output(['git', '-C', str(tree), 'diff', '--name-only', 'HEAD'], text=True).splitlines())
assert changed <= {'codex-rs/Cargo.lock', 'codex-rs/sandboxing/src/lib.rs'}, changed
untracked = subprocess.check_output(['git', '-C', str(tree), 'ls-files', '--others', '--exclude-standard'], text=True)
assert not untracked.strip(), 'Unexpected untracked source files'
files = ['codex-rs/sandboxing/src/policy_transforms.rs',
         'codex-rs/protocol/src/permissions.rs',
         'codex-rs/utils/path-uri/src/lib.rs']
hashes = {}
for name in files:
    expected = subprocess.check_output(['git', '-C', str(tree), 'show', 'HEAD:' + name])
    assert (tree / name).read_bytes() == expected, name
    hashes[name] = hashlib.sha256(expected).hexdigest()
record = {'commit': pin, 'source_sha256': hashes, 'hook': hook,
          'harness_sha256': hashlib.sha256(harness.read_bytes()).hexdigest(),
          'lock_sha256': hashlib.sha256((tree / 'codex-rs/Cargo.lock').read_bytes()).hexdigest(),
          'stubs': [], 'production_function_changes': []}
manifest = root / 'evidence/kani-source-manifest.json'
if checking:
    assert json.loads(manifest.read_text()) == record, 'Verification inputs changed during the run'
    print('Verification inputs still match the recorded manifest.')
else:
    manifest.write_text(json.dumps(record, indent=2) + '\n')
    print('Prepared actual-source worktree; production function files match the pinned commit.')
