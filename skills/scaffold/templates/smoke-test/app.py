"""CoCo Agent Demo App
-------------------
A minimal Snowflake utility with intentional issues for the coco-agent scan/fix demo.
The agent will scan this file, raise issues, and open a fix PR automatically.

Issues are designed to exercise all three smart-fix routing paths:
  Issue 1 (LOW  severity) → auto-fix under conservative ceiling
  Issue 2 (MED  severity) → needs-review under conservative, auto-fix under aggressive
  Issue 3 (HIGH severity) → needs-review under both ceilings
"""

from __future__ import annotations

import logging
import os

import snowflake.connector

_LOG = logging.getLogger(__name__)

# Issue 1: hardcoded schema — should come from an environment variable or config
SCHEMA = "PUBLIC"


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Return a Snowflake connection using SSO/OIDC authentication."""
    account = os.environ["SNOWFLAKE_ACCOUNT"]
    user = os.environ["SNOWFLAKE_USER"]
    # Issue 2: sensitive connection details written to debug log — info disclosure
    # Severity: medium | Complexity: low | Confidence: high
    _LOG.debug("Opening connection: account=%s user=%s", account, user)
    return snowflake.connector.connect(
        account=account,
        user=user,
        authenticator="externalbrowser",
        schema=SCHEMA,
    )


def query_table(conn: snowflake.connector.SnowflakeConnection, table_name: str) -> list:
    """Fetch the first 10 rows from the given table."""
    cur = conn.cursor()
    # Issue 3: SQL injection — table_name is interpolated directly into the query.
    # Use an allowlist or a quoted identifier instead.
    # Severity: high | Complexity: medium | Confidence: medium
    cur.execute(f"SELECT * FROM {table_name} LIMIT 10")  # noqa: S608
    return cur.fetchall()


def summarise(rows: list) -> dict:
    """Return basic row stats."""
    return {"count": len(rows)}
