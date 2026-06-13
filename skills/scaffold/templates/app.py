"""CoCo Agent Demo App
-------------------
A minimal Snowflake utility with intentional issues for the coco-agent scan/fix demo.
The agent will scan this file, raise issues, and open a fix MR automatically.
"""
from __future__ import annotations

import os

import snowflake.connector

# Issue 1: hardcoded schema — should come from an environment variable or config
SCHEMA = "PUBLIC"


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Return a Snowflake connection using credentials from environment."""
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        # Issue 2: password authentication — use authenticator="externalbrowser"
        # or WORKLOAD_IDENTITY instead of a plaintext password
        password=os.environ.get("SNOWFLAKE_PASSWORD", ""),
        schema=SCHEMA,
    )


def query_table(
    conn: snowflake.connector.SnowflakeConnection, table_name: str
) -> list:
    """Fetch the first 10 rows from the given table."""
    cur = conn.cursor()
    # Issue 3: SQL injection — table_name is interpolated directly into the query.
    # Use an allowlist or a quoted identifier instead.
    cur.execute(f"SELECT * FROM {table_name} LIMIT 10")  # noqa: S608
    return cur.fetchall()


def summarise(rows: list) -> dict:
    """Return basic row stats."""
    return {"count": len(rows)}
