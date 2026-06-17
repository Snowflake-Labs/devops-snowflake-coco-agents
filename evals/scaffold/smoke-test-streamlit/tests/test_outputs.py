"""
Smoke tests for smoke-test-streamlit routing determinism.

Hybrid approach:
  - Trajectory checks (5): verify the agent went through the expected steps
  - Routing checks (4): read /app/scan-results.json for precise routing counts

The target outcome is deterministic routing across all 5 attempts:
  Issue 1 (validate_filters / assert)      → SEVERITY=low  → auto-fix
  Issue 2 (load_region_data / SQL f-string) → SEVERITY=high → needs-review
  Issue 3 (export_report / subprocess)     → SEVERITY=critical → needs-review
"""

import json
from pathlib import Path
import pytest

_TRAJECTORY_PATH = Path("/logs/agent/trajectory.json")
_RESULTS_PATH = Path("/app/scan-results.json")


# ── Trajectory helpers ────────────────────────────────────────────────────────

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


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def trajectory() -> dict:
    t = _load_trajectory()
    if not t:
        pytest.skip("No trajectory available")
    return t


@pytest.fixture
def full_text(trajectory) -> str:
    text = _collect_all_text(trajectory)
    assert text.strip(), "Trajectory exists but no text found"
    return text.lower()


@pytest.fixture
def scan_results() -> dict:
    assert _RESULTS_PATH.exists(), (
        f"Agent did not write {_RESULTS_PATH}. "
        "Step 3 of the instruction requires writing scan-results.json."
    )
    try:
        data = json.loads(_RESULTS_PATH.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"scan-results.json is not valid JSON: {e}")
    assert "findings" in data and isinstance(data["findings"], list), (
        "scan-results.json missing 'findings' list"
    )
    return data


# ── Trajectory checks: did the agent follow the steps? ────────────────────────

def test_agent_wrote_demo_app(full_text):
    """Agent must write the demo Python app with all three required functions."""
    assert all(fn in full_text for fn in ("get_default_filters", "load_region_data", "export_report")), (
        "Not all three required functions found in the trajectory. "
        "Expected get_default_filters, load_region_data, and export_report to be written."
    )


def test_agent_wrote_scan_results(full_text):
    """Agent must write scan-results.json (Step 3)."""
    assert "scan-results.json" in full_text, (
        "Agent did not appear to write scan-results.json. "
        "Step 3 requires writing routing results to /app/scan-results.json."
    )


def test_agent_found_pseudorandom_issue(full_text):
    """Agent must detect the pseudo-random non-security use (Issue 1 — auto-fix target)."""
    assert any(ind in full_text for ind in ("random", "s311", "pseudo-random", "randint", "pseudorandom")), (
        "Agent did not mention the pseudo-random/S311 usage in its response. "
        "get_default_filters uses random.randint() — expected S311 or pseudo-random mention."
    )


def test_agent_found_sql_injection(full_text):
    """Agent must detect the SQL f-string injection issue (Issue 2 — needs-review)."""
    assert any(ind in full_text for ind in ("sql injection", "f-string", "s608", "string interpolation")), (
        "Agent did not specifically mention SQL injection. "
        "load_region_data builds SQL via f-string — expected injection or S608 reference."
    )


def test_agent_found_subprocess_injection(full_text):
    """Agent must detect the subprocess shell injection issue (Issue 3 — needs-review)."""
    assert any(ind in full_text for ind in ("subprocess", "shell=true", "s602", "s605", "command injection")), (
        "Agent did not mention the subprocess/shell injection issue. "
        "export_report uses subprocess.run(..., shell=True) — expected subprocess or S60x."
    )


# ── Routing checks: did the agent route correctly? ───────────────────────────

def test_exactly_one_autofix(scan_results):
    """Exactly 1 finding should be auto-fix (the assert issue — low/low/high)."""
    count = scan_results.get("auto_fix", sum(1 for f in scan_results["findings"] if f.get("routing") == "auto-fix"))
    assert count == 1, (
        f"Expected exactly 1 auto-fix finding, got {count}. "
        f"Only the assert issue (SEVERITY=low, COMPLEXITY=low, CONFIDENCE=high) should auto-fix. "
        f"Findings: {json.dumps(scan_results['findings'], indent=2)}"
    )


def test_at_least_two_needs_review(scan_results):
    """At least 2 findings should be needs-review (SQL injection + subprocess)."""
    count = scan_results.get("needs_review", sum(1 for f in scan_results["findings"] if f.get("routing") == "needs-review"))
    assert count >= 2, (
        f"Expected >= 2 needs-review findings, got {count}. "
        "SQL injection (load_region_data) and subprocess (export_report) should both be needs-review."
    )


def test_pseudorandom_finding_is_autofix(scan_results):
    """The datetime.utcnow() deprecation finding must be routed auto-fix."""
    dep_findings = [
        f for f in scan_results["findings"]
        if any(kw in f.get("issue", "").lower() for kw in ("random", "s311", "pseudo-random", "randint"))
    ]
    assert dep_findings, (
        "No pseudo-random finding in scan-results.json. "
        "get_default_filters uses random.randint() — expected it to appear as a finding."
    )
    bad = [f for f in dep_findings if f.get("routing") != "auto-fix"]
    assert not bad, (
        f"Deprecation finding(s) were not routed to auto-fix: "
        f"{[(f.get('function'), f.get('severity'), f.get('routing')) for f in bad]}. "
        "random.randint() non-security use should score SEVERITY=low → auto-fix."
    )


def test_subprocess_and_sql_are_needs_review(scan_results):
    """SQL injection and subprocess findings must both be needs-review."""
    findings = scan_results["findings"]

    sql_findings = [
        f for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("sql", "inject", "f-string", "string"))
        or f.get("function", "").lower() == "load_region_data"
    ]
    subprocess_findings = [
        f for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("subprocess", "shell", "command"))
        or f.get("function", "").lower() == "export_report"
    ]

    assert sql_findings, (
        "No SQL injection finding in scan-results.json. "
        "load_region_data builds SQL via f-string — expected it to appear as a finding."
    )
    assert subprocess_findings, (
        "No subprocess finding in scan-results.json. "
        "export_report uses subprocess.run(shell=True) — expected it to appear as a finding."
    )

    bad_sql = [f for f in sql_findings if f.get("routing") != "needs-review"]
    bad_sub = [f for f in subprocess_findings if f.get("routing") != "needs-review"]

    assert not bad_sql, (
        f"SQL injection finding(s) not routed to needs-review: "
        f"{[(f.get('function'), f.get('severity'), f.get('routing')) for f in bad_sql]}"
    )
    assert not bad_sub, (
        f"Subprocess finding(s) not routed to needs-review: "
        f"{[(f.get('function'), f.get('severity'), f.get('routing')) for f in bad_sub]}"
    )
