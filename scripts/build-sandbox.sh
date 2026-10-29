#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
source scripts/env.sh
mkdir -p evidence .tools
python3 scripts/fetch_sources.py
# The release lock has stale versions for workspace packages only.
cp upstream/codex/codex-rs/Cargo.lock .tools/Cargo.lock.before-build
trap 'cp .tools/Cargo.lock.before-build upstream/codex/codex-rs/Cargo.lock' EXIT
export CARGO_HOME="$SAFETY_ROOT/.tools/cargo"
export CARGO_TARGET_DIR="$SAFETY_ROOT/.tools/codex-target"
export CARGO_PROFILE_DEV_DEBUG=0
cargo +1.99.1 build --manifest-path upstream/codex/codex-rs/Cargo.toml -p codex-linux-sandbox
cp .tools/codex-target/debug/codex-linux-sandbox .tools/bin/codex-linux-sandbox
if [[ "${1:-}" == cli ]]; then
    rm -f .tools/final-link.json
    # The capture linker deliberately exits 99 after retaining transient inputs.
    if ! MALLOC_ARENA_MAX=2 cargo +1.99.1 rustc -j 1 --locked --manifest-path upstream/codex/codex-rs/Cargo.toml -p codex-cli --bin codex -- -C linker="$SAFETY_ROOT/scripts/capture-link.py" -C linker-flavor=gcc -C link-arg=-Wl,--threads=1,--strip-all,--no-mmap-output-file; then
        test -s .tools/final-link.json
    fi
    python3 scripts/link-cli.py
fi
python3 - <<'PY'
from pathlib import Path
import tomllib
original = Path('.tools/Cargo.lock.before-build')
resolved = Path('upstream/codex/codex-rs/Cargo.lock')
a, b = (tomllib.loads(p.read_text()) for p in (original, resolved))
assert [p for p in a['package'] if 'source' in p] == [p for p in b['package'] if 'source' in p], 'External dependencies changed'
Path('evidence/Cargo.lock.build').write_bytes(resolved.read_bytes())
PY
