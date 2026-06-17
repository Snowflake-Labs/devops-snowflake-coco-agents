# Step 5c: Verify Smart Fix Routing (GitHub)

> Sub-step of Step 5. Walks through all three smart-fix paths after the scan completes.

---

## Beat 1 — Ceiling source

Check the scan job summary for the active ceiling and its source:

```bash
gh run list --repo "$REPO_PATH" --workflow cortex-scan.yml --limit 1 --json databaseId --jq '.[0].databaseId'
```

Open the Actions summary and look for:

```
::notice::Fix ceiling: conservative (source: .github/coco-config.yml)
```

---

## Beat 2 — Auto-fix PR (LOW severity)

The `datetime.utcnow()` deprecation issue should have triggered an auto-fix PR automatically:

```bash
gh issue list --repo "$REPO_PATH" --label "coco:auto-fix"
gh pr list   --repo "$REPO_PATH" --state open
```

Expected: 1 issue labeled `coco:auto-fix`, 1 open PR replacing `datetime.utcnow()` with `datetime.now(timezone.utc)`.

---

## Beat 3 — Needs-review labels (MEDIUM + HIGH severity)

```bash
gh issue list --repo "$REPO_PATH" --label "coco:needs-review"
```

Expected: 2 issues — f-string SQL injection (high/medium) + subprocess shell=True injection (critical/high).

---

## Beat 4 — Comment trigger (`/coco fix`)

Trigger the fix on the SQL injection (f-string) needs-review issue — the one that routes to `/coco fix`:

```bash
ISSUE_NUM=$(gh issue list --repo "$REPO_PATH" --label "coco:needs-review" \
  --json number,title \
  --jq '[.[] | select(.title | test("sql|select|inject"; "i"))] | .[0].number')
echo "Triggering /coco fix on issue #$ISSUE_NUM"
gh issue comment "$ISSUE_NUM" --repo "$REPO_PATH" --body "/coco fix"
```

Watch `cortex-comment-fix.yml` trigger in Actions:

```bash
echo "$(gh repo view "$REPO_PATH" --json url -q .url)/actions"
```

Expected: fix workflow fires, PR raised for the logging issue within ~2 minutes.

---

When all four beats pass, load `github/steps/step-5b-revert.md`.
