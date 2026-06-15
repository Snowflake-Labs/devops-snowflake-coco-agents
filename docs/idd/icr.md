# Intent Compression Ratio (ICR)

ICR measures how much work one human instruction compresses into agent operations:

```text
ICR = Total operations the agent performs ÷ Human instructions required
```

## ICR maturity ladder

| ICR Range | What it means | Category |
|-----------|--------------|----------|
| 1–3 | Agent is a copy-paste wrapper | Command relay |
| 4–8 | Meaningful automation | Automation wrapper |
| 9–15 | Agent owns the workflow | Agentic partner |
| **15+** | **1 instruction runs the full DAG** | **Intent engine** |

## `/scaffold` ICR = 48

One conversation instruction. 48 distinct state-changing operations:

- Repo creation + Actions disable
- Snowflake ROLE + WAREHOUSE + USER provisioned
- OIDC trust configured (WORKLOAD_IDENTITY)
- CI secrets set
- Fix-mode ceiling variable set
- Manifest written at every step
- Optional: runner installed, PAT created, smoke test pushed, PRs raised, teardown

This is the number to cite when asked *"how do we measure CoCo adoption?"*

A team at ICR 48 is getting fundamentally different leverage than a team at ICR 3.

## Measure your own ICR

Use the IDD skill to measure your team's agentic maturity:

```text
/idd-measure-icr
```

## The ICR adoption ladder

```text
Level 0 — No agent       →  Team does everything manually
Level 1 — Command relay  →  ICR 1–3    Agent wraps a few commands
Level 2 — Wrapper        →  ICR 4–8    Team saves hours per sprint
Level 3 — Partner        →  ICR 9–15   Agent owns full workflows
Level 4 — Intent engine  →  ICR 15+    devops-coco-agents /scaffold = 48
```

Target: all teams at Level 3+ within one quarter of CoCo install.
