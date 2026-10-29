#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
[[ "$(uname -m)" == x86_64 ]] || { echo 'Requires Linux x86-64'; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo 'Requires Linux x86-64'; exit 1; }
for tool in rustup cargo git cc cmake perl pkg-config curl python3; do
    command -v "$tool" >/dev/null || { echo "Missing setup prerequisite: $tool"; exit 1; }
done
pkg-config --exists openssl || { echo 'Install OpenSSL development files through environment setup'; exit 1; }
python3 - <<'PY'
import os, sys
from pathlib import Path
assert sys.version_info >= (3, 11), 'Python 3.11 or newer required'
memory = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
cap = Path('/sys/fs/cgroup/memory.max')
if cap.exists() and cap.read_text().strip() != 'max':
    memory = min(memory, int(cap.read_text()))
assert memory >= 14 * 1024**3, 'Use a nominal 16 GiB or larger Cloud VM; do not raise laptop limits'
disk = os.statvfs('.')
assert disk.f_bavail * disk.f_frsize >= 20 * 1024**3, 'At least 20 GiB free disk required before setup'
PY
mkdir -p .tools evidence
source scripts/env.sh
rustup toolchain install 1.99.1 --profile minimal --component rust-src
cargo +1.99.1 install --force --locked kani-verifier --version 0.68.0 --root "$SAFETY_ROOT/.tools"
curl -fL --connect-timeout 15 --max-time 600 \
    https://github.com/model-checking/kani/releases/download/kani-0.68.0/kani-0.68.0-x86_64-unknown-linux-gnu.tar.gz \
    -o .tools/kani-0.68.0-x86_64-unknown-linux-gnu.tar.gz
python3 - <<'PY'
import hashlib
from pathlib import Path
p = Path('.tools/kani-0.68.0-x86_64-unknown-linux-gnu.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '32e2b484d73ede0bbf64a2cf0879c4259422497d8aec4ee67d448de9ae7843d3'
PY
# Keep inherited Cargo/rustup authentication and proxy settings for setup.
cargo +1.99.1 kani setup --use-local-bundle "$SAFETY_ROOT/.tools/kani-0.68.0-x86_64-unknown-linux-gnu.tar.gz"
python3 scripts/fetch_sources.py
echo 'Setup complete. Run: bash scripts/kani-feasibility.sh --seconds 1200 --rss-gib 8'
