# GitHub OIDC Subject Resolution

> Loaded from `github/steps/step-2-connect-snowflake.md`. Requires `$REPO_PATH`,
> `$MANIFEST`, `$MANIFEST_OPS`. Sets `$OIDC_SUBJECT` (confirmed by the user).

GitHub repos created, renamed, or transferred after 2026-07-15 (or opted in) emit an
**immutable** subject that embeds owner and repo IDs:
`repo:<owner>@<owner_id>/<repo>@<repo_id>:ref:refs/heads/main`. Older repos keep the
classic `repo:<owner>/<repo>:ref:refs/heads/main`. Ask GitHub which one this repo emits
rather than assuming. Runs after Step 1 because the repo IDs exist only once it is created.

Reference: <https://docs.github.com/actions/reference/openid-connect-reference>

---

## Resume

If the manifest already has `snowflake.oidc_subject`, use it as the default and skip
resolution:

```bash
OIDC_SUBJECT=$(python3 "$MANIFEST_OPS" read --manifest "$MANIFEST" \
  --key snowflake.oidc_subject 2>/dev/null)
[ -n "$OIDC_SUBJECT" ] && OIDC_SOURCE="resumed"
```

## Resolve

Only when `$OIDC_SUBJECT` is still empty. Order of trust:

```bash
OIDC_REF_SUFFIX=":ref:refs/heads/main"
OIDC_SOURCE="" ; OIDC_USE_DEFAULT="true"

# 1. Exact prefix GitHub will emit (handles immutable, classic, and opt-in).
#    Gate on exit code: on 4xx gh prints the error body to stdout.
if OIDC_SETTINGS=$(gh api "repos/$REPO_PATH/actions/oidc/customization/sub" \
  --jq '[.sub_claim_prefix // "", (.use_default | tostring), (.use_immutable_subject // false | tostring)] | @tsv' \
  2>/dev/null); then
  IFS=$'\t' read -r SUB_PREFIX OIDC_USE_DEFAULT USE_IMMUTABLE <<< "$OIDC_SETTINGS"
  if [ -n "$SUB_PREFIX" ]; then
    OIDC_SUBJECT="${SUB_PREFIX}${OIDC_REF_SUFFIX}"; OIDC_SOURCE="github"
  fi
fi

# 2. Settings unavailable: build the immutable form from repo IDs, unless GitHub
#    reported the repo is not on immutable subjects
if [ -z "$OIDC_SOURCE" ] && [ "${USE_IMMUTABLE:-true}" = "true" ] \
  && SUB_PREFIX=$(gh api "repos/$REPO_PATH" \
       --jq '"repo:\(.owner.login)@\(.owner.id)/\(.name)@\(.id)"' 2>/dev/null); then
  OIDC_SUBJECT="${SUB_PREFIX}${OIDC_REF_SUFFIX}"; OIDC_SOURCE="derived"
fi

# 3. Last resort: classic name-based subject
if [ -z "$OIDC_SOURCE" ]; then
  OIDC_SUBJECT="repo:${REPO_PATH}${OIDC_REF_SUFFIX}"; OIDC_SOURCE="classic"
fi
```

## Confirm

Ask once, pre-filled — the user accepts the default in the common case:

```
ask_user_question:
  header: "OIDC subject"
  question: "Snowflake will trust GitHub OIDC tokens with this subject. <source note> Accept or edit:"
  type: text
  defaultValue: "$OIDC_SUBJECT"
```

`<source note>` by `$OIDC_SOURCE`:

| Source | Note |
|--------|------|
| `github` | "Read from this repo's GitHub OIDC settings." |
| `derived` | "Built from repo/owner IDs (immutable format) — GitHub OIDC settings were not readable, so this is unverified." |
| `classic` | "Classic name-based format — could not read repo IDs. Verify against the token's `sub` claim." |
| `resumed` | "Saved from a previous run." |

If `$OIDC_USE_DEFAULT` = `false`, append: "⚠️ This repo uses a custom OIDC claim template,
so the `:ref:refs/heads/main` suffix may not match the real token — check the claim keys
in the repo's OIDC settings."

Set `OIDC_SUBJECT` to the confirmed value. It is persisted to the manifest in step-2a.
