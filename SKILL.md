---
name: gemini
description: >
  Unified delegation interface for high-context tasks using Gemini 2.0/2.5. Triggers for long-form writing (proposals,
  blogs, content), documentation, planning, research, complex code analysis, code review, git diffs, reasoning,
  summarizing logs, generating code, codebase Q&A, and vision/screenshot audits.
---
# Gemini Unified Delegation
Claude acts as the manager/orchestrator; Gemini provides a 2M+ token window for high-capacity tasks. The `claude-gemini-bridge` automatically intercepts large reads or multi-file operations via the PreToolUse hook.
## Routing Table
| Task Type | Implementation Path | Preferred Model |
| :--- | :--- | :--- |
| Writing, Planning, Docs, Proposals | CONTENT (Offload) | pro |
| Code Analysis, Review, Refactoring | CODE (gcop analyze/generate) | pro |
| Git Diffs & Log Summarization | CODE (gcop diff/summarize) | flash |
| Architectural Reasoning & Logic | CODE (gcop reason) | pro |
| Codebase Q&A & Search | CODE (gcop ask) | pro |
| UI/UX Audits via Screenshots | CODE (gcop vision) | pro |
| Bulk File Operations | CODE (gcop bulk) | pro |
## Execution Guidelines
### CONTENT Path (Writing/Offload)
Use for structured text generation (blogs, documentation, proposals):
1. Prepare a detailed prompt and write it to `/tmp/gemini_task.txt`.
2. Define sections clearly: TASK, CONTEXT, OUTPUT FORMAT, CONSTRAINTS.
3. Execute: `bash ~/.claude/skills/gemini/scripts/try_gemini.sh /tmp/gemini_task.txt`
### CODE Path (Technical/Analysis)
Use for codebase-aware operations and technical reasoning:
1. Run: `bash ~/.claude/skills/gemini/scripts/run_gcop.sh <command> [args]`
2. Commands: `analyze`, `reason`, `summarize`, `diff`, `generate`, `ask`, `bulk`, `vision`, `cost`.
3. Use `--model flash` for speed/economy; `--model pro` for precision.
## Error Handling
- **GEMINI_SKIP:** Gemini CLI not found. Ensure `/opt/homebrew/bin` is in PATH or run `npm install -g @google/gemini-cli`.
- **GEMINI_FAILED:** API timeout or network error. Retry the operation exactly once.
- **JSON Output:** `gcop` returns JSON. Extract the `response` string for the final answer.
## Model Selection
- **Pro:** Default for complex logic, code generation, and vision.
- **Flash:** Efficient for summarization, simple diffs, and background analysis.
- **2.5-Pro:** Use when extreme reasoning depth is required.
