"""Manifest operations for the devops-coco-agents scaffold skill.

Reads  .coco-agent/manifest.toml using stdlib tomllib (Python 3.11+, read-only).
Writes using a hand-rolled serializer scoped to the manifest schema — no
external dependencies required.

Schema (both GitHub and GitLab, identical structure):

    schema_version = "1"

    [config]
    stale_threshold_s        = 3600
    runner_stale_threshold_s = 300

    [template]
    name       = "github-coco-agent"
    repo_url   = "https://github.com/Snowflake-Labs/github-coco-agent"
    ref        = "main"
    cloned_at  = ""

    [project]
    platform   = "github"
    prefix     = "youruser"
    repo_path  = "org/repo-name"
    repo_name  = "repo-name"
    repo_url   = "https://github.com/org/repo-name"
    visibility = "private"
    run_mode   = "guided"
    created_at = "2026-06-13T10:00:00Z"

    [snowflake]
    user      = "YOURPREFIX_GH_MY_REPO_COCO_AGENT_USER"
    role      = "YOURPREFIX_GH_MY_REPO_COCO_AGENT_ROLE"
    warehouse = "YOURPREFIX_GH_MY_REPO_COCO_AGENT_WH"
    oidc_subject = "repo:org@123/repo-name@456:ref:refs/heads/main"

    [runner]
    installed  = false
    pid        = 0
    runner_id  = ""

    [steps.step_1]
    label        = "Create Project"
    status       = "PENDING"
    started_at   = ""
    completed_at = ""

    ...steps step_2 through step_4...

Usage:
    python3 manifest_ops.py <command> [options]

Commands:
    init           Write a fresh draft manifest after input collection
    move           Move draft into cloned repo and fill repo_path/repo_url
    step-start     Mark a step IN_PROGRESS with started_at timestamp
    step-complete  Mark a step COMPLETE with completed_at timestamp
    fill-snowflake Fill [snowflake] section with derived object names
    fill-oidc      Record the confirmed OIDC subject in [snowflake]
    fill-runner    Fill [runner] pid and runner_id after nohup launch
    read           Read a single dotted-path value from the manifest
    summary        Print a step progress table (used for resume detection)
    check-stale    Exit 0 (use cache) or 1 (re-run gate) based on step age
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import os
import re
import sys
import tomllib
from pathlib import Path

SCHEMA_VERSION = "1"

STEP_LABELS = {
    "step_1": "Create Project",
    "step_2": "Connect Snowflake",
    "step_3": "Configure",
    "step_4": "Watch the Loop",
}

# ---------------------------------------------------------------------------
# Field order constants — drive the serializer (preserves declaration order)
# ---------------------------------------------------------------------------

_ROOT_KEYS = ["schema_version"]

_CONFIG_KEYS = ["stale_threshold_s", "runner_stale_threshold_s"]

_TEMPLATE_KEYS = ["name", "repo_url", "ref", "cloned_at"]

_PROJECT_KEYS = [
    "platform",
    "prefix",
    "repo_path",
    "repo_name",
    "repo_url",
    "visibility",
    "run_mode",
    "created_at",
]

_SNOWFLAKE_KEYS = ["user", "role", "warehouse", "oidc_subject"]

_RUNNER_KEYS = ["installed", "pid", "runner_id"]

_STEP_KEYS = ["label", "status", "started_at", "completed_at"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _escape_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _toml_value(v: object) -> str:
    """Serialize a Python value to a TOML literal string."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        items = ", ".join(f'"{_escape_str(str(i))}"' for i in v)
        return f"[{items}]"
    if isinstance(v, str):
        return f'"{_escape_str(v)}"'
    return f'"{_escape_str(str(v))}"'


def _write_section(data: dict, ordered_keys: list[str]) -> list[str]:
    """Emit a flat dict in key-declaration order, then any remaining keys."""
    lines: list[str] = []
    emitted: set[str] = set()
    for key in ordered_keys:
        if key in data:
            lines.append(f"{key:<20} = {_toml_value(data[key])}")
            emitted.add(key)
    for key, val in data.items():
        if key not in emitted and not isinstance(val, dict):
            lines.append(f"{key:<20} = {_toml_value(val)}")
    return lines


def _section_rule(title: str, width: int = 72) -> str:
    fill = "─" * max(2, width - len(title) - 5)
    return f"# ── {title} {fill}"


# ---------------------------------------------------------------------------
# Public I/O API
# ---------------------------------------------------------------------------


def load_manifest(path: Path | str) -> dict:
    """Read manifest.toml.  Returns {} if missing or corrupt."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError:
        return {}


def save_manifest(path: Path | str, data: dict) -> None:
    """Write *data* to *path* as TOML.

    Creates the parent directory with mode 700 if needed.
    Sets the file mode to 600 after writing.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(p.parent, 0o700)

    lines: list[str] = ["# Machine-managed by Cortex Code. Do not hand-edit."]

    # Root scalars
    for key in _ROOT_KEYS:
        if key in data:
            lines.append(f"{key:<20} = {_toml_value(data[key])}")

    # [config]
    if "config" in data:
        lines += ["", _section_rule("config"), "[config]"]
        lines += _write_section(data["config"], _CONFIG_KEYS)

    # [template]
    if "template" in data:
        lines += ["", _section_rule("template"), "[template]"]
        lines += _write_section(data["template"], _TEMPLATE_KEYS)

    # [project]
    if "project" in data:
        lines += ["", _section_rule("project"), "[project]"]
        lines += _write_section(data["project"], _PROJECT_KEYS)

    # [snowflake]
    if "snowflake" in data:
        lines += ["", _section_rule("snowflake — no sensitive values"), "[snowflake]"]
        lines += _write_section(data["snowflake"], _SNOWFLAKE_KEYS)

    # [runner]
    if "runner" in data:
        lines += ["", _section_rule("runner"), "[runner]"]
        lines += _write_section(data["runner"], _RUNNER_KEYS)

    # [steps.step_N] in sorted order
    if "steps" in data:
        for step_key in sorted(data["steps"]):
            step = data["steps"][step_key]
            lines += ["", f"[steps.{step_key}]"]
            lines += _write_section(step, _STEP_KEYS)

    content = "\n".join(lines) + "\n"
    p.write_text(content, encoding="utf-8")
    with contextlib.suppress(OSError):
        os.chmod(p, 0o600)


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------


def _blank_steps() -> dict:
    return {
        key: {
            "label": label,
            "status": "PENDING",
            "started_at": "",
            "completed_at": "",
        }
        for key, label in STEP_LABELS.items()
    }


def _fresh_manifest(
    *,
    prefix: str,
    repo_name: str,
    visibility: str,
    run_mode: str,
    platform: str,
    template_name: str,
) -> dict:
    now = _now_iso()
    tpl_base = "https://github.com/Snowflake-Labs"
    return {
        "schema_version": SCHEMA_VERSION,
        "config": {
            "stale_threshold_s": 3600,
            "runner_stale_threshold_s": 300,
        },
        "template": {
            "name": template_name,
            "repo_url": f"{tpl_base}/{template_name}",
            "ref": "main",
            "cloned_at": "",
        },
        "project": {
            "platform": platform,
            "prefix": prefix,
            "repo_path": "",
            "repo_name": repo_name,
            "repo_url": "",
            "visibility": visibility,
            "run_mode": run_mode,
            "created_at": now,
        },
        "snowflake": {"user": "", "role": "", "warehouse": "", "oidc_subject": ""},
        "runner": {"installed": False, "pid": 0, "runner_id": ""},
        "steps": _blank_steps(),
    }


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    draft_path = Path(args.draft_path) / "manifest.toml"
    data = _fresh_manifest(
        prefix=args.prefix,
        repo_name=args.repo_name,
        visibility=args.visibility,
        run_mode=args.run_mode,
        platform=args.platform,
        template_name=args.template_name,
    )
    save_manifest(draft_path, data)
    print(f"✓ Draft manifest written to {draft_path}")
    return 0


def cmd_move(args: argparse.Namespace) -> int:
    src = Path(args.from_path) / "manifest.toml"
    dst_dir = Path(args.to_path)
    dst = dst_dir / "manifest.toml"

    if not src.exists():
        print(f"Error: source manifest not found: {src}", file=sys.stderr)
        return 1

    data = load_manifest(src)
    if not data:
        print(f"Error: could not read manifest at {src}", file=sys.stderr)
        return 1

    # Fill repo identity now that clone succeeded
    data["project"]["repo_path"] = args.repo_path
    data["project"]["repo_url"] = args.repo_url
    if args.repo_name:
        data["project"]["repo_name"] = args.repo_name
    if "template" in data:
        data["template"]["cloned_at"] = _now_iso()

    save_manifest(dst, data)

    # Clean up draft location
    src.unlink(missing_ok=True)
    with contextlib.suppress(OSError):
        src.parent.rmdir()
        src.parent.parent.rmdir()

    print(f"✓ Manifest moved to {dst}")
    return 0


def cmd_step_start(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    steps = data.setdefault("steps", {})
    step = steps.setdefault(
        args.step,
        {
            "label": STEP_LABELS.get(args.step, args.step),
            "status": "PENDING",
            "started_at": "",
            "completed_at": "",
        },
    )
    step["status"] = "IN_PROGRESS"
    step["started_at"] = _now_iso()
    save_manifest(args.manifest, data)
    print(f"✓ {args.step} → IN_PROGRESS")
    return 0


def cmd_step_complete(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    step = data.get("steps", {}).get(args.step)
    if not step:
        print(f"Error: step {args.step} not found in manifest", file=sys.stderr)
        return 1
    step["status"] = "COMPLETE"
    step["completed_at"] = _now_iso()
    save_manifest(args.manifest, data)
    print(f"✓ {args.step} → COMPLETE")
    return 0


def cmd_fill_snowflake(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    suffix = "GH" if args.platform == "github" else "GL"
    p = args.prefix.upper()
    r = re.sub(r"[^A-Z0-9]", "_", args.repo_name.upper())
    # update() rather than replace so a re-run keeps oidc_subject
    data.setdefault("snowflake", {}).update(
        {
            "user": f"{p}_{suffix}_{r}_COCO_AGENT_USER",
            "role": f"{p}_{suffix}_{r}_COCO_AGENT_ROLE",
            "warehouse": f"{p}_{suffix}_{r}_COCO_AGENT_WH",
        }
    )
    save_manifest(args.manifest, data)
    print(f"✓ [snowflake] filled with {p}_{suffix}_{r}_COCO_AGENT_* names")
    return 0


def cmd_fill_oidc(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    subject = args.subject.strip()
    if not subject:
        print("Error: --subject must not be empty", file=sys.stderr)
        return 1
    data.setdefault("snowflake", {})["oidc_subject"] = subject
    save_manifest(args.manifest, data)
    print(f"✓ [snowflake] oidc_subject = {subject}")
    return 0


def cmd_fill_runner(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    data.setdefault("runner", {})
    data["runner"]["installed"] = True
    data["runner"]["pid"] = int(args.pid) if str(args.pid).isdigit() else 0
    data["runner"]["runner_id"] = str(args.runner_id) if args.runner_id else ""
    save_manifest(args.manifest, data)
    print(f"✓ [runner] pid={args.pid} runner_id={args.runner_id}")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    keys = args.key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict) or k not in val:
            print(f"Error: key '{args.key}' not found in manifest", file=sys.stderr)
            return 1
        val = val[k]
    print(val)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    data = load_manifest(args.manifest)
    if not data:
        print(f"No manifest found at {args.manifest}")
        return 1
    proj = data.get("project", {})
    print(f"\n{'=' * 56}")
    print(f"  Manifest : {args.manifest}")
    print(f"  Project  : {proj.get('repo_url') or proj.get('repo_name', '?')}")
    print(f"  Prefix   : {proj.get('prefix', '?')}")
    print(f"  Platform : {proj.get('platform', '?')}")
    print("\n Step progress:")
    icon_map = {"COMPLETE": "✓", "IN_PROGRESS": "→", "PENDING": "○", "SKIPPED": "-"}
    for key in sorted(data.get("steps", {})):
        step = data["steps"][key]
        age = ""
        if step.get("completed_at"):
            try:
                completed = datetime.datetime.fromisoformat(step["completed_at"])
                secs = (datetime.datetime.now(datetime.UTC) - completed).total_seconds()
                age = f"  ({secs / 60:.0f}m ago)"
            except ValueError:
                pass
        icon = icon_map.get(step.get("status", "PENDING"), "?")
        label = step.get("label", key)
        status = step.get("status", "PENDING")
        print(f"    {icon}  {key}: {label} [{status}]{age}")
    print(f"{'=' * 56}\n")
    return 0


def cmd_check_stale(args: argparse.Namespace) -> int:
    """Exit 0 = use manifest cache; exit 1 = re-run gate check."""
    data = load_manifest(args.manifest)
    if not data:
        return 1
    step = data.get("steps", {}).get(args.step, {})
    if step.get("status") != "COMPLETE":
        return 1
    completed_at = step.get("completed_at", "")
    if not completed_at:
        return 1
    try:
        completed = datetime.datetime.fromisoformat(completed_at)
        age = (datetime.datetime.now(datetime.UTC) - completed).total_seconds()
        threshold = args.threshold or data.get("config", {}).get(
            "runner_stale_threshold_s" if "runner" in args.step else "stale_threshold_s",
            3600,
        )
        if age < threshold:
            print(f"Using manifest cache ({age:.0f}s old, threshold {threshold}s)")
            return 0
        return 1
    except ValueError:
        return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Manifest operations for the devops-coco-agents scaffold skill."
    )
    sub = p.add_subparsers(dest="command", required=True)

    # init
    pi = sub.add_parser("init", help="Write a fresh draft manifest after input collection")
    pi.add_argument("--draft-path", required=True, help="Directory to write manifest.toml into")
    pi.add_argument("--prefix", required=True)
    pi.add_argument("--repo-name", required=True)
    pi.add_argument("--visibility", required=True)
    pi.add_argument("--run-mode", required=True)
    pi.add_argument("--platform", required=True, choices=["github", "gitlab"])
    pi.add_argument("--template-name", required=True)

    # move
    pm = sub.add_parser("move", help="Move draft into cloned repo, fill repo_path/repo_url")
    pm.add_argument("--from", dest="from_path", required=True)
    pm.add_argument("--to", dest="to_path", required=True)
    pm.add_argument("--repo-path", required=True)
    pm.add_argument("--repo-url", required=True)
    pm.add_argument("--repo-name", default="")

    # step-start
    ps = sub.add_parser("step-start", help="Mark a step IN_PROGRESS")
    ps.add_argument("--manifest", required=True)
    ps.add_argument("--step", required=True)

    # step-complete
    pc = sub.add_parser("step-complete", help="Mark a step COMPLETE")
    pc.add_argument("--manifest", required=True)
    pc.add_argument("--step", required=True)

    # fill-snowflake
    pfs = sub.add_parser("fill-snowflake", help="Fill [snowflake] with derived object names")
    pfs.add_argument("--manifest", required=True)
    pfs.add_argument("--prefix", required=True)
    pfs.add_argument("--repo-name", required=True)
    pfs.add_argument("--platform", required=True, choices=["github", "gitlab"])

    # fill-oidc
    pfo = sub.add_parser("fill-oidc", help="Record the confirmed OIDC subject")
    pfo.add_argument("--manifest", required=True)
    pfo.add_argument("--subject", required=True)

    # fill-runner
    pfr = sub.add_parser("fill-runner", help="Fill [runner] pid and runner_id")
    pfr.add_argument("--manifest", required=True)
    pfr.add_argument("--pid", required=True)
    pfr.add_argument("--runner-id", default="")

    # read
    pr = sub.add_parser("read", help="Read a dotted-path value from the manifest")
    pr.add_argument("--manifest", required=True)
    pr.add_argument("--key", required=True, help="Dotted path, e.g. project.prefix")

    # summary
    psum = sub.add_parser("summary", help="Print step progress table")
    psum.add_argument("--manifest", required=True)

    # check-stale
    pcs = sub.add_parser("check-stale", help="Exit 0=use cache, 1=re-run gate")
    pcs.add_argument("--manifest", required=True)
    pcs.add_argument("--step", required=True)
    pcs.add_argument("--threshold", type=int, default=0, help="Override stale threshold (seconds)")

    return p


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    dispatch = {
        "init": cmd_init,
        "move": cmd_move,
        "step-start": cmd_step_start,
        "step-complete": cmd_step_complete,
        "fill-snowflake": cmd_fill_snowflake,
        "fill-oidc": cmd_fill_oidc,
        "fill-runner": cmd_fill_runner,
        "read": cmd_read,
        "summary": cmd_summary,
        "check-stale": cmd_check_stale,
    }
    fn = dispatch.get(args.command)
    if fn is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
