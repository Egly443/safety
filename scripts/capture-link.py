#!/usr/bin/env python3
"""Retain the final CLI link inputs so linking can run after rustc exits."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
root = Path(__file__).resolve().parents[1]
keep = root / '.tools/link-inputs'
keep.mkdir(exist_ok=True)
args = []
for arg in sys.argv[1:]:
    pieces = arg.split(',')
    for i, part in enumerate(pieces):
        p = Path(part)
        if p.is_file() and (str(p).startswith('/tmp/') or p.name.endswith('.o') or any(piece.startswith('rustc') for piece in p.parts)):
            dest = keep / (hashlib.sha256(str(p).encode()).hexdigest()[:12] + '-' + p.name)
            shutil.copy2(p, dest)
            pieces[i] = str(dest)
    args.append(','.join(pieces))
output = args.index('-o') + 1
args[output] = str(root / '.tools/bin/codex')
(root / '.tools/final-link.json').write_text(json.dumps({'cwd': str(Path.cwd()), 'args': ['cc'] + args}))
print('Final link inputs captured; run scripts/link-cli.py next.', file=sys.stderr)
sys.exit(99)
