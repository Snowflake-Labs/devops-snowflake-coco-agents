# Shared: Snowflake DROP SQL

Guard and drop Snowflake objects created by this scaffold.
Called from step-6 teardown sub-steps with `$SF_USER`, `$SF_WH`, `$SF_ROLE` from manifest.

**Guard — abort if names don't match COCO_AGENT pattern:**

```bash
for _obj in "$SF_USER" "$SF_WH" "$SF_ROLE"; do
  [[ "$_obj" =~ _COCO_AGENT_(USER|ROLE|WH)$ ]] \
    || { echo "⚠️  Guard blocked: '$_obj' — aborting"; exit 1; }
done
```

**Execute using `snowflake_sql_execute`:**

```sql
DROP USER      IF EXISTS $SF_USER;
DROP WAREHOUSE IF EXISTS $SF_WH;
DROP ROLE      IF EXISTS $SF_ROLE;
```

See `references/teardown.md` for full ordering rules.
