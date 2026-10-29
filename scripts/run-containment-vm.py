#!/usr/bin/env python3
"""Package the real sandbox helper and execute containment cases in a fresh VM."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
os.chdir(root)
vm = root / '.tools/vm'
stage = vm / 'payload'
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir()
libdir = stage / 'lib'
libdir.mkdir(exist_ok=True)
helper = root / '.tools/codex-target/debug/codex-linux-sandbox'
bwrap = root / '.tools/bin/bwrap'
cli = root / '.tools/bin/codex'
binaries = [helper, bwrap, Path('/usr/bin/strace')]
if cli.exists():
    binaries.append(cli)
for binary in binaries:
    shutil.copy2(binary, stage / binary.name)
    out = subprocess.check_output(['ldd', str(binary)], text=True)
    for library in re.findall(r'=> (/\S+)', out):
        p = Path(library)
        if p.name in ('libc.so.6', 'libm.so.6', 'libpthread.so.0', 'libdl.so.2', 'librt.so.1'):
            continue
        shutil.copy2(p, libdir / p.name)
shutil.copy2(root / 'integration/run_containment.py', stage / 'run_containment.py')
seed = vm / 'containment-seed'
seed.mkdir(exist_ok=True)
for name in ('meta-data', 'network-config'):
    shutil.copy2(root / 'integration/vm-seed' / name, seed / name)
(seed / 'user-data').write_text('''#cloud-config
users: []
ssh_pwauth: false
package_update: false
runcmd:
  - [sh, -c, 'mkdir -p /mnt/payload /usr/local/lib/safety; mount -o ro /dev/sr1 /mnt/payload; cp /mnt/payload/codex-linux-sandbox /mnt/payload/bwrap /mnt/payload/strace /usr/local/bin/; chmod 755 /usr/local/bin/codex-linux-sandbox /usr/local/bin/bwrap /usr/local/bin/strace; if test -f /mnt/payload/codex; then cp /mnt/payload/codex /usr/local/bin/; chmod 755 /usr/local/bin/codex; fi; cp /mnt/payload/lib/* /usr/local/lib/safety/; echo /usr/local/lib/safety > /etc/ld.so.conf.d/safety.conf; ldconfig; sysctl -w kernel.apparmor_restrict_unprivileged_userns=0; LD_LIBRARY_PATH=/usr/local/lib/safety /usr/bin/python3 /mnt/payload/run_containment.py > /dev/ttyS0 2>&1']
power_state:
  mode: poweroff
  timeout: 120
  condition: true
''')
subprocess.run(['genisoimage', '-quiet', '-o', str(vm / 'payload.iso'), '-V', 'SAFETY', '-J', '-R', str(stage)], check=True)
subprocess.run(['genisoimage', '-quiet', '-o', str(vm / 'containment-seed.iso'), '-V', 'cidata', '-J', '-R'] + [str(seed / n) for n in ('user-data','meta-data','network-config')], check=True)
image = vm / 'ubuntu-24.04-minimal-20261027-amd64.img'
lock = json.loads((root / 'prerequisites.lock.json').read_text())
assert hashlib.sha256(image.read_bytes()).hexdigest() == lock['vm']['sha256']
assert hashlib.sha256((vm / 'vmlinuz').read_bytes()).hexdigest() == '41ba36d860aa0b0cd995f4ca8856d80249b244577e704929b55be13fbd1ebd2f'
log = root / 'evidence/containment-vm.log'
cmd = ['timeout', '600', 'qemu-system-x86_64', '-machine', 'accel=tcg', '-cpu', 'max',
       '-m', '1024', '-smp', '2',
       '-kernel', str(vm / 'vmlinuz'), '-append',
       'root=PARTUUID=e4b514e9-f821-40c5-90b6-f8bb12336fc7 ro console=ttyS0 systemd.mask=systemd-networkd-wait-online.service', '-display', 'none', '-serial', f'file:{log}',
       '-monitor', 'none', '-nic', 'none', '-snapshot', '-drive',
       f'file={image},format=qcow2,if=virtio', '-drive',
       f'file={vm / "containment-seed.iso"},format=raw,media=cdrom', '-drive',
       f'file={vm / "payload.iso"},format=raw,media=cdrom', '-no-reboot']
subprocess.run(cmd, env={**os.environ, 'TMPDIR': str(vm)}, check=True)
output = log.read_text(errors='replace')
match = re.search(r'SAFETY_RESULTS_BEGIN\s*\n(.*?)\nSAFETY_RESULTS_END', output, re.S)
if not match:
    raise SystemExit('VM did not produce a report; inspect evidence/containment-vm.log')
report = json.loads(match[1])
report['vm_command'] = cmd
report['source_pins'] = json.loads((root / 'sources.lock.json').read_text())
report['build_lock_sha256'] = hashlib.sha256((root / 'evidence/Cargo.lock.build').read_bytes()).hexdigest()
(root / 'evidence/containment-results.json').write_text(json.dumps(report, indent=2) + '\n')
for result in report['results']:
    print(('PASS' if result['passed'] else 'FAIL') + ' ' + result['name'])
raise SystemExit(0 if all(r['passed'] for r in report['results']) else 1)
