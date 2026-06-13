# devops-coco-agents

A CoCo / Claude Code plugin that scaffolds new projects from the
[github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) and
[gitlab-coco-agent](https://gitlab.com/kameshsampath/gitlab-coco-agent) templates
and guides you through the scan->issue->fix automation loop end-to-end.

## What it does

1. Creates a new repo/project from the template
2. Provisions Snowflake OIDC resources (`setup.sql`)
3. Sets GitHub secrets or GitLab CI/CD variables
4. Triggers the first scan pipeline
5. Walks through each stage with confirm checkpoints

The automation loop runs entirely in CI — Cortex scans for bugs,
opens `[coco-agent]` issues, and the fix pipeline auto-applies the fix
and opens a PR/MR.

## Installation

### Cortex Code (CoCo)

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

### Claude Code

Add as a marketplace (recommended — enables `/plugin update`):

```bash
claude plugin marketplace add https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
claude plugin install devops-coco-agents@devops-coco-agents
```

Or install directly:

```bash
claude plugin install --source github --repo Snowflake-Labs/devops-snowflake-coco-agents
```

### Local install (for development)

```bash
git clone https://github.com/Snowflake-Labs/devops-snowflake-coco-agents.git
cortex plugin install ./devops-snowflake-coco-agents       # CoCo
claude plugin install ./devops-snowflake-coco-agents       # Claude Code
```

Validate the plugin structure before installing:

```bash
claude plugin validate ./devops-snowflake-coco-agents
```

## Usage

From the chat panel:

```
$scaffold github    # guided GitHub scaffold   (CoCo)
$scaffold gitlab    # guided GitLab scaffold   (CoCo)
$scaffold           # choose platform interactively

/scaffold           # guided scaffold          (Claude Code)
```

## Quick Start

### Guided (recommended)

```
$scaffold github    # walks you through all steps with confirm checkpoints
$scaffold gitlab
```

The skill collects your target repo/project, Snowflake prefix, and account,
then guides you through each step.

### Non-interactive (`cortex exec`)

**GitHub:**

```bash
export REPO_PATH=myorg/my-project PREFIX=MYORG SNOWFLAKE_ACCOUNT=xy12345.us-east-1

cortex exec -c <connection> --bypass --no-history \
  --allowed "Bash(gh *)" --allowed "Bash(snow *)" --allowed "Read" \
  - << 'EOF'
You are setting up a new GitHub repository from the github-coco-agent template
to run the CoCo scan->issue->fix automation loop.

Environment variables are already set: REPO_PATH, PREFIX, SNOWFLAKE_ACCOUNT.

Steps:
1. gh repo create "$REPO_PATH" \
     --template https://github.com/Snowflake-Labs/github-coco-agent \
     --public --clone
   cd into the last segment of REPO_PATH.

2. snow sql -f snowflake/setup.sql \
     -D "PREFIX=$PREFIX" -D "REPO_PATH=$REPO_PATH"

3. gh secret set SNOWFLAKE_ACCOUNT   --body "$SNOWFLAKE_ACCOUNT"
   gh secret set SNOWFLAKE_ROLE      --body "${PREFIX}_GITHUB_COCO_AGENT_ROLE"
   gh secret set SNOWFLAKE_WAREHOUSE --body "${PREFIX}_GITHUB_COCO_AGENT_WH"

4. gh workflow run cortex-scan.yml

5. Print the repository URL and Actions URL.
EOF
```

**GitLab:**

```bash
export PROJECT_PATH=mygroup/my-project PREFIX=MYORG \
       SNOWFLAKE_ACCOUNT=xy12345.us-east-1 GITLAB_TOKEN_coco=<token>

cortex exec -c <connection> --bypass --no-history \
  --allowed "Bash(glab *)" --allowed "Bash(snow *)" --allowed "Read" \
  - << 'EOF'
You are setting up a new GitLab project from the gitlab-coco-agent template
to run the CoCo scan->issue->fix automation loop.

Environment variables are already set: PROJECT_PATH, PREFIX, SNOWFLAKE_ACCOUNT, GITLAB_TOKEN_coco.

Steps:
1. GROUP="${PROJECT_PATH%/*}"; PROJECT_NAME="${PROJECT_PATH##*/}"
   glab project create "$PROJECT_NAME" \
     --group "$GROUP" \
     --template-project https://gitlab.com/kameshsampath/gitlab-coco-agent
   glab repo clone "$PROJECT_PATH" && cd "$PROJECT_NAME"

2. snow sql -f snowflake/setup.sql \
     -D "PREFIX=$PREFIX" -D "REPO_PATH=$PROJECT_PATH" \
     --enable-templating STANDARD

3. glab variable set SNOWFLAKE_ACCOUNT   --value "$SNOWFLAKE_ACCOUNT"   --masked
   glab variable set SNOWFLAKE_USER      --value "${PREFIX}_GITLAB_COCO_AGENT_USER"
   glab variable set SNOWFLAKE_WAREHOUSE --value "${PREFIX}_GITLAB_COCO_AGENT_WH"
   glab variable set GITLAB_TOKEN_coco   --value "$GITLAB_TOKEN_coco"   --masked

4. glab pipeline run --branch main

5. Print the project URL and pipelines URL.
EOF
```

## Prerequisites

| Tool | Purpose |
|------|---------|
| `gh` | GitHub CLI — `gh auth login` |
| `glab` | GitLab CLI — `glab auth login` |
| `snow` | Snowflake CLI — configured connection with ACCOUNTADMIN |

## Templates

| Platform | Template |
|----------|----------|
| GitHub Actions | [Snowflake-Labs/github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) |
| GitLab CI | [kameshsampath/gitlab-coco-agent](https://gitlab.com/kameshsampath/gitlab-coco-agent) |

## License

Plugin code and configuration: [Apache 2.0](LICENSE)

Skill content (`skills/`): [Snowflake Skills License](skills/scaffold/LICENSE)
