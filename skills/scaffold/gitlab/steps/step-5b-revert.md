# Step 5b: Revert and Protect (GitLab)

> Sub-step of Step 5. Load after smoke test is confirmed done.

**Revert smoke-test commit** (push triggers cleanup run):

```bash
cd "$PROJECT_NAME" && git revert HEAD --no-edit && git push
```

**Protect main branch** (smoke test complete — no more direct pushes needed):

```bash
glab api "projects/$ENCODED_PATH/protected_branches" \
  -X POST -F name=main -F push_access_level=0 -F merge_access_level=40
```

```bash
python3 "$MANIFEST_OPS" step-complete --manifest "$MANIFEST" --step step_5
```

### What we did

- Smoke-test reverted — cleanup pipeline triggered
- Main branch protected (MR reviews required, push restricted)

### ICR

```
/scaffold ICR = 48
```

One instruction automated 48 state-changing operations: project + OIDC + tokens +
CI ceiling + smoke-test + issue routing + branch protection.
See `docs/idd/icr.md` for the full breakdown and adoption ladder.
