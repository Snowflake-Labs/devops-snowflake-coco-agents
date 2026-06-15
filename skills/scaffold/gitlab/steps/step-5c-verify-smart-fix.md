# Step 5c: Verify Smart Fix Routing (GitLab)

> Sub-step of Step 5. Walks through all three smart-fix paths after the scan completes.

```bash
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
```

---

## Beat 1 — Ceiling source

Open the pipeline summary and look for the ceiling log line:

```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -3
```

Expected output in the scan-code job log:
```
Fix ceiling: conservative (source: .gitlab/coco-config.yml)
```

---

## Beat 2 — Auto-fix MR (LOW severity)

The hardcoded-schema issue should have triggered an auto-fix MR automatically:

```bash
glab issue list --label "coco:auto-fix"
glab mr list --state opened
```

Expected: 1 issue labeled `coco:auto-fix`, 1 open MR fixing `SCHEMA = "PUBLIC"`.

---

## Beat 3 — Needs-review labels (MEDIUM + HIGH severity)

```bash
glab issue list --label "coco:needs-review"
```

Expected: 2 issues — debug-log info disclosure (medium) + SQL injection (high).

---

## Beat 4 — Comment trigger (`/coco fix`)

Trigger the fix on the MEDIUM severity needs-review issue via a note:

```bash
ISSUE_IID=$(glab issue list --label "coco:needs-review" -P 1 \
  | python3 -c "
import sys
for line in sys.stdin:
    if 'log' in line.lower() or 'debug' in line.lower():
        print(line.split()[0].lstrip('#'))
        break
")
echo "Triggering /coco fix on issue #$ISSUE_IID"
glab api "projects/$ENCODED_PATH/issues/$ISSUE_IID/notes" \
  -X POST -F "body=/coco fix"
```

Watch the comment-fix pipeline job trigger:
```bash
echo "https://gitlab.com/$PROJECT_PATH/-/pipelines"
glab pipeline list --project "$PROJECT_PATH" 2>&1 | head -3
```

Expected: fix job fires, MR raised for the logging issue within ~2 minutes.

---

When all four beats pass, load `gitlab/steps/step-5b-revert.md`.
