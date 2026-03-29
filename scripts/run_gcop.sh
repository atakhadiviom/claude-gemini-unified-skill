#!/bin/bash
# run_gcop.sh — wrapper to invoke gcop (gemini co-processor) from Claude skills
# Usage: bash ~/.claude/skills/gcop/scripts/run_gcop.sh <command> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
GCOP_BIN="$SKILL_ROOT/bin/gemini"

# Expand PATH to include common Node/gemini install locations
NVM_DIR="$HOME/.nvm"
if [ -d "$NVM_DIR/versions/node" ]; then
    LATEST_NODE=$(ls "$NVM_DIR/versions/node" 2>/dev/null | sort -V | tail -1)
    if [ -n "$LATEST_NODE" ]; then
        export PATH="$NVM_DIR/versions/node/$LATEST_NODE/bin:$PATH"
    fi
fi
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

if [ ! -f "$GCOP_BIN" ]; then
    echo '{"status":"error","error":"gcop bin not found at '"$GCOP_BIN"'"}'
    exit 1
fi

exec python3 "$GCOP_BIN" "$@"
