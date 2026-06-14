#!/usr/bin/env bash
# PreToolUse hook: guard sql_execute against accidental drops outside COCO_AGENT objects.
#
# Allow conditions (any one is sufficient):
#   1. SQL contains _COCO_AGENT_ — objects created by this scaffold
#   2. SQL uses IDENTIFIER($var) — session-variable dereference (safe parameterised SQL)
# Block: DROP USER, DROP ROLE, DROP WAREHOUSE that don't match either condition.

input=$(cat)
sql=$(echo "$input" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('sql', ''))
except Exception:
    print('')
" 2>/dev/null | tr '[:lower:]' '[:upper:]')

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
