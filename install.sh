#!/bin/bash
# install.sh — Install claude-gemini-unified-skill to ~/.claude/skills/gemini

set -e

SKILL_DIR="$HOME/.claude/skills/gemini"

echo "Installing claude-gemini-unified-skill..."

# Clone or update
if [ -d "$SKILL_DIR/.git" ]; then
    echo "Updating existing installation..."
    git -C "$SKILL_DIR" pull
else
    echo "Cloning to $SKILL_DIR..."
    git clone https://github.com/atakhadiviom/claude-gemini-unified-skill "$SKILL_DIR"
fi

chmod +x "$SKILL_DIR/scripts/"*.sh "$SKILL_DIR/bin/gemini"

# Check prerequisites
echo ""
echo "Checking prerequisites..."
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if command -v gemini &>/dev/null; then
    echo "  [OK] Gemini CLI: $(gemini --version 2>/dev/null || echo 'installed')"
else
    echo "  [MISSING] Gemini CLI — run: npm install -g @google/gemini-cli"
fi

if command -v python3 &>/dev/null; then
    echo "  [OK] Python3: $(python3 --version)"
else
    echo "  [MISSING] Python3"
fi

if command -v jq &>/dev/null; then
    echo "  [OK] jq"
else
    echo "  [MISSING] jq — run: brew install jq"
fi

echo ""
echo "Installation complete."
echo ""
echo "To enable the automatic bridge (optional), install:"
echo "  https://github.com/tkaufmann/claude-gemini-bridge"
echo ""
echo "Then restart Claude Code."
