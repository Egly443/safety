# Source from bash to use this project's local prerequisites.
SAFETY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$SAFETY_ROOT/.tools/bin:$SAFETY_ROOT/.venv/bin:$PATH"
export KANI_HOME="$SAFETY_ROOT/.tools/kani"
export CARGO_BUILD_JOBS=2
