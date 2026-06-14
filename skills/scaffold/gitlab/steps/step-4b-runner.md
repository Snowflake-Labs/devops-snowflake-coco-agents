# Step 4b: GitLab Local Runner Setup (Optional)

> Sub-step of Step 4. Load only if user chose "Yes, install runner".

⚠️ MANDATORY: call `enter_plan_mode`. Then present:

**What we'll do**
```
Installs:  $PROJECT_NAME/.gitlab/runner/  (gitignored, shell executor)
Tags:      [local]
Patches:   scan-code and coco-agent jobs get tags: [local]
PAT:       1-day service-user PAT — Keychain → SNOWFLAKE_PAT variable
```

Call `exit_plan_mode`. Then execute:

```bash
mkdir -p "$PROJECT_NAME/.gitlab/runner"
curl -LsS "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-darwin-arm64" \
  -o "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
chmod +x "$PROJECT_NAME/.gitlab/runner/gitlab-runner"
_j() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
RUNNER_TOKEN=$(glab api "projects/$ENCODED_PATH/runners" --method POST \
  --field "runner_type=project_type" --field "description=local-mac" --field "tag_list=local" \
  | _j "['token']")
"$PROJECT_NAME/.gitlab/runner/gitlab-runner" register \
  --non-interactive --url "https://gitlab.com" --token "$RUNNER_TOKEN" \
  --executor shell --config "$PROJECT_NAME/.gitlab/runner/config.toml"
python3 - << 'PYEOF'
import re, os
path = os.environ.get("PROJECT_NAME", ".") + "/.gitlab-ci.yml"
content = open(path).read()
for job in ["scan-code", "coco-agent"]:
    content = re.sub(rf"^({job}:)", rf"\1\n  tags: [local]", content, flags=re.MULTILINE)
open(path, "w").write(content)
print("Patched: tags: [local] added")
PYEOF
git -C "$PROJECT_NAME" add .gitlab-ci.yml
git -C "$PROJECT_NAME" commit -m "ci: use self-hosted local runner for testing [skip ci]"
RUNNER_ID=$(glab api "projects/$ENCODED_PATH/runners" \
  | python3 -c "import sys,json; r=[x for x in json.load(sys.stdin) if x.get('description')=='local-mac']; print(r[0]['id'] if r else '')")
nohup "$PROJECT_NAME/.gitlab/runner/gitlab-runner" run \
  --config "$PROJECT_NAME/.gitlab/runner/config.toml" \
  > "$PROJECT_NAME/.gitlab/runner/runner.log" 2>&1 &
RUNNER_PID=$!; echo $RUNNER_PID > "$PROJECT_NAME/.gitlab/runner/runner.pid"
sleep 3
grep -q "Listening for Jobs" "$PROJECT_NAME/.gitlab/runner/runner.log" \
  && echo "✓ Runner is listening (PID $RUNNER_PID)" \
  || echo "Still starting — check: tail -f $PROJECT_NAME/.gitlab/runner/runner.log"
python3 "$MANIFEST_OPS" fill-runner --manifest "$MANIFEST" --pid "$RUNNER_PID" --runner-id "$RUNNER_ID"
PAT_OPS="$SKILL_DIR/scripts/pat_ops.py"
python3 "$PAT_OPS" create --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT" --manifest "$MANIFEST"
KSVC=$(python3 "$PAT_OPS" service-name --user "$SF_USER" --account "$SNOWFLAKE_ACCOUNT")
security find-generic-password -s "$KSVC" -a "$SF_USER" -w \
  | glab variable set SNOWFLAKE_PAT --masked
```

```
ask_user_question:
  header: "Start runner"
  question: "Runner started in background. Confirmed listening?"
  options:
    - label: "Yes, runner is listening — continue"
    - label: "Not yet — show runner log"
    - label: "Stop here"
```
If "Not yet": `tail -20 "$PROJECT_NAME/.gitlab/runner/runner.log"` and re-ask.
