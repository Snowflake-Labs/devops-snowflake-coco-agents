# IDD

The scaffold skill is built on Intent-Driven Development (IDD), a design practice where prompts state the desired outcome rather than the procedural steps.

## The IDD prompt structure

Every skill prompt uses four sections:

```text
[Goal]         — the desired state / outcome
[Requirements] — intent statements, not steps
[Constraints]  — scope, safety rules, what not to do
[Output]       — what success looks like (Glass Box reporting)
```

This structure gives the LLM execution agent the *why* and the *what*, not the *how*.
The agent figures out the how — and proves it worked via the Output section.

## IDD vs step-by-step instructions

=== "Step-by-step (fragile)"

    ```text
    1. Run gh repo create
    2. Disable Actions
    3. Clone the repo
    4. Set secrets
    ...
    ```

    Breaks on any environment difference. No way to verify the outcome.

=== "IDD (intent-driven)"

    ```text
    [Goal]
    A new GitHub repo exists, Snowflake OIDC is configured,
    secrets are set, CI is ready to run on first push.

    [Constraints]
    - Do not enable Actions before secrets are configured
    - All Snowflake objects must follow naming convention PREFIX_GH_REPO_COCO_AGENT_*
    ...

    [Output]
    - repo_url: https://github.com/...
    - snowflake_user: DEMO_GH_NIMBLE_BROKER_COCO_AGENT_USER
    - "Setup complete."
    ```

    The agent finds the path that achieves the goal within the constraints.
    The Output section makes the result verifiable.

## Why it matters for agents

A vague prompt produces vague results. IDD forces the prompt author to define:

- The exact end state (Goal)
- The non-negotiable rules (Constraints)
- What proof of completion looks like (Output)

This is why CoCo's scaffold has an ICR of 48: one instruction compresses 48 operations because the intent is precisely stated. See [ICR](icr.md).

## Blog series

!!! note "External content"
    The blog series below is community content by Kamesh Sampath
    (Snowflake Developer Advocate). Links point to an external site
    not controlled by Snowflake.

Kamesh Sampath's IDD series (the intellectual foundation of this skill):

1. [Infrastructure-as-Intent: The Field Velocity Blueprint](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
2. [The Ghost in the Machine: Why AI Needs the Spirit of UML](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
3. [Intent-Driven Development: The Shift Developers Can't Ignore](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
4. [Intent Compression Ratio: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
5. [ICR and Token Economics](https://blogs.kameshs.dev/icr-and-token-economics-9a014a75b399)
