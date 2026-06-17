"""
Trajectory-based tests for smoke-test-streamlit routing determinism.

Inspects the agent trajectory to verify the demo generation + scan produced:
  - A Python app was written
  - Security scan was performed
  - All 3 issue types were detected (assert, SQL injection, subprocess)
  - assert issue was routed to auto-fix
  - SQL injection and subprocess were routed to needs-review
"""

import json
from pathlib import Path
import pytest

_TRAJECTORY_PATH = Path("/logs/agent/trajectory.json")


def _load_trajectory():
    if not _TRAJECTORY_PATH.exists():
        return None
    try:
        return json.loads(_TRAJECTORY_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _collect_assistant_text(trajectory: dict) -> str:
    chunks = []
    for step in trajectory.get("steps", []):
        if step.get("source") != "agent":
            continue
        for field in ("assistant_response", "message", "final_response"):
            v = step.get(field, "")
            if isinstance(v, str) and v.strip():
                chunks.append(v)
    return "\n".join(chunks)


def _collect_all_text(trajectory: dict) -> str:
    chunks = []
    for step in trajectory.get("steps", []):
        for field in ("assistant_response", "message", "final_response"):
            v = step.get(field, "")
            if isinstance(v, str) and v.strip():
                chunks.append(v)
        for tc in step.get("tool_calls", []):
            for field in ("input", "output", "result", "arguments"):
                v = tc.get(field, "")
                if isinstance(v, str) and v.strip():
                    chunks.append(v)
                elif isinstance(v, dict):
                    chunks.append(json.dumps(v))
            fn = tc.get("function_name", "")
            if fn:
                chunks.append(fn)
    return "\n".join(chunks)

pytest_plugins = ["cortex_code_eval.eval_container_tools.conftest"]


@pytest.fixture
def trajectory() -> dict:
    t = _load_trajectory()
    if not t:
        pytest.skip("No trajectory available")
    return t


@pytest.fixture
def assistant_text(trajectory) -> str:
    text = _collect_assistant_text(trajectory)
    assert text.strip(), "Trajectory exists but no assistant response text found"
    return text.lower()


@pytest.fixture
def full_text(trajectory) -> str:
    text = _collect_all_text(trajectory)
    assert text.strip(), "Trajectory exists but no text found"
    return text.lower()


def test_agent_wrote_python_file(full_text):
    """Agent must write a Python file for the demo app."""
    file_indicators = [
        "demo/app.py",
        "app.py",
        "validate_filters",
        "load_region_data",
        "export_report",
    ]
    assert any(ind in full_text for ind in file_indicators), (
        "Agent did not appear to write the demo Python file. "
        "Expected to see demo/app.py or the required function names in the trajectory."
    )


def test_agent_scanned_code(full_text):
    """Agent must read/scan the demo code for security issues."""
    scan_indicators = [
        "scan",
        "severity",
        "security",
        "bandit",
        "issue",
        "finding",
    ]
    assert any(ind in full_text for ind in scan_indicators), (
        "Agent did not appear to scan the code for security issues. "
        "Expected scan-related terminology in the trajectory."
    )


def test_agent_found_assert_issue(full_text):
    """Agent must detect the assert-based validation issue (Issue 1)."""
    assert_indicators = [
        "assert",
        "s101",
        "assert statement",
        "assertion",
    ]
    assert any(ind in full_text for ind in assert_indicators), (
        "Agent did not mention the assert-based issue. "
        "Expected 'assert' or 'S101' in trajectory — this is Issue 1 (auto-fix target)."
    )


def test_agent_found_sql_injection(full_text):
    """Agent must detect the SQL injection issue (Issue 2)."""
    sql_indicators = [
        "sql injection",
        "sql",
        "f-string",
        "f\"select",
        "load_region_data",
        "injection",
        "s608",
    ]
    assert any(ind in full_text for ind in sql_indicators), (
        "Agent did not mention the SQL injection issue. "
        "Expected SQL injection indicators in trajectory — this is Issue 2 (needs-review)."
    )


def test_agent_found_subprocess_injection(full_text):
    """Agent must detect the subprocess shell injection issue (Issue 3)."""
    subprocess_indicators = [
        "subprocess",
        "shell=true",
        "shell injection",
        "command injection",
        "export_report",
        "s602",
        "s605",
        "s607",
    ]
    assert any(ind in full_text for ind in subprocess_indicators), (
        "Agent did not mention the subprocess/shell injection issue. "
        "Expected subprocess indicators in trajectory — this is Issue 3 (needs-review)."
    )


def test_agent_applied_autofix_routing(assistant_text):
    """Agent must route at least one issue to auto-fix in its response."""
    autofix_indicators = [
        "auto-fix",
        "auto_fix",
        "auto fix",
        "autofix",
    ]
    assert any(ind in assistant_text for ind in autofix_indicators), (
        "Agent did not mention auto-fix routing in its response. "
        "The assert issue (S101/low severity) should be routed to auto-fix."
    )


def test_agent_applied_needs_review_routing(assistant_text):
    """Agent must route at least one issue to needs-review in its response."""
    review_indicators = [
        "needs-review",
        "needs_review",
        "needs review",
        "needsreview",
    ]
    assert any(ind in assistant_text for ind in review_indicators), (
        "Agent did not mention needs-review routing in its response. "
        "SQL injection and subprocess issues should be routed to needs-review."
    )
