# Devops With Snowflake CoCo Agent

A [Snowflake Cortex Code (CoCo)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
and [Claude Code](https://claude.ai/code) plugin with two skill sets:

- **Scaffold** — guided setup of autonomous CI/CD agent projects on GitHub or GitLab
- **IDD** — apply [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
  to your prompts and workflows

---

## How it works

The scaffold skills walk through six guided beats with confirm checkpoints:

```text
1. Create repo/project from template
2. Disable CI/CD until setup is complete
3. Provision Snowflake OIDC user (setup.sql + verify)
4. Set GitHub secrets or GitLab CI/CD variables
5. Optional smoke test → CI scans → issues created → fixes opened as PR/MR
6. Teardown (optional)
```

---

## Prerequisites

Install all three tools and authenticate before running any scaffold command.

### gh — GitHub CLI

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate
gh auth login
gh auth status    # verify
```

> Full install guide: [cli.github.com](https://cli.github.com)

### glab — GitLab CLI

```bash
# macOS
brew install glab

# Linux (Debian/Ubuntu)
sudo apt install glab

# Authenticate
glab auth login
glab auth status  # verify
```

> Full install guide: [gitlab.com/gitlab-org/cli](https://gitlab.com/gitlab-org/cli)

### snow — Snowflake CLI

```bash
pip install snowflake-cli
```

Configure a named connection with ACCOUNTADMIN in `~/.snowflake/connections.toml`:

```toml
[connections.default]
account   = "<your-account>"   # e.g. xy12345.us-east-1
user      = "<your-user>"
authenticator = "externalbrowser"
```

```bash
snow connection test           # verify
```

> Full install guide: [Snowflake CLI docs](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index)

---

## Installation

### Cortex Code (CoCo)

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

### Claude Code

```bash
# Add as a marketplace (recommended — enables /plugin update)
claude plugin marketplace add https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
claude plugin install devops-coco-agents@devops-coco-agents

# Or install directly without the marketplace
claude plugin install --source github --repo Snowflake-Labs/devops-snowflake-coco-agents
```

### Local (for development)

```bash
git clone https://github.com/Snowflake-Labs/devops-snowflake-coco-agents.git
cortex plugin install ./devops-snowflake-coco-agents    # CoCo
claude plugin install ./devops-snowflake-coco-agents    # Claude Code

# Validate before installing
claude plugin validate ./devops-snowflake-coco-agents
```

---

## Usage

Type any of these in the **chat panel** inside CoCo or Claude Code.

### Scaffold commands

| CoCo | Claude Code | What it does |
|------|-------------|--------------|
| `$devops-coco-agents:scaffold` | `/scaffold` | Choose platform interactively |
| `$devops-coco-agents:scaffold-for-github` | `/scaffold-for-github` | Guided GitHub Actions setup |
| `$devops-coco-agents:scaffold-for-gitlab` | `/scaffold-for-gitlab` | Guided GitLab CI setup |

### IDD commands

| CoCo | Claude Code | What it does |
|------|-------------|--------------|
| `$devops-coco-agents:idd` | `/idd` | Choose IDD tool interactively |
| `$devops-coco-agents:idd/evaluate-prompt` | `/idd/evaluate-prompt` | Score a prompt on IDD dimensions |
| `$devops-coco-agents:idd/rewrite-prompt` | `/idd/rewrite-prompt` | Guided IDD rewrite |
| `$devops-coco-agents:idd/measure-icr` | `/idd/measure-icr` | Measure Intent Compression Ratio |

---

## Quick Start

### Guided (recommended)

Type in the chat panel — the skill collects your repo name, Snowflake prefix,
and account, then guides through each step:

```text
$devops-coco-agents:scaffold-for-github   # GitHub Actions
$devops-coco-agents:scaffold-for-gitlab   # GitLab CI
```

### Non-interactive (`cortex exec`)

For automated or scripted setups. The prompts below use [IDD structure](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c).

**GitHub:**

```bash
export REPO_PATH=myorg/my-project \
       PREFIX=MYORG \
       SNOWFLAKE_ACCOUNT=xy12345.us-east-1

cortex exec -c <connection> --bypass --no-history \
  --allowed "Bash(gh *)" --allowed "Bash(snow *)" --allowed "Read" \
  - << 'EOF'
[Goal]
Set up a new GitHub repository from the github-coco-agent template and trigger
the CoCo scan->issue->fix automation loop.

[Requirements]
- Create repo from https://github.com/Snowflake-Labs/github-coco-agent
- Run snowflake/setup.sql with PREFIX and REPO_PATH from env
- Set three GitHub secrets: SNOWFLAKE_ACCOUNT, SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE
- Trigger cortex-scan.yml

[Constraints]
- Use environment variables as-is; do not prompt for them
- Only modify the new repo, not the template

[Output]
- Repository URL and Actions URL
- "Setup complete. Scan workflow triggered."
EOF
```

**GitLab:**

```bash
export PROJECT_PATH=mygroup/my-project \
       PREFIX=MYORG \
       SNOWFLAKE_ACCOUNT=xy12345.us-east-1 \
       GITLAB_TOKEN_coco=<token>

cortex exec -c <connection> --bypass --no-history \
  --allowed "Bash(glab *)" --allowed "Bash(snow *)" --allowed "Read" \
  - << 'EOF'
[Goal]
Set up a new GitLab project from the gitlab-coco-agent template and trigger
the CoCo scan->issue->fix automation loop.

[Requirements]
- Create project from https://gitlab.com/kameshsampath/gitlab-coco-agent
- Run snowflake/setup.sql with --enable-templating STANDARD
- Set four CI/CD variables: SNOWFLAKE_ACCOUNT (masked), SNOWFLAKE_USER,
  SNOWFLAKE_WAREHOUSE, GITLAB_TOKEN_coco (masked)
- Trigger the main branch pipeline

[Constraints]
- Use environment variables as-is; do not prompt for them

[Output]
- Project URL and pipelines URL
- "Setup complete. Scan pipeline triggered."
EOF
```

---

## IDD — Intent-Driven Development

> "A vague developer with AI produces noise. A precise developer with AI produces systems."
> — Kamesh Sampath

The `idd` skills help you apply IDD to any prompt or CI/CD workflow.

### IDD prompt structure

```text
[Goal]          — desired outcome / desired state
[Requirements]  — intent statements (not steps)
[Constraints]   — scope, safety rules, what not to do
[Output]        — what success looks like (Glass Box reporting)
```

### Intent Compression Ratio

```text
ICR = Total Operations / Intent Expressions

ICR 1–3   command relay        agent is just a wrapper
ICR 4–8   automation wrapper   meaningful compression
ICR 9+    architectural partner high agentic readiness
```

Target: **Glass Box Compression** — high ICR + full observability + safe retry.

### Blog series

1. [Infrastructure-as-Intent: The Field Velocity Blueprint](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
2. [The Ghost in the Machine: Why AI Needs the Spirit of UML](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
3. [Intent-Driven Development: The Shift Developers Can't Ignore](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
4. [Intent Compression Ratio: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
5. [ICR and Token Economics](https://blogs.kameshs.dev/icr-and-token-economics-9a014a75b399)

---

## Templates

| Platform | Template | CI/CD auth |
|----------|----------|------------|
| GitHub Actions | [Snowflake-Labs/github-coco-agent](https://github.com/Snowflake-Labs/github-coco-agent) | [snowflake-cli-action](https://github.com/snowflakedb/snowflake-cli-action) — OIDC |
| GitLab CI | [kameshsampath/gitlab-coco-agent](https://gitlab.com/kameshsampath/gitlab-coco-agent) | [snowflake-cicd-component](https://gitlab.com/snowflake-dev/snowflake-cicd-component) — OIDC |

---

## License

Plugin code and configuration: [Apache 2.0](LICENSE)

Skill content (`skills/`): [Snowflake Skills License](skills/scaffold/LICENSE)

---

Markdown style follows the [Markdown Guide](https://www.markdownguide.org/basic-syntax/)
and is enforced by [markdownlint](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
via `.markdownlint.yml` + pre-commit hook.
