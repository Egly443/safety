"""Run only inside the disposable VM. No external dependencies."""
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/var/lib/safety-fixtures')
WS = ROOT / 'workspace'
OUT = ROOT / 'outside'
PROTECTED = WS / 'protected'
HELPER = '/usr/local/bin/codex-linux-sandbox'
for p in (WS, OUT, PROTECTED):
    p.mkdir(parents=True, exist_ok=True)
    os.chown(p, 1000, 1000)
(PROTECTED / 'sentinel').write_text('unchanged')
os.chown(PROTECTED / 'sentinel', 1000, 1000)
(WS / 'escape').symlink_to(OUT, target_is_directory=True)
(WS / 'protected-alias').symlink_to(PROTECTED, target_is_directory=True)

def entry(path, access):
    return {'path': {'type': 'path', 'path': str(path)}, 'access': access}

profile = {'type': 'managed', 'network': 'restricted', 'file_system': {
    'type': 'restricted', 'entries': [entry('/', 'read'), entry(WS, 'write'),
                                    entry(PROTECTED, 'read')]}}

def demote():
    os.setgroups([])
    os.setgid(1000)
    os.setuid(1000)

env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(WS),
       'LD_LIBRARY_PATH': '/usr/local/lib/safety'}
results = []
if Path('/usr/local/bin/codex').exists():
    cli = subprocess.run(['/usr/local/bin/codex', '--version'], env=env,
                         preexec_fn=demote, capture_output=True, text=True, timeout=40)
    results.append({'name': 'installed-cli-version', 'passed': cli.returncode == 0 and cli.stdout.strip() == 'codex-cli 0.165.0',
                    'returncode': cli.returncode, 'stdout': cli.stdout, 'stderr': cli.stderr})

def run(name, code, expected=True, raw=False, custom_profile=None, custom_env=None):
    args = ['/usr/bin/python3', '-c', code]
    if not raw:
        args = [HELPER, '--sandbox-policy-cwd', str(WS), '--permission-profile',
                json.dumps(profile if custom_profile is None else custom_profile), '--'] + args
    try:
        r = subprocess.run(args, cwd=WS, env=custom_env or env, preexec_fn=demote,
                           capture_output=True, text=True, timeout=40)
        passed = (r.returncode == 0) == expected
        results.append({'name': name, 'passed': passed, 'returncode': r.returncode,
                        'argv': args, 'stdout': r.stdout, 'stderr': r.stderr})
    except Exception as exc:
        results.append({'name': name, 'passed': False, 'error': repr(exc), 'argv': args})

def write(path):
    return f"from pathlib import Path; Path({str(path)!r}).write_text('ok')"

def denied(path):
    return f'''import errno
try:
    open({str(path)!r}, 'w').write('escape')
except OSError as e:
    assert e.errno in (errno.EACCES, errno.EPERM, errno.EROFS), repr(e)
else:
    raise AssertionError('write unexpectedly allowed')
'''

run('unsandboxed-outside-positive-control', write(OUT / 'control'), raw=True)
run('permitted-workspace-write', write(WS / 'allowed') + "; import os,json; print(json.dumps({f: os.readlink('/proc/self/fd/'+f) for f in os.listdir('/proc/self/fd') if os.path.exists('/proc/self/fd/'+f)}))")
run('outside-workspace-denied', denied(OUT / 'denied'))
run('protected-subtree-denied', denied(PROTECTED / 'sentinel'))
run('symlink-outside-denied', denied(WS / 'escape' / 'denied'))
run('symlink-protected-denied', denied(WS / 'protected-alias' / 'sentinel'))
run('missing-workspace-path-created', write(WS / 'new-file'))
run('missing-outside-path-denied', denied(OUT / 'missing-file'))
child = denied(PROTECTED / 'child')
run('descendant-write-denied', f'import subprocess,sys; subprocess.run([sys.executable,"-c",{child!r}],check=True)')
run('network-socket-denied', '''import socket,errno
try:
    socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except OSError as e:
    assert e.errno in (errno.EPERM,errno.EACCES), repr(e)
else:
    raise AssertionError('network socket unexpectedly allowed')
''')
run('pid-namespace-isolated', f"import os; assert os.readlink('/proc/self/ns/pid') != {os.readlink('/proc/self/ns/pid')!r}")
run('setup-failure-does-not-execute', write(WS / 'must-not-exist'), expected=False,
    custom_profile={'type': 'invalid-profile'})
# PATH removal alone still permits the sibling bundled-bwrap discovery path.
bwrap_path = Path('/usr/local/bin/bwrap')
bwrap_hidden = Path('/usr/local/bin/bwrap.disabled')
bwrap_path.rename(bwrap_hidden)
try:
    run('missing-bwrap-does-not-execute', write(WS / 'missing-bwrap-ran'), expected=False,
        custom_env={**env, 'PATH': '/nonexistent'})
finally:
    bwrap_hidden.rename(bwrap_path)
results.append({'name': 'missing-bwrap-no-side-effect', 'passed': not (WS / 'missing-bwrap-ran').exists()})
results.append({'name': 'setup-failure-no-side-effect', 'passed': not (WS / 'must-not-exist').exists()})
results.append({'name': 'protected-sentinel-unchanged', 'passed': (PROTECTED / 'sentinel').read_text() == 'unchanged'})
# Separate diagnostic run: assertions above are measured without ptrace.
trace_file = WS / 'exec-trace'
trace_command = ['/usr/local/bin/strace', '-f', '-s', '65535', '-e', 'trace=execve,execveat',
                 '-o', str(trace_file), HELPER, '--sandbox-policy-cwd', str(WS),
                 '--permission-profile', json.dumps(profile), '--', '/usr/bin/true']
try:
    trace = subprocess.run(trace_command, cwd=WS, env=env, preexec_fn=demote,
                           capture_output=True, text=True, timeout=40)
    trace_info = {'returncode': trace.returncode, 'stderr': trace.stderr,
                  'exec_trace': trace_file.read_text() if trace_file.exists() else None}
except Exception as exc:
    trace_info = {'error': repr(exc)}
report = {'vm_configuration': {k: Path('/proc/sys/' + k.replace('.', '/')).read_text().strip() for k in ('kernel.apparmor_restrict_unprivileged_userns', 'user.max_user_namespaces')}, 'binary_ownership': {p: {'uid': Path(p).stat().st_uid, 'mode': oct(Path(p).stat().st_mode & 0o777)} for p in ([HELPER, '/usr/local/bin/bwrap'] + (['/usr/local/bin/codex'] if Path('/usr/local/bin/codex').exists() else []))}, 'diagnostic_trace': trace_info, 'kernel': os.uname().release, 'profile': profile,
          'hashes': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                     for p in ([HELPER, '/usr/local/bin/bwrap'] + (['/usr/local/bin/codex'] if Path('/usr/local/bin/codex').exists() else []))},
          'inherited_fds': sorted(os.listdir('/proc/self/fd')), 'results': results}
print('SAFETY_RESULTS_BEGIN')
print(json.dumps(report, sort_keys=True))
print('SAFETY_RESULTS_END')
print('SAFETY_CONTAINMENT_' + ('PASS' if all(r['passed'] for r in results) else 'FAIL'), flush=True)
