# Claude-Gemini Unified Skill

![Stars](https://img.shields.io/github/stars/atakhadiviom/claude-gemini-unified-skill?style=flat-square)
![License](https://img.shields.io/github/license/atakhadiviom/claude-gemini-unified-skill?style=flat-square)

Claude-Gemini Unified Skill is a high-performance orchestration layer for Claude Code that delegates resource-intensive tasks to Google Gemini. By unifying content offloading, code co-processing, and automated tool-call interception, it allows Claude to leverage Gemini's 2-million-token context window for large-scale codebase analysis and long-form content generation while maintaining Claude's precision for execution.

## Why Use This?

* **Massive Token Savings**: Offload large file reads and multi-file tasks (>50k tokens) to Gemini to prevent Claude's context window from bloating.
* **Context Superiority**: Utilize Gemini's 2M token window to analyze entire repositories or massive documentation sets that exceed Claude's native limits.
* **Specialized Routing**: Automatically directs tasks to the most efficient model — Gemini CLI for content/planning, Gemini API for deep code reasoning.

## How It Works

The skill operates as a three-layer architecture:

```
[ Claude Code ]
      |
      v
[ Unified Gemini Skill ]
      |
      +---- (Auto Intercept) ----> [ Gemini Bridge ] ----> Large reads/greps (>50k tokens)
      |
      +---- (Writing Task)   ----> [ Content Path  ] ----> Planning, docs, proposals
      |
      +---- (Code Task)      ----> [ gcop Path     ] ----> Analysis, review, diffs, reasoning
```

## Requirements

* **Gemini CLI**: `npm install -g @google/gemini-cli` — then run `gemini` once to authenticate
* **Python 3**: Version 3.9+
* **jq**: `brew install jq` (macOS) or `apt install jq` (Linux)
* **OS**: macOS or Linux

## Installation

```bash
git clone https://github.com/atakhadiviom/claude-gemini-unified-skill ~/.claude/skills/gemini
chmod +x ~/.claude/skills/gemini/scripts/*.sh
```

To enable the **Automatic Bridge** (auto-intercepts large tool calls), add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Read|Grep|Glob|Task",
      "hooks": [{"type": "command", "command": "/path/to/claude-gemini-bridge/hooks/gemini-bridge.sh"}]
    }]
  }
}
```

> The bridge backend is a separate project: [tkaufmann/claude-gemini-bridge](https://github.com/tkaufmann/claude-gemini-bridge)

## Routing Table

| Task Type | Path | Commands | Model |
| :--- | :--- | :--- | :--- |
| Writing, Planning, Docs, Proposals | Content | write task file → try_gemini.sh | pro |
| Code Analysis, Review, Refactoring | gcop | `analyze`, `generate` | pro |
| Git Diffs & Log Summarization | gcop | `diff`, `summarize` | flash |
| Architectural Reasoning | gcop | `reason` | pro |
| Codebase Q&A | gcop | `ask` | pro |
| UI/UX Screenshot Audit | gcop | `vision` | pro |
| Bulk File Operations | gcop | `bulk` | pro |
| Large reads / multi-file ops | Bridge | auto-intercepted | — |

## Usage

Claude Code will automatically invoke this skill for matching tasks. You can also trigger it directly via the skill system in Claude Code.

**Content path** — Claude writes a structured task to `/tmp/gemini_task.txt` then runs:
```bash
bash ~/.claude/skills/gemini/scripts/try_gemini.sh /tmp/gemini_task.txt
```

**Code path** — Claude runs:
```bash
bash ~/.claude/skills/gemini/scripts/run_gcop.sh <command> [args]
# Examples:
bash ~/.claude/skills/gemini/scripts/run_gcop.sh analyze --file src/main.py --focus security
git diff | bash ~/.claude/skills/gemini/scripts/run_gcop.sh diff
bash ~/.claude/skills/gemini/scripts/run_gcop.sh reason "Explain the concurrency model in this codebase"
```

## Model Selection

| Flag | Model | Best For |
| :--- | :--- | :--- |
| `--model pro` | Gemini Pro | Complex reasoning, code generation (default) |
| `--model flash` | Gemini Flash | Fast summaries, simple diffs |
| `--model 2.5-pro` | Gemini 2.5 Pro | Maximum reasoning depth |

## License

MIT
