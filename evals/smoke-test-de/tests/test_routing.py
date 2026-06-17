"""
Tests for smoke-test routing determinism.

Verifies that the demo generation + scan produces:
  - Exactly 1 auto-fix finding (Issue 1: assert for validation, SEVERITY=low)
  - At least 2 needs-review findings (Issue 2: SQL injection, Issue 3: subprocess)
  - The auto-fix finding scores LOW severity
  - SQL injection and subprocess injection are present
"""

import json
from pathlib import Path

import pytest

RESULTS_PATH = Path("/app/scan-results.json")
APP_PATH = Path("/app/demo/app.py")


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_results() -> dict:
    assert RESULTS_PATH.exists(), (
        f"scan-results.json not written to {RESULTS_PATH}. "
        "Agent may have failed to complete Step 3."
    )
    try:
        return json.loads(RESULTS_PATH.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"scan-results.json is not valid JSON: {e}")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def results() -> dict:
    return load_results()


@pytest.fixture(scope="module")
def findings(results) -> list:
    return results.get("findings", [])


@pytest.fixture(scope="module")
def auto_fix_findings(findings) -> list:
    return [f for f in findings if f.get("routing") == "auto-fix"]


@pytest.fixture(scope="module")
def needs_review_findings(findings) -> list:
    return [f for f in findings if f.get("routing") == "needs-review"]


# ── File presence ──────────────────────────────────────────────────────────────

def test_demo_app_written():
    """Agent wrote demo/app.py."""
    assert APP_PATH.exists(), "demo/app.py was not written"


def test_scan_results_written():
    """Agent wrote scan-results.json."""
    assert RESULTS_PATH.exists(), "scan-results.json was not written"


def test_results_schema(results):
    """scan-results.json has the required keys."""
    for key in ("total", "auto_fix", "needs_review", "findings"):
        assert key in results, f"Missing key '{key}' in scan-results.json"
    assert isinstance(results["findings"], list), "'findings' must be a list"


# ── Routing counts ─────────────────────────────────────────────────────────────

def test_exactly_one_autofix(results):
    """Exactly 1 finding should auto-fix (Issue 1: assert validation)."""
    assert results["auto_fix"] == 1, (
        f"Expected 1 auto-fix finding, got {results['auto_fix']}. "
        f"Findings: {json.dumps(results['findings'], indent=2)}"
    )


def test_at_least_two_needs_review(results):
    """At least 2 findings should be needs-review (SQL injection + subprocess)."""
    assert results["needs_review"] >= 2, (
        f"Expected >= 2 needs-review findings, got {results['needs_review']}"
    )


# ── Severity routing ───────────────────────────────────────────────────────────

def test_autofix_is_low_severity(auto_fix_findings):
    """The auto-fix finding must score SEVERITY=low (assert is a minor code issue)."""
    assert len(auto_fix_findings) >= 1, "No auto-fix findings found"
    bad = [f for f in auto_fix_findings if f.get("severity") != "low"]
    assert not bad, (
        f"Auto-fix finding(s) scored non-low severity: "
        f"{[f['severity'] for f in bad]}. "
        "Check that Issue 1 (assert validation) is placed correctly."
    )


def test_autofix_is_low_complexity(auto_fix_findings):
    """The auto-fix finding must score COMPLEXITY=low."""
    bad = [f for f in auto_fix_findings if f.get("complexity") != "low"]
    assert not bad, (
        f"Auto-fix finding(s) scored non-low complexity: "
        f"{[f['complexity'] for f in bad]}"
    )


def test_autofix_is_high_confidence(auto_fix_findings):
    """The auto-fix finding must score CONFIDENCE=high."""
    bad = [f for f in auto_fix_findings if f.get("confidence") != "high"]
    assert not bad, (
        f"Auto-fix finding(s) scored non-high confidence: "
        f"{[f['confidence'] for f in bad]}"
    )


# ── Issue presence ─────────────────────────────────────────────────────────────

def test_sql_injection_found(findings):
    """SQL injection (Issue 2) must be detected."""
    issues = [f.get("issue", "").lower() for f in findings]
    assert any("sql" in i or "inject" in i or "f-string" in i for i in issues), (
        f"No SQL injection finding detected. Issues found: {issues}"
    )


def test_subprocess_found(findings):
    """Subprocess shell injection (Issue 3) must be detected."""
    issues = [f.get("issue", "").lower() for f in findings]
    assert any(
        "subprocess" in i or "shell" in i or "command" in i or "injection" in i
        for i in issues
    ), f"No subprocess/command injection finding detected. Issues found: {issues}"


def test_assert_found(findings):
    """Assert validation issue (Issue 1) must be detected."""
    issues = [f.get("issue", "").lower() for f in findings]
    funcs = [f.get("function", "").lower() for f in findings]
    assert any(
        "assert" in i or "s101" in i or "assert" in func
        for i, func in zip(issues, funcs)
    ), f"No assert-related finding detected. Issues: {issues}"
