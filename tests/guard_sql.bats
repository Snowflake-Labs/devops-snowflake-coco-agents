#!/usr/bin/env bats
# Tests for .cortex/hooks/guard-sql.sh

setup() {
  HOOK="$BATS_TEST_DIRNAME/../.cortex/hooks/guard-sql.sh"
}

# --- Blocked: bare dangerous DDL ---

@test "blocks bare DROP USER" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER admin"}}'
  [ "$status" -eq 2 ]
}

@test "blocks bare DROP ROLE" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP ROLE SYSADMIN"}}'
  [ "$status" -eq 2 ]
}

@test "blocks bare DROP WAREHOUSE" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP WAREHOUSE compute_wh"}}'
  [ "$status" -eq 2 ]
}

@test "blocks case-insensitive drop user" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"drop user Admin"}}'
  [ "$status" -eq 2 ]
}

# --- Blocked: comment bypass ---

@test "blocks IDENTIFIER hidden in inline comment" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER foo -- IDENTIFIER($bar)"}}'
  [ "$status" -eq 2 ]
}

@test "blocks IDENTIFIER hidden in block comment" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER x /* IDENTIFIER($y) */"}}'
  [ "$status" -eq 2 ]
}

@test "blocks COCO_AGENT hidden in block comment" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER x /* _COCO_AGENT_ */"}}'
  [ "$status" -eq 2 ]
}

# --- Blocked: newline split ---

@test "blocks newline between DROP and USER" {
  input=$(printf '{"tool_input":{"sql":"DROP\\nUSER admin"}}')
  run bash "$HOOK" <<< "$input"
  [ "$status" -eq 2 ]
}

@test "blocks multi-newline DROP ROLE" {
  input=$(printf '{"tool_input":{"sql":"DROP\\n  ROLE\\n  SYSADMIN"}}')
  run bash "$HOOK" <<< "$input"
  [ "$status" -eq 2 ]
}

# --- Allowed: legitimate teardown (IDENTIFIER parameterised) ---

@test "allows DROP USER IDENTIFIER with session var" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER IDENTIFIER($SF_USER)"}}'
  [ "$status" -eq 0 ]
}

@test "allows DROP ROLE IDENTIFIER with session var" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP ROLE IDENTIFIER($COCO_ROLE)"}}'
  [ "$status" -eq 0 ]
}

@test "allows DROP WAREHOUSE IDENTIFIER with session var" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP WAREHOUSE IDENTIFIER($SF_WH)"}}'
  [ "$status" -eq 0 ]
}

# --- Allowed: COCO_AGENT naming marker ---

@test "allows DROP USER with COCO_AGENT marker" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP USER MY_COCO_AGENT_USER"}}'
  [ "$status" -eq 0 ]
}

@test "allows DROP ROLE with COCO_AGENT marker" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP ROLE ETL_COCO_AGENT_ROLE"}}'
  [ "$status" -eq 0 ]
}

# --- Allowed: harmless SQL ---

@test "allows SELECT" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"SELECT 1"}}'
  [ "$status" -eq 0 ]
}

@test "allows CREATE TABLE" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"CREATE TABLE foo (id INT)"}}'
  [ "$status" -eq 0 ]
}

@test "allows SHOW WAREHOUSES" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"SHOW WAREHOUSES"}}'
  [ "$status" -eq 0 ]
}

@test "allows DROP TABLE (not guarded)" {
  run bash "$HOOK" <<< '{"tool_input":{"sql":"DROP TABLE temp_staging"}}'
  [ "$status" -eq 0 ]
}
