from __future__ import annotations

import json
import re
from pathlib import Path

TRAJECTORY_PATH = Path("/logs/agent/trajectory.json")


def load_trajectory() -> dict | None:
    """Load the agent trajectory JSON if present."""
    if not TRAJECTORY_PATH.exists():
        return None
    try:
        return json.loads(TRAJECTORY_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def collect_assistant_text(trajectory: dict) -> str:
    """Collect assistant-authored text from trajectory steps."""
    chunks: list[str] = []
    for step in trajectory.get("steps", []):
        if step.get("source") != "agent":
            continue
        for field in ("assistant_response", "message", "final_response"):
            value = step.get(field, "")
            if isinstance(value, str) and value.strip():
                chunks.append(value)
    return "\n".join(chunks)


def collect_all_text(trajectory: dict) -> str:
    """Collect all text from trajectory (assistant + tool calls/results)."""
    chunks: list[str] = []
    for step in trajectory.get("steps", []):
        for field in ("assistant_response", "message", "final_response"):
            value = step.get(field, "")
            if isinstance(value, str) and value.strip():
                chunks.append(value)
        for tc in step.get("tool_calls", []):
            for field in ("input", "output", "result", "arguments"):
                value = tc.get(field, "")
                if isinstance(value, str) and value.strip():
                    chunks.append(value)
                elif isinstance(value, dict):
                    chunks.append(json.dumps(value))
            fn = tc.get("function_name", "")
            if fn:
                chunks.append(fn)
    return "\n".join(chunks)


def strip_markdown(text: str) -> str:
    """Remove markdown formatting for cleaner text matching."""
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text
