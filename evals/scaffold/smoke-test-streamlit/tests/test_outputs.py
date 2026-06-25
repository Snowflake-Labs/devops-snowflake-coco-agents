"""
Determinism verifier for smoke-test-streamlit: Streamlit dashboard demo generation + scan.

Validates that the agent deterministically produces:
  - demo/app.py with exactly 3 functions using specific vulnerability patterns
  - scan-results.json with correct routing (1 auto-fix + 2 needs-review)
  - /app/issues/ with issue files matching production scan.md format
"""

import json
from pathlib import Path

import pytest

DEMO_APP = Path("/workspace/demo/app.py")
DEMO_TOML = Path("/workspace/demo/pyproject.toml")
SCAN_RESULTS = Path("/app/scan-results.json")
ISSUES_DIR = Path("/app/issues")


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def app_content() -> str:
    assert DEMO_APP.exists(), f"{DEMO_APP} does not exist"
    return DEMO_APP.read_text().lower()


@pytest.fixture
def scan_results() -> dict:
    assert SCAN_RESULTS.exists(), f"{SCAN_RESULTS} does not exist"
    data = json.loads(SCAN_RESULTS.read_text())
    assert "findings" in data and isinstance(data["findings"], list), (
        "scan-results.json missing 'findings' list"
    )
    return data


@pytest.fixture
def issue_files() -> list[dict]:
    assert ISSUES_DIR.exists(), f"{ISSUES_DIR} does not exist"
    files = sorted(ISSUES_DIR.glob("*.json"))
    assert len(files) > 0, "No .json issue files in /app/issues/"
    issues = []
    for f in files:
        issues.append(json.loads(f.read_text()))
    return issues


# ── Demo app structure ──────────────────────────────────────────────────────


def test_demo_app_exists():
    assert DEMO_APP.exists()


def test_demo_pyproject_exists():
    assert DEMO_TOML.exists()


def test_app_has_get_default_filters(app_content):
    assert "get_default_filters" in app_content


def test_app_has_load_region_data(app_content):
    assert "load_region_data" in app_content


def test_app_has_export_report(app_content):
    assert "export_report" in app_content


def test_app_uses_random(app_content):
    assert "random" in app_content


def test_app_uses_subprocess(app_content):
    assert "subprocess" in app_content


# ── Scan results routing ────────────────────────────────────────────────────


def test_exactly_one_autofix(scan_results):
    auto_fix = [f for f in scan_results["findings"] if f.get("routing") == "auto-fix"]
    assert len(auto_fix) == 1, f"Expected 1 auto-fix, got {len(auto_fix)}"


def test_at_least_two_needs_review(scan_results):
    needs_review = [f for f in scan_results["findings"] if f.get("routing") == "needs-review"]
    assert len(needs_review) >= 2, f"Expected >= 2 needs-review, got {len(needs_review)}"


def test_random_finding_is_autofix(scan_results):
    findings = scan_results["findings"]
    random_findings = [
        f
        for f in findings
        if any(
            kw in f.get("issue", "").lower()
            for kw in ("random", "s311", "pseudo-random", "randint")
        )
        or f.get("function", "").lower() == "get_default_filters"
    ]
    assert random_findings, "No pseudo-random finding for get_default_filters"
    bad = [f for f in random_findings if f.get("routing") != "auto-fix"]
    assert not bad, f"Pseudo-random finding routed to '{bad[0].get('routing')}', expected auto-fix"


def test_random_finding_severity_low(scan_results):
    findings = scan_results["findings"]
    random_findings = [
        f
        for f in findings
        if any(
            kw in f.get("issue", "").lower()
            for kw in ("random", "s311", "pseudo-random", "randint")
        )
        or f.get("function", "").lower() == "get_default_filters"
    ]
    assert random_findings, "No pseudo-random finding for get_default_filters"
    for f in random_findings:
        assert f.get("severity") == "low", (
            f"Pseudo-random finding severity should be 'low', got '{f.get('severity')}'"
        )


def test_sql_injection_is_needs_review(scan_results):
    findings = scan_results["findings"]
    sql_findings = [
        f
        for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("sql", "inject", "f-string"))
        or f.get("function", "").lower() == "load_region_data"
    ]
    assert sql_findings, "No SQL injection finding for load_region_data"
    bad = [f for f in sql_findings if f.get("routing") != "needs-review"]
    assert not bad, f"SQL injection routed to '{bad[0].get('routing')}', expected needs-review"


def test_sql_injection_severity_high_or_critical(scan_results):
    findings = scan_results["findings"]
    sql_findings = [
        f
        for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("sql", "inject", "f-string"))
        or f.get("function", "").lower() == "load_region_data"
    ]
    assert sql_findings, "No SQL injection finding for load_region_data"
    for f in sql_findings:
        assert f.get("severity") in ("high", "critical"), (
            f"SQL injection severity should be 'high' or 'critical', got '{f.get('severity')}'"
        )


def test_subprocess_is_needs_review(scan_results):
    findings = scan_results["findings"]
    sub_findings = [
        f
        for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("subprocess", "shell", "command"))
        or f.get("function", "").lower() == "export_report"
    ]
    assert sub_findings, "No subprocess finding for export_report"
    bad = [f for f in sub_findings if f.get("routing") != "needs-review"]
    assert not bad, f"Subprocess routed to '{bad[0].get('routing')}', expected needs-review"


def test_subprocess_severity_high_or_critical(scan_results):
    findings = scan_results["findings"]
    sub_findings = [
        f
        for f in findings
        if any(kw in f.get("issue", "").lower() for kw in ("subprocess", "shell", "command"))
        or f.get("function", "").lower() == "export_report"
    ]
    assert sub_findings, "No subprocess finding for export_report"
    for f in sub_findings:
        assert f.get("severity") in ("high", "critical"), (
            f"Subprocess severity should be 'high' or 'critical', got '{f.get('severity')}'"
        )


# ── Issue files: production format ──────────────────────────────────────────


def test_issue_count_matches_findings(scan_results, issue_files):
    assert len(issue_files) >= len(scan_results["findings"]), (
        f"Expected {len(scan_results['findings'])} issue files, found {len(issue_files)}"
    )


def test_autofix_issue_has_coco_agent_prefix(issue_files):
    autofix = [i for i in issue_files if "coco:auto-fix" in i.get("labels", [])]
    assert len(autofix) >= 1, "No issue with 'coco:auto-fix' label"
    for issue in autofix:
        assert issue["title"].startswith("[coco-agent]"), (
            f"Auto-fix title must start with '[coco-agent]', got: {issue['title']}"
        )


def test_needs_review_issue_no_prefix(issue_files):
    needs_review = [i for i in issue_files if "coco:needs-review" in i.get("labels", [])]
    assert len(needs_review) >= 2, f"Expected >= 2 needs-review issues, got {len(needs_review)}"
    for issue in needs_review:
        assert not issue["title"].startswith("[coco-agent]"), (
            f"Needs-review title must NOT start with '[coco-agent]', got: {issue['title']}"
        )
        assert issue["title"].startswith("Bug:"), (
            f"Needs-review title must start with 'Bug:', got: {issue['title']}"
        )


def test_autofix_issue_has_coco_agent_label(issue_files):
    autofix = [i for i in issue_files if "coco:auto-fix" in i.get("labels", [])]
    for issue in autofix:
        assert "coco-agent" in issue["labels"], (
            f"Auto-fix issue missing 'coco-agent' label: {issue['labels']}"
        )
        assert "coco-agent-security" in issue["labels"], (
            f"Auto-fix issue missing 'coco-agent-security' label: {issue['labels']}"
        )


def test_needs_review_issue_has_security_label(issue_files):
    needs_review = [i for i in issue_files if "coco:needs-review" in i.get("labels", [])]
    for issue in needs_review:
        assert "coco-agent-security" in issue["labels"], (
            f"Needs-review issue missing 'coco-agent-security' label: {issue['labels']}"
        )


def test_issue_body_has_structured_format(issue_files):
    for i, issue in enumerate(issue_files):
        body = issue.get("body", "")
        assert "Code:" in body, f"issue-{i + 1}.json body missing 'Code:' section"
        assert "Problem:" in body, f"issue-{i + 1}.json body missing 'Problem:' section"
        assert "Expected:" in body, f"issue-{i + 1}.json body missing 'Expected:' section"


def test_issue_body_has_severity_footer(issue_files):
    for i, issue in enumerate(issue_files):
        body = issue.get("body", "")
        assert "Severity:" in body, f"issue-{i + 1}.json body missing severity footer"
        assert "Complexity:" in body, f"issue-{i + 1}.json body missing complexity in footer"
        assert "Confidence:" in body, f"issue-{i + 1}.json body missing confidence in footer"
        assert "Fix mode:" in body, f"issue-{i + 1}.json body missing fix mode in footer"


def test_needs_review_body_has_coco_fix_hint(issue_files):
    needs_review = [i for i in issue_files if "coco:needs-review" in i.get("labels", [])]
    for issue in needs_review:
        assert "/coco fix" in issue.get("body", ""), (
            f"Needs-review issue body missing '/coco fix' trigger hint"
        )
