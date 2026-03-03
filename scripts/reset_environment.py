#!/usr/bin/env python3
"""
reset_environment.py
Cross-platform equivalent of reset_environment.sh

Shuts down Docker containers, removes images, purges the local database
and generated JSON graph artifacts. Test fixture folders (data/test_project*
and data/test_benchmark) are preserved.

Usage:
    python scripts/reset_environment.py

Run from the project root (where docker-compose.yml lives).
"""

import os
import sys
import glob
import subprocess

# ── Helpers ──────────────────────────────────────────────────────────────────

def _banner(text: str) -> None:
    line = "=" * 70
    print(line)
    print(text)
    print(line)


def _run(cmd: list[str], check: bool = True) -> int:
    """Run a subprocess command and return its exit code."""
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        print(f"  ⚠️  Command returned exit code {result.returncode}: {' '.join(cmd)}")
    return result.returncode


# ── Guard: must run from project root ────────────────────────────────────────

def _check_project_root() -> None:
    if not os.path.isfile("docker-compose.yml"):
        print("❌ Error: This script must be run from the root of the Strata project.")
        print("   Usage: python scripts/reset_environment.py")
        sys.exit(1)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    _check_project_root()

    _banner(
        "⚠️  WARNING: STRATA ENVIRONMENT RESET ⚠️\n"
        "======================================================================\n"
        "This will permanently destroy the local database (data/app.db),\n"
        "all generated JSON graph artifacts, and the built Docker images.\n"
        "Your test PHP files in data/test_project* and data/test_benchmark\n"
        "will be PRESERVED (they are standard fixtures, not runtime artifacts).\n"
        "----------------------------------------------------------------------"
    )

    try:
        confirm = input("Are you absolutely sure you want to perform a hard reset? (y/N): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nReset aborted.")
        sys.exit(0)

    if confirm.lower() != "y":
        print("Reset aborted.")
        sys.exit(0)

    print()
    print("[+] Shutting down Docker containers and pruning volumes...")
    _run(["docker", "compose", "down", "-v"])

    print("[+] Removing strata-api and strata-frontend images...")
    # Ignore errors — images may not exist yet
    _run(["docker", "rmi", "strata-api", "strata-frontend"], check=False)

    print("[+] Purging local artifacts and database...")
    targets = [
        os.path.join("data", "app.db"),
        *glob.glob(os.path.join("data", "*.json")),
    ]
    removed = 0
    for path in targets:
        if os.path.isfile(path):
            os.remove(path)
            removed += 1
    print(f"    Removed {removed} file(s).")

    print()
    print("✅ Strata Environment has been securely sanitized!")
    print("   Run 'docker compose up --build -d' to start completely fresh.")
    print("=" * 70)


if __name__ == "__main__":
    main()
