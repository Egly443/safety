# Source from bash to select the repository-local tools installed by cloud setup.
SAFETY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -x "$SAFETY_ROOT/.tools/cargo/bin/rustup" || ! -x "$SAFETY_ROOT/.tools/elan/bin/elan" ]]; then
    echo 'Repository-local cloud tools are missing; run the saved environment installation script first.' >&2
    return 1
fi
export RUSTUP_HOME="$SAFETY_ROOT/.tools/rustup"
export CARGO_HOME="$SAFETY_ROOT/.tools/cargo"
export ELAN_HOME="$SAFETY_ROOT/.tools/elan"
export PATH="$CARGO_HOME/bin:$ELAN_HOME/bin:$PATH"
source "$SAFETY_ROOT/scripts/env.sh"
