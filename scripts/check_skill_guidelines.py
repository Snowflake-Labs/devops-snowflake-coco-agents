#!/usr/bin/env python3
"""Fast mechanical checks for CoCo scaffold skill guidelines.

Checks (no LLM, no network):
  - Coordinator SKILL.md files:  < 500 lines
  - Step files (steps/*.md):     < 200 lines
  - No inline SKILL_DIR bash block in step files
  - manifest_ops.py imports only stdlib modules

Exits 0 (all pass) or 1 (violations found).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCAFFOLD = Path(__file__).parent.parent / "skills" / "scaffold"

COORDINATOR_LIMIT = 500
STEP_LIMIT = 200

# Sentinel that must NOT appear in step files (indicates inlined SKILL_DIR block)
INLINE_SENTINEL = 'find ~/.snowflake/cortex/plugins -name "manifest_ops.py"'

STDLIB_MODULES = {
    "argparse",
    "contextlib",
    "datetime",
    "os",
    "pathlib",
    "re",
    "sys",
    "tomllib",
    "__future__",
}

violations: list[str] = []


def check_line_count(path: Path, limit: int) -> None:
    lines = path.read_text().count("\n")
    if lines > limit:
        violations.append(f"  {path.relative_to(SCAFFOLD)}: {lines} lines (limit {limit})")


def check_no_inline_skill_dir(path: Path) -> None:
    if INLINE_SENTINEL in path.read_text():
        violations.append(
            f"  {path.relative_to(SCAFFOLD)}: inline SKILL_DIR bash block found"
            f" — use 'Resolve per references/manifest.md' instead"
        )


def check_manifest_ops_imports(path: Path) -> None:
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or stripped.startswith("from ")):
            continue
        # Extract module name
        module = stripped.split()[1].split(".")[0]
        if module not in STDLIB_MODULES:
            violations.append(f"  {path.relative_to(SCAFFOLD)}: non-stdlib import '{module}'")


def main() -> int:
    if not SCAFFOLD.exists():
        print("skills/scaffold/ not found — skipping", file=sys.stderr)
        return 0

    # Coordinator SKILL.md files
    for p in SCAFFOLD.glob("*/SKILL.md"):
        check_line_count(p, COORDINATOR_LIMIT)

    # Step files
    for p in SCAFFOLD.glob("*/steps/*.md"):
        check_line_count(p, STEP_LIMIT)
        check_no_inline_skill_dir(p)

    # manifest_ops.py
    manifest_ops = SCAFFOLD / "scripts" / "manifest_ops.py"
    if manifest_ops.exists():
        check_manifest_ops_imports(manifest_ops)

    if violations:
        print("Skill guidelines violations:")
        for v in violations:
            print(v)
        return 1

    print("✓ Skill guidelines OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
