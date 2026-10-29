#!/usr/bin/env python3
"""Extract the kernel from the checksum-pinned image without mounting it."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
root = Path(__file__).resolve().parents[1]
vm = root / '.tools/vm'
image = vm / 'ubuntu-24.04-minimal-20261027-amd64.img'
lock = json.loads((root / 'prerequisites.lock.json').read_text())
assert hashlib.sha256(image.read_bytes()).hexdigest() == lock['vm']['sha256']
raw, boot = vm / 'extract.raw', vm / 'boot.ext4'
try:
    subprocess.run(['qemu-img', 'convert', '-O', 'raw', str(image), str(raw)], check=True)
    with raw.open('rb') as src:
        src.seek(512)
        header = src.read(512)
        assert header[:8] == b'EFI PART'
        table = struct.unpack_from('<Q', header, 72)[0] * 512
        # GPT entry 15 is this frozen Ubuntu image's separate /boot partition.
        src.seek(table + 15 * 128)
        entry = src.read(128)
        start, end = struct.unpack_from('<QQ', entry, 32)
        assert (start, end) == (227328, 2097152)
        size = (end - start + 1) * 512
        src.seek(start * 512)
        with boot.open('wb') as dst:
            while size:
                chunk = src.read(min(size, 8 * 1024 * 1024))
                if not chunk:
                    raise RuntimeError('short partition read')
                size -= len(chunk)
                if chunk.count(0) == len(chunk):
                    dst.seek(len(chunk), 1)
                else:
                    dst.write(chunk)
            dst.truncate()
    subprocess.run(['debugfs', '-R', f'dump /vmlinuz-6.8.0-147-generic {vm / "vmlinuz"}', str(boot)], check=True)
    assert hashlib.sha256((vm / 'vmlinuz').read_bytes()).hexdigest() == '41ba36d860aa0b0cd995f4ca8856d80249b244577e704929b55be13fbd1ebd2f'
finally:
    raw.unlink(missing_ok=True)
    boot.unlink(missing_ok=True)
