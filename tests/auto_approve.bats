#!/usr/bin/env bats
# Tests for .cortex/hooks/auto-approve.sh

setup() {
  HOOK="$BATS_TEST_DIRNAME/../.cortex/hooks/auto-approve.sh"
}

get_decision() {
  local output
  output=$(bash "$HOOK" <<< "$1" 2>/dev/null) || true
  echo "$output" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('hookSpecificOutput', {}).get('permissionDecision', ''))
except Exception:
    print('')
"
}

# --- Auto-approved (read-only tools) ---

@test "auto-approves read tool" {
  result=$(get_decision '{"tool_name":"read"}')
  [ "$result" = "allow" ]
}

@test "auto-approves grep tool" {
  result=$(get_decision '{"tool_name":"grep"}')
  [ "$result" = "allow" ]
}

@test "auto-approves glob tool" {
  result=$(get_decision '{"tool_name":"glob"}')
  [ "$result" = "allow" ]
}

@test "auto-approves tgrep tool" {
  result=$(get_decision '{"tool_name":"tgrep"}')
  [ "$result" = "allow" ]
}

# --- Requires user approval (write/execute tools) ---

@test "asks for write tool" {
  result=$(get_decision '{"tool_name":"write"}')
  [ "$result" = "ask" ]
}

@test "asks for edit tool" {
  result=$(get_decision '{"tool_name":"edit"}')
  [ "$result" = "ask" ]
}

@test "asks for bash tool" {
  result=$(get_decision '{"tool_name":"bash"}')
  [ "$result" = "ask" ]
}

@test "asks for sql_execute tool" {
  result=$(get_decision '{"tool_name":"sql_execute"}')
  [ "$result" = "ask" ]
}

@test "asks for empty tool name" {
  result=$(get_decision '{"tool_name":""}')
  [ "$result" = "ask" ]
}

@test "is case-sensitive: Read != read" {
  result=$(get_decision '{"tool_name":"Read"}')
  [ "$result" = "ask" ]
}

# --- Edge cases ---

@test "asks when tool_name key missing" {
  result=$(get_decision '{}')
  [ "$result" = "ask" ]
}

@test "asks on invalid JSON" {
  result=$(get_decision 'not json')
  [ "$result" = "ask" ]
}
