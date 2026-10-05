#!/usr/bin/env bash
# Install preset and extension (--dev) into a fresh spec-kit scratch project in .scratch/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$ROOT/.scratch/proj"
command -v specify >/dev/null || { echo "specify CLI not found: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git" >&2; exit 1; }
rm -rf "$SCRATCH"; mkdir -p "$ROOT/.scratch"
(cd "$ROOT/.scratch" && specify init proj --non-interactive --integration claude)
cd "$SCRATCH"
specify preset add --dev "$ROOT/preset"
specify extension add --dev "$ROOT/extension"
specify preset list
specify extension list
echo "OK: scratch project at $SCRATCH"
