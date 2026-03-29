"""Gemini CLI client for Claude Code delegation.

Uses the `gemini` CLI subprocess instead of google-genai SDK.
All function signatures preserved for backward compatibility.
"""
from __future__ import annotations
import subprocess
import os
import sys
import time
import shutil
from pathlib import Path

try:
    from . import cache, cost
except ImportError:
    try:
        from lib import cache, cost
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from lib import cache, cost

# Model aliases — same as original for compatibility
MODELS = {
    "pro": "gemini-3.1-pro-preview",
    "flash": "gemini-2.5-flash",
    "flash-preview": "gemini-2.5-flash-preview",
    "2.5-pro": "gemini-2.5-pro",
}
DEFAULT_MODEL = "flash"

# Kept for compatibility — thinking tiers are accepted but not applied via CLI
THINKING_TIERS = {
    "low":    {"flash": 1024,  "pro": 2048},
    "medium": {"flash": 4096,  "pro": 8192},
    "high":   {"flash": 8192,  "pro": 16384},
    "max":    {"flash": 16384, "pro": 32768},
}
DEFAULT_TIER = "high"

NAKED_REASONER_INSTRUCTION = (
    "You are the naked reasoning engine. Focus entirely on logical deduction, "
    "structural mapping, and first-principles problem solving. Cross disciplinary "
    "boundaries if required. Do not output tool-calling boilerplate. Do not write "
    "execution code unless explicitly asked. Return the logical proof, architectural "
    "resolution, or analytical framework."
)

# NVM node versions to check (newest first)
_NVM_NODE_VERSIONS = ["v24.13.0", "v22.21.0", "v20.18.2"]

# Noise patterns from the gemini CLI to strip
_NOISE_PREFIXES = [
    "MCP issues detected.",
    "Loaded cached credentials.",
    "Loading extension:",
    "[MCP",
    "Server '",
    "MCP context refresh",
    "Coalescing burst",
    "Executing MCP context",
]


def _find_gemini_bin() -> tuple[str | None, str | None]:
    """Find gemini binary and the node binary needed to run it.

    Returns (gemini_path, node_path) or (None, None) if not found.
    """
    home = Path.home()

    # Check nvm paths first (most common on macOS dev machines)
    for version in _NVM_NODE_VERSIONS:
        nvm_bin = home / ".nvm" / "versions" / "node" / version / "bin"
        gemini = nvm_bin / "gemini"
        node = nvm_bin / "node"
        if gemini.exists() and node.exists():
            return str(gemini), str(nvm_bin)

    # Check common static paths
    for candidate in [
        "/opt/homebrew/bin/gemini",
        "/usr/local/bin/gemini",
        str(home / ".npm-global" / "bin" / "gemini"),
        str(home / ".local" / "bin" / "gemini"),
    ]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate, None

    # Fallback: shutil.which with current PATH
    found = shutil.which("gemini")
    if found:
        return found, None

    return None, None


def _build_env(node_bin_dir: str | None) -> dict:
    """Build subprocess env with node in PATH."""
    env = os.environ.copy()
    if node_bin_dir:
        env["PATH"] = node_bin_dir + os.pathsep + env.get("PATH", "")
    return env


def _strip_noise(text: str) -> str:
    """Remove gemini CLI status lines from output."""
    if not text:
        return ""
    clean = []
    for line in text.splitlines():
        stripped = line.strip()
        if not any(stripped.startswith(p) for p in _NOISE_PREFIXES):
            clean.append(line)
    return "\n".join(clean).strip()


def _resolve_model(model: str) -> str:
    return MODELS.get(model, model)


def route_model(task: str, content_size: int = 0, focus: str = "") -> str:
    """Auto-select model based on task type, content size, and focus area."""
    combined = f"{task} {focus}".lower()
    pro_signals = [
        "architect", "security", "threat", "design", "review", "debug",
        "complex", "vulnerability", "reason", "proof", "diff", "vision",
        "concurrent", "crypto", "fraud", "compliance",
    ]
    if any(s in combined for s in pro_signals):
        return "pro"
    if content_size > 500_000:
        return "pro"
    return "flash"


def generate(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system_instruction: str = "",
    files: list[str] | None = None,
    images: list[str] | None = None,
    temperature: float = 0.3,
    max_tokens: int = 16384,
    json_mode: bool = True,
    use_cache: bool = True,
    task_label: str = "",
    think: bool = True,
    tier: str | None = None,
    thinking_budget: int | None = None,
) -> dict:
    """Call Gemini via CLI subprocess. Same signature as original SDK-based client."""
    resolved_model = _resolve_model(model)

    # Budget check
    within_budget, spent, limit = cost.check_budget()
    if not within_budget:
        return {
            "status": "error",
            "error": f"Daily budget exceeded: ${spent:.2f} / ${limit:.2f}",
            "model": resolved_model,
        }

    # Find gemini binary
    gemini_bin, node_bin_dir = _find_gemini_bin()
    if not gemini_bin:
        return {
            "status": "error",
            "error": "GEMINI_SKIP: gemini CLI not installed. Run: npm install -g @google/gemini-cli",
            "model": resolved_model,
        }

    # Build full prompt (embed system instruction + file contents inline)
    parts = []
    if system_instruction:
        parts.append(f"[SYSTEM INSTRUCTION]\n{system_instruction}\n[END SYSTEM INSTRUCTION]\n")

    if files:
        for fpath in files:
            p = Path(fpath)
            if p.exists() and p.is_file():
                try:
                    text = p.read_text(errors="replace")
                    parts.append(f"--- File: {fpath} ---\n{text}\n--- End: {fpath} ---")
                except Exception as e:
                    parts.append(f"--- File: {fpath} (error reading: {e}) ---")

    if images:
        for img in images:
            parts.append(f"[Image: {img} — vision not supported via CLI; describe from filename/context]")

    parts.append(prompt)
    if json_mode:
        parts.append("\nRespond with valid JSON only. No markdown fences.")

    full_prompt = "\n\n".join(parts)

    # Cache lookup (use same cache.get/put API as original)
    if use_cache and not images:
        cached = cache.get(resolved_model, full_prompt, files,
                           system_instruction=system_instruction)
        if cached:
            cached["cached"] = True
            cached["status"] = "ok"
            return cached

    # Call gemini CLI with retry
    env = _build_env(node_bin_dir)
    cmd = [gemini_bin, "--model", resolved_model, "-p", full_prompt]
    start = time.time()
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                env=env,
                timeout=120,
            )
            response_text = _strip_noise(result.stdout)

            if result.returncode == 0 and response_text:
                break
            else:
                last_error = f"exit {result.returncode}: {result.stderr.strip()[:200]}"
                if not response_text:
                    last_error = "empty output"
        except subprocess.TimeoutExpired:
            last_error = "timeout after 120s"
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            time.sleep(1 * (2 ** attempt))
    else:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "error",
            "error": f"Gemini CLI failed after {max_retries} attempts: {last_error}",
            "model": resolved_model,
            "latency_ms": latency_ms,
        }

    latency_ms = int((time.time() - start) * 1000)

    # Estimate tokens (4 chars ≈ 1 token)
    input_tokens = len(full_prompt) // 4
    output_tokens = len(response_text) // 4

    cost_usd = cost.estimate_cost(resolved_model, input_tokens, output_tokens)
    cost.log_usage(resolved_model, input_tokens, output_tokens, cost_usd, task_label)

    # Try to parse JSON if requested
    parsed = None
    if json_mode:
        clean = response_text.strip()
        for fence in ["```json", "```"]:
            if clean.startswith(fence):
                clean = clean[len(fence):]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            import json
            parsed = json.loads(clean)
        except Exception:
            try:
                import json
                parsed = json.loads(response_text)
            except Exception:
                parsed = None

    result_dict = {
        "status": "ok",
        "response": parsed if parsed is not None else response_text,
        "raw_text": response_text if parsed is not None else None,
        "model": resolved_model,
        "thinking": False,
        "thinking_tokens": 0,
        "thinking_text": None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
        "latency_ms": latency_ms,
        "cached": False,
    }

    # Cache the result
    if use_cache and not images:
        cache.put(resolved_model, full_prompt, result_dict, files,
                  system_instruction=system_instruction)

    return result_dict


def _detect_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".pdf": "application/pdf",
    }.get(suffix, "application/octet-stream")
