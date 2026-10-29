#!/usr/bin/env python3
"""Run the captured CLI link without retaining rustc in memory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
command = json.loads((root / '.tools/final-link.json').read_text())
parser = argparse.ArgumentParser()
parser.add_argument('--backend', choices=['lld', 'gold'], default='lld')
backend = parser.parse_args().backend
# Select a standalone linker without retaining the Rust compiler in memory.
command['args'] = [a for a in command['args'] if not a.startswith('-fuse-ld=') and not (a.startswith('-B') and 'gcc-ld' in a) and a != '-Wl,--threads=1,--strip-all,--no-mmap-output-file']
if backend == 'gold':
    command['args'][1:1] = ['-fuse-ld=gold', '-Wl,--strip-all,--no-keep-files-mapped,--no-map-whole-files,--no-threads']
else:
    toolchain = Path(subprocess.check_output(['rustup', 'run', '1.99.1', 'rustc', '--print', 'sysroot'], text=True).strip())
    command['args'][1:1] = ['-fuse-ld=lld', '-B' + str(toolchain / 'lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld'), '-Wl,--threads=1,--strip-all,--no-mmap-output-file']
(root / 'evidence/cli-link-command.json').write_text(json.dumps(command, indent=2) + '\n')
result = subprocess.run(command['args'], cwd=command['cwd'], env={**os.environ, 'MALLOC_ARENA_MAX': '2'})
if result.returncode:
    raise SystemExit('CLI link failed with exit code ' + str(result.returncode))
subprocess.run([str(root / '.tools/bin/codex'), '--version'], check=True)
