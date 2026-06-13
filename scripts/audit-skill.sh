#!/usr/bin/env bash
# Delegates scaffold skill audit to the CoCo bundled skill-development skill.
# Skips gracefully when cortex is not on PATH (CI without CoCo, other contributors).
set -euo pipefail

if ! cortex exec --help > /dev/null 2>&1; then
  echo "cortex not on PATH — skipping LLM skill audit"
  exit 0
fi

OUTPUT=$(cortex exec \
  "Run a skill-development audit on the scaffold skills in skills/scaffold/. \
Check: coordinator SKILL.md files use plan mode correctly, step files use \
ask_user_question for all user interactions, no sensitive values are echoed, \
references/manifest.md is the canonical source for shared content (not inlined \
in step files). Report each violation clearly. \
End your response with exactly one of: SKILL_AUDIT_PASS or SKILL_AUDIT_FAIL" \
  --bypass --no-history --allowed "Read" 2>&1)

echo "$OUTPUT"

if grep -q "SKILL_AUDIT_PASS" <<< "$OUTPUT"; then
  exit 0
else
  echo ""
  echo "Skill audit found violations — fix before committing."
  exit 1
fi
