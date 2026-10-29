#!/usr/bin/env python3
"""Report availability without changing machine configuration."""
import shutil
import subprocess

checks = {
    "Rust (target 1.99.1)": ["rustup", "run", "1.99.1", "rustc", "--version"],
    "Lean": ["elan", "run", "leanprover/lean4:v4.34.1", "lean", "--version"],
    "Kani": ["cargo", "kani", "--version"],
    "pytest": [".venv/bin/python", "-m", "pytest", "--version"],
    "bubblewrap (target 0.13.1)": ["bwrap", "--version"],
    "strace": ["strace", "--version"],
    "QEMU": ["qemu-system-x86_64", "--version"],
    "Meson": ["meson", "--version"],
}
for name, command in checks.items():
    if not shutil.which(command[0]):
        print(f"{name}: MISSING")
        continue
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout or result.stderr).strip().splitlines()
    status = 'OK' if result.returncode == 0 else 'UNAVAILABLE'
    if command[0] == 'bwrap' and result.stdout.strip() != 'bubblewrap 0.13.1':
        status = 'VERSION MISMATCH'
    print(f"{name}: {status}: "
          f"{output[0] if output else 'no output'}")
