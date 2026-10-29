#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
source scripts/env.sh
mkdir -p evidence
if [[ ! -e .tools/kani-source/.git ]]; then
    git -C upstream/codex worktree add --detach "$SAFETY_ROOT/.tools/kani-source" 360319d8dee62d87e2d59fc0c21805d79519cfed
fi
python3 scripts/prepare-kani.py
export CARGO_HOME="$SAFETY_ROOT/.tools/cargo"
export CARGO_BUILD_JOBS=1
export CARGO_NET_OFFLINE="${CARGO_NET_OFFLINE:-false}"
export CARGO_PROFILE_DEV_DEBUG=0
export CARGO_INCREMENTAL=0
set +e
python3 scripts/run-limited.py --seconds 1200 --rss-gib 4 \
    --cwd "$SAFETY_ROOT/.tools/kani-source/codex-rs" \
    --record "$SAFETY_ROOT/evidence/kani-feasibility-resources.json" \
    --log "$SAFETY_ROOT/evidence/kani-feasibility.log" "$@" -- \
    cargo kani --manifest-path "$SAFETY_ROOT/.tools/kani-source/codex-rs/Cargo.toml" \
    --target-dir "$SAFETY_ROOT/.tools/kani-target" \
    -p codex-sandboxing --harness actual_policy_smoke
result=$?
set -e
python3 scripts/prepare-kani.py --check
exit "$result"
