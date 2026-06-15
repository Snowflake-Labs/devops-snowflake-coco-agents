# Getting Started

## Before you begin

This plugin runs inside **Cortex Code (CoCo)**, Snowflake's agentic IDE.
Install CoCo before proceeding:

- [Cortex Code — official docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)

Once CoCo is running and connected to Snowflake, continue below.

## Install the plugin

```bash
cortex plugin install https://github.com/Snowflake-Labs/devops-snowflake-coco-agents
```

## Prerequisites

Install and authenticate each tool before running the scaffold skill.

=== "GitHub"

    **gh CLI**
    ```bash
    # macOS
    brew install gh

    # Linux (Debian/Ubuntu)
    sudo apt install gh

    # Authenticate
    gh auth login
    gh auth status  # verify
    ```

=== "GitLab"

    **glab CLI**
    ```bash
    # macOS
    brew install glab

    # Linux
    sudo apt install glab

    # Authenticate
    glab auth login
    glab auth status  # verify
    ```

**Snowflake CLI (both paths)**

```bash
pip install snowflake-cli
```

Configure a connection in `~/.snowflake/connections.toml`:

```toml
[connections.default]
account        = "<your-account>"   # e.g. xy12345.us-east-1
user           = "<your-user>"
authenticator  = "externalbrowser"
```

```bash
snow connection test  # verify
```

**Python 3.11+**

Required for URL encoding and JSON parsing inside scaffold steps.

## Choose your setup mode

When you run `/scaffold-for-github` or `/scaffold-for-gitlab`, the skill asks upfront:

```text
Quick start — cloud runners
  Create project → Snowflake OIDC → set secrets → re-enable CI → done (~10 min)

Full setup — with smoke test
  All steps including an end-to-end validation run with a sample app
```

For a first run, **Quick start** is recommended. You can always run the smoke test later.

## Run the scaffold

```text
# In CoCo chat panel:
/scaffold-for-github     # GitHub Actions
/scaffold-for-gitlab     # GitLab CI
/scaffold                # Choose platform interactively
```

See [GitHub scaffold](scaffold/github.md) or [GitLab scaffold](scaffold/gitlab.md) for the full 6-step walkthrough.
