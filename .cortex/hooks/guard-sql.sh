#!/usr/bin/env bash
# PreToolUse hook: guard sql_execute against accidental drops outside COCO_AGENT objects.
#
# Allow conditions (any one is sufficient):
#   1. SQL contains _COCO_AGENT_ — objects created by this scaffold
#   2. SQL uses IDENTIFIER($var) — session-variable dereference (safe parameterised SQL)
# Block: DROP USER, DROP ROLE, DROP WAREHOUSE that don't match either condition.

input=$(cat)
sql=$(echo "$input" | python3 -c "
import sys, json, re
try:
    d = json.load(sys.stdin)
    raw = d.get('tool_input', {}).get('sql', '')
    # Strip SQL comments before safety checks to prevent bypass via
    # patterns hidden inside comments (e.g. DROP USER x -- IDENTIFIER(\$y))
    raw = re.sub(r'--[^\n]*', ' ', raw)
    raw = re.sub(r'/\*.*?\*/', ' ', raw, flags=re.DOTALL)
    raw = ' '.join(raw.split())  # collapse whitespace to prevent newline split bypass
    print(raw)
except Exception:
    print('')
" 2>/dev/null | tr '[:lower:]' '[:upper:]')

# Fail-closed: if SQL could not be parsed, block rather than allow
if [ -z "$sql" ]; then
  echo "guard-sql: could not parse SQL input — blocking as a precaution." >&2
  exit 2
fi

for pattern in "DROP USER" "DROP ROLE" "DROP WAREHOUSE"; do
    if echo "$sql" | grep -q "$pattern"; then
        # Allow: IDENTIFIER($var) session-variable dereference
        if echo "$sql" | grep -qE 'IDENTIFIER\(\$[A-Z_]+\)'; then
            exit 0
        fi
        # Allow: contains the COCO_AGENT naming marker
        if echo "$sql" | grep -q "_COCO_AGENT_"; then
            exit 0
        fi
        echo "Blocked: '$pattern' outside COCO_AGENT objects. Use the scaffold teardown step." >&2
        exit 2
    fi
done

exit 0
