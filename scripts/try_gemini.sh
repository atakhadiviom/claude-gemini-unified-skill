#!/bin/bash
# try_gemini.sh — attempt to run a task with Gemini CLI
# Usage: try_gemini.sh <task_file>
# Exit 0 + prints output if Gemini succeeded
# Exit 1 + prints reason if Gemini failed or unavailable

# Expand PATH to include Homebrew, nvm, and other common Node/tool locations
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node 2>/dev/null | sort -V | tail -1)/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

TASK_FILE="$1"

if [ -z "$TASK_FILE" ] || [ ! -f "$TASK_FILE" ]; then
    echo "GEMINI_SKIP: no task file provided" >&2
    exit 1
fi

TASK=$(cat "$TASK_FILE")

# Check if gemini CLI is installed
GEMINI_BIN=""
for candidate in gemini gemini-cli; do
    if command -v "$candidate" &>/dev/null; then
        GEMINI_BIN="$candidate"
        break
    fi
done

# Also check common install paths (including Homebrew)
if [ -z "$GEMINI_BIN" ]; then
    for path in \
        "/opt/homebrew/bin/gemini" \
        "/usr/local/bin/gemini" \
        "$HOME/.npm-global/bin/gemini" \
        "$HOME/.local/bin/gemini" \
        "$(npm root -g 2>/dev/null)/.bin/gemini"; do
        if [ -x "$path" ]; then
            GEMINI_BIN="$path"
            break
        fi
    done
fi

if [ -z "$GEMINI_BIN" ]; then
    echo "GEMINI_SKIP: gemini CLI not installed (run: npm install -g @google/gemini-cli)" >&2
    exit 1
fi

# Run task with Gemini
# Use GEMINI_MODEL env var if set, otherwise default to gemini-3.1-pro
# Loading/auth noise goes to stderr; actual response goes to stdout
# One MCP warning line may appear in stdout — strip it
if [ -n "${GEMINI_MODEL:-}" ]; then
    OUTPUT=$("$GEMINI_BIN" --model "$GEMINI_MODEL" -p "$TASK" 2>/tmp/gemini_stderr.txt)
else
    OUTPUT=$("$GEMINI_BIN" -p "$TASK" 2>/tmp/gemini_stderr.txt)
fi
EXIT_CODE=$?

# Strip known Gemini status prefixes that appear inline on the response line
OUTPUT=$(echo "$OUTPUT" | sed \
    -e 's/^MCP issues detected\. Run \/mcp list for status\.//g' \
    -e 's/^Loaded cached credentials\.//g' \
    | grep -v "^Loading extension:\|^\[MCP\|^Server '.*' supports\|^Listening for\|^$" | head -c 100000)

# Check for failure signals
if [ $EXIT_CODE -ne 0 ]; then
    echo "GEMINI_FAILED: exit code $EXIT_CODE" >&2
    cat /tmp/gemini_stderr.txt >&2
    exit 1
fi

if [ -z "$(echo "$OUTPUT" | tr -d '[:space:]')" ]; then
    echo "GEMINI_FAILED: empty output" >&2
    exit 1
fi

# Only fail on hard API-level errors, not MCP extension warnings
FAILURE_PATTERNS="rate limit\|quota exceeded\|api key not\|invalid api key\|authentication failed\|permission denied\|billing account\|billing error\|billing required"
if echo "$OUTPUT" | grep -qi "$FAILURE_PATTERNS"; then
    echo "GEMINI_FAILED: API error in output" >&2
    echo "$OUTPUT" >&2
    exit 1
fi

# Success — print Gemini's output
echo "$OUTPUT"
exit 0
