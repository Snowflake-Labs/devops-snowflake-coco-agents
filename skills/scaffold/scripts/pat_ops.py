"""PAT lifecycle management for the scaffold local runner.

Creates a short-lived (1-day) Programmatic Access Token for the service user,
stores it in macOS Keychain, and can revoke it when the smoke test is done.
Token is never printed — it flows Snowflake → Keychain → CI secret directly.

Usage:
  python3 pat_ops.py create --user SF_USER --account ACCOUNT --manifest MANIFEST
  python3 pat_ops.py revoke --user SF_USER --account ACCOUNT --manifest MANIFEST
  python3 pat_ops.py service-name --user SF_USER --account ACCOUNT
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PAT_SUFFIX = "_COCO_PAT"
EXPIRY_DAYS = 1


def _keychain_service(account: str, user: str) -> str:
    """Deterministic Keychain service name — unique per (account, user).

    Formula: coco-sf-{account}-{user}, both normalised to lowercase-hyphen.
    Reconstructable anywhere the skill knows SNOWFLAKE_ACCOUNT + SF_USER.
    """
    norm = str.maketrans("_", "-")
    return f"coco-sf-{account.lower().translate(norm)}-{user.lower().translate(norm)}"


def _snow_sql(query: str) -> list[dict]:
    result = subprocess.run(
        ["snow", "sql", "-q", query, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout) if result.stdout.strip() else []


def _keychain(action: str, service: str, user: str, token: str | None = None) -> str | None:
    if action == "store":
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-U",
                "-s",
                service,
                "-a",
                user,
                "-w",
                token,
            ],
            check=True,
            capture_output=True,
        )
        return None
    if action == "fetch":
        r = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", user, "-w"],
            capture_output=True,
            text=True,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    if action == "delete":
        subprocess.run(
            ["security", "delete-generic-password", "-s", service, "-a", user],
            capture_output=True,
        )
        return None
    return None


def _manifest_ops(manifest: str, *extra_args: str) -> None:
    """Delegate to manifest_ops.py in the same scripts/ directory."""
    script = Path(__file__).parent / "manifest_ops.py"
    subprocess.run([sys.executable, str(script), *extra_args, "--manifest", manifest], check=True)


def cmd_create(args: argparse.Namespace) -> int:
    svc = _keychain_service(args.account, args.user)
    pat_name = args.user + PAT_SUFFIX
    rows = _snow_sql(
        f"ALTER USER {args.user} ADD PROGRAMMATIC ACCESS TOKEN {pat_name} "
        f"EXPIRES_IN DAYS = {EXPIRY_DAYS} "
        f"COMMENT = 'Smoke test only — revoked at end of step-5';"
    )
    token = next(
        (str(v) for row in rows for k, v in row.items() if k.upper() == "TOKEN"),
        None,
    )
    if not token:
        print("Error: PAT token not found in SQL output", file=sys.stderr)
        return 1
    _keychain("store", svc, args.user, token)
    if args.manifest:
        _manifest_ops(args.manifest, "fill-pat", "--pat-name", pat_name)
    print(f"✓ PAT {pat_name} created (expires {EXPIRY_DAYS}d) — Keychain service: {svc}")
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    svc = _keychain_service(args.account, args.user)
    pat_name = args.user + PAT_SUFFIX
    _snow_sql(f"ALTER USER {args.user} DROP PROGRAMMATIC ACCESS TOKEN {pat_name};")
    _keychain("delete", svc, args.user)
    if args.manifest:
        _manifest_ops(args.manifest, "fill-pat", "--pat-name", "")
    print(f"✓ PAT {pat_name} revoked and removed from Keychain")
    return 0


def cmd_service_name(args: argparse.Namespace) -> int:
    """Print the Keychain service name — used in skill steps for `security` calls."""
    print(_keychain_service(args.account, args.user))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PAT lifecycle for scaffold local runner")
    sub = parser.add_subparsers(dest="command")

    for cmd in ("create", "revoke"):
        p = sub.add_parser(cmd)
        p.add_argument("--user", required=True)
        p.add_argument("--account", required=True, help="Snowflake account identifier")
        p.add_argument("--manifest", default="", help="Manifest path to persist pat_name")

    sn = sub.add_parser("service-name", help="Print Keychain service name")
    sn.add_argument("--user", required=True)
    sn.add_argument("--account", required=True)

    args = parser.parse_args()
    if args.command == "create":
        return cmd_create(args)
    if args.command == "revoke":
        return cmd_revoke(args)
    if args.command == "service-name":
        return cmd_service_name(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
