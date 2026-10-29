#!/usr/bin/env python3
"""Build a small, deterministic, source-only Cloud retry handoff."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parents[1]
files = [
    'scripts/env.sh', 'scripts/fetch_sources.py', 'scripts/prepare-kani.py',
    'scripts/run-limited.py', 'scripts/kani-feasibility.sh',
    'scripts/cloud-kani-bootstrap.sh', 'verification/kani/narrow_policy.rs',
    'verification/CONTRACT.md', 'verification/CLOUD_RETRY.md', 'sources.lock.json',
]
payload = {name: (root / name).read_bytes() for name in files}
payload['.gitignore'] = b'.tools/\nupstream/\n__pycache__/\nevidence/*.log\n'
payload['PAYLOAD_MANIFEST.json'] = (json.dumps({
    'format': 1, 'purpose': 'actual-code smoke feasibility retry; not a bounded theorem',
    'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())},
}, indent=2) + '\n').encode()
buffer = io.BytesIO()
with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, mtime=0) as compressed:
    with tarfile.open(fileobj=compressed, mode='w') as archive:
        for name, data in sorted(payload.items()):
            info = tarfile.TarInfo('safety-proof-retry/' + name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
data = buffer.getvalue()
digest = hashlib.sha256(data).hexdigest()
(root / 'evidence/kani-cloud-retry.tar.gz').write_bytes(data)
encoded = base64.b64encode(data).decode()
prompt = '''# Controlled actual-code Kani retry

Run this one verification experiment in a published Linux x86-64 Codex Cloud
environment with nominal RAM of at least 16 GiB and at least 20 GiB free disk
before setup. Verify actual memory limits. If unavailable, report that and stop.
Do not purchase or provision external compute, create subagents, modify the
environment's repository, commit, push, or open a pull request.

The laptop compiled actual pinned Codex code but obtained no proof: one run hit
a 4 GiB RSS guard, and a short-path follow-up hit its five-minute wall limit.
This retry changes resource budgets only, using that exact short fixture.

Read applicable environment/runtime instructions. Preserve proxies, CA trust,
credential guard variables, and TLS verification. Use environment setup for
missing dependencies or network permissions; do not bypass restrictions.

Materialize the source-only payload in a fresh subdirectory with this Python
snippet. It contains no credentials, conversation history, or compiled binaries.

```python
import base64, hashlib, io, tarfile, tempfile
from pathlib import Path, PurePosixPath
data = base64.b64decode("ENCODED_PAYLOAD")
assert hashlib.sha256(data).hexdigest() == "ARCHIVE_DIGEST"
work = Path(tempfile.mkdtemp(prefix="safety-proof-", dir=Path.cwd()))
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
    for member in archive.getmembers():
        parts = PurePosixPath(member.name).parts
        assert member.isfile() and parts[0] == "safety-proof-retry"
        assert ".." not in parts and not member.name.startswith("/")
        target = work.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.extractfile(member).read())
print(work / "safety-proof-retry")
```

Read `verification/CONTRACT.md` and `verification/CLOUD_RETRY.md`. Verify every
file against `PAYLOAD_MANIFEST.json`. From the printed payload directory, run:

```bash
bash scripts/cloud-kani-bootstrap.sh
bash scripts/kani-feasibility.sh --seconds 1200 --rss-gib 8
```

Run only this experiment, one job at a time. Do not build the full CLI or run the
VM. Do not change the harness, unwind setting, production code, dependencies,
or intended claim. Do not add stubs or disable safety/unwinding checks.

Return the complete verifier log, resource JSON, source manifest, exact tool
versions, and worktree diff. Classify resource stops as inconclusive. Do not
infer success from compilation or a zero exit alone: report harness counts,
assertion results and unwinding checks. A successful smoke run still needs a
must-fail reachability control before the bounded theorem is attempted.
Stop and report this experiment's result; do not silently redesign the proof.
'''.replace('ENCODED_PAYLOAD', encoded).replace('ARCHIVE_DIGEST', digest)
(root / 'verification/CLOUD_TASK.md').write_text(prompt)
(root / 'evidence/kani-cloud-retry.sha256').write_text(digest + '  kani-cloud-retry.tar.gz\n')
print(json.dumps({'archive_bytes': len(data), 'archive_sha256': digest,
                  'prompt_bytes': len(prompt.encode()), 'files': len(payload)}))
