#!/usr/bin/env bash
# PermissionRequest hook: auto-approve read-only tools to reduce dialog noise.
# Stdin: full hook context JSON with tool_name field.
# Returns allow for safe read-only ops; ask for everything else.

input=$(cat)
tool=$(echo "$input" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except Exception:
    print('')
" 2>/dev/null)

case "$tool" in
    read|grep|glob|tgrep)
        echo '{"hookSpecificOutput":{"permissionDecision":"allow"}}'
        ;;
    *)
        echo '{"hookSpecificOutput":{"permissionDecision":"ask"}}'
        ;;
esac
