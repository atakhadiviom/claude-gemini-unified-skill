# Claude-Gemini Unified Skill

![Stars](https://img.shields.io/github/stars/atakhadiviom/claude-gemini-unified-skill?style=flat-square)
![License](https://img.shields.io/github/license/atakhadiviom/claude-gemini-unified-skill?style=flat-square)

Claude-Gemini Unified Skill is a high-performance orchestration layer for Claude Code that delegates resource-intensive tasks to Google Gemini. By unifying content offloading, code co-processing, and automated tool-call interception, it allows Claude to leverage Gemini's 2-million-token context window for large-scale codebase analysis and long-form content generation while maintaining Claude's precision for execution.

## Why Use This?

* **Massive Token Savings**: Offload large file reads and multi-file tasks (>50k tokens) to Gemini to prevent Claude's context window from bloating.
* **Context Superiority**: Utilize Gemini's 2M token window to analyze entire repositories or massive documentation sets that exceed Claude's native limits.
* **Specialized Routing**: Automatically directs tasks to the most efficient model — latest Gemini 3.x for power, Flash for speed.

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

To enable the **Automatic Bridge** (auto-intercepts large tool calls), install the bridge backend and add to `~/.claude/settings.json`:

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

> Bridge backend: [tkaufmann/claude-gemini-bridge](https://github.com/tkaufmann/claude-gemini-bridge)

## Routing Table

| Task Type | Path | Commands | Model |
| :--- | :--- | :--- | :--- |
| Writing, Planning, Docs, Proposals | Content | write task file → try_gemini.sh | gemini-3.1-pro-preview |
| Code Analysis, Review, Refactoring | gcop | `analyze`, `generate` | gemini-3.1-pro-preview |
| Git Diffs & Log Summarization | gcop | `diff`, `summarize` | gemini-3-flash-preview |
| Architectural Reasoning | gcop | `reason` | gemini-3.1-pro-preview |
| Codebase Q&A | gcop | `ask` | gemini-3.1-pro-preview |
| UI/UX Screenshot Audit | gcop | `vision` | gemini-3.1-pro-preview |
| Bulk File Operations | gcop | `bulk` | gemini-3-flash-preview |
| Large reads / multi-file ops | Bridge | auto-intercepted | — |

## Model Reference

| Model ID | Description |
| :--- | :--- |
| `gemini-3.1-pro-preview` | Latest — advanced intelligence, agentic coding (Preview) |
| `gemini-3-flash-preview` | Fast — frontier-class performance at low cost (Preview) |
| `gemini-2.5-pro` | Stable — deep reasoning and coding (Production) |
| `gemini-2.5-flash` | Stable — best price-performance for high-volume tasks (Production) |

Use `--model <model-id>` to override the default in any gcop command.

## License

MIT
