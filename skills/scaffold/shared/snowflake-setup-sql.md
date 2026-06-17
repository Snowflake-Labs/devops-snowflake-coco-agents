# Shared: Snowflake Setup SQL

> Loaded from step-2a. `$SF_ROLE`, `$SF_USER`, `$SF_WH`, `$OIDC_ISSUER`, `$OIDC_SUBJECT`
> must be set by the calling step before loading this file.

---

⚠️ MANDATORY: call `enter_plan_mode`. Display the full SQL block below with values
substituted so the user can review before anything runs:

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS $SF_ROLE;
GRANT ROLE $SF_ROLE TO ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS $SF_WH
  WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
GRANT USAGE ON WAREHOUSE $SF_WH TO ROLE $SF_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE $SF_ROLE;
CREATE USER IF NOT EXISTS $SF_USER
  TYPE = SERVICE DEFAULT_ROLE = $SF_ROLE DEFAULT_WAREHOUSE = $SF_WH;
GRANT ROLE $SF_ROLE TO USER $SF_USER;
ALTER USER $SF_USER SET
  WORKLOAD_IDENTITY = (
    TYPE    = OIDC
    ISSUER  = '$OIDC_ISSUER'
    SUBJECT = '$OIDC_SUBJECT'
  );
```

Call `exit_plan_mode`. Execute **all statements in a single `snowflake_sql_execute` call**
(separate statements with `;` — do NOT execute them one at a time).

**Verify** (single `snowflake_sql_execute`):

```sql
SHOW ROLES LIKE '$SF_ROLE'; SHOW WAREHOUSES LIKE '$SF_WH';
```

If empty or error: ⚠️ Re-run this step.
