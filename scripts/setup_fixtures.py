#!/usr/bin/env python3
"""
setup_fixtures.py
Cross-platform equivalent of setup_fixtures.sh

Downloads the CodeIgniter 3 source from GitHub and places the system/ folder
under data/test_benchmark/system — the PHP class definitions used as the
benchmark fixture.

Usage:
    python scripts/setup_fixtures.py

Run from the project root BEFORE docker compose up on a new machine.
This is a one-time setup step — the data folder persists across resets.
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import tempfile

# ── Helpers ──────────────────────────────────────────────────────────────────

def _banner(text: str) -> None:
    line = "=" * 70
    print(line)
    print(text)
    print(line)


def _count_php_files(path: str) -> int:
    count = 0
    for root, _, files in os.walk(path):
        count += sum(1 for f in files if f.endswith(".php"))
    return count


# ── Guard: must run from project root ────────────────────────────────────────

def _check_project_root() -> None:
    if not os.path.isfile("docker-compose.yml"):
        print("❌ Error: Run this script from the root of the Strata project.")
        print("   Usage: python scripts/setup_fixtures.py")
        sys.exit(1)


# ── Download with progress indicator ─────────────────────────────────────────

def _download_with_progress(url: str, dest: str) -> None:
    """Download a file with a simple progress indicator."""
    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size <= 0:
            print(f"\r    Downloading... {block_num * block_size // 1024} KB", end="", flush=True)
        else:
            downloaded = min(block_num * block_size, total_size)
            pct = downloaded * 100 // total_size
            bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
            print(f"\r    [{bar}] {pct}%  ({downloaded // 1024}/{total_size // 1024} KB)", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=_reporthook)
    print()  # newline after progress bar


# ── Main ─────────────────────────────────────────────────────────────────────

GITHUB_URL = "https://github.com/bcit-ci/CodeIgniter/archive/refs/heads/develop.zip"
TARGET_DIR = os.path.join("data", "test_benchmark", "system")


def main() -> None:
    _check_project_root()

    _banner(" Strata: Test Fixture Setup")

    # ── Idempotency check ──────────────────────────────────────────────────
    if os.path.isdir(TARGET_DIR):
        print(f"✓ {TARGET_DIR} already exists — nothing to do.")
        print("  (Delete data/test_benchmark and re-run to force a fresh download.)")
        print("=" * 70)
        sys.exit(0)

    os.makedirs(os.path.join("data", "test_benchmark"), exist_ok=True)

    # ── Download into a temp directory (cleaned up automatically) ─────────
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "ci3.zip")
        extract_dir = os.path.join(tmpdir, "ci3_extracted")

        print(f"[+] Downloading CodeIgniter 3 source from GitHub ...")
        try:
            _download_with_progress(GITHUB_URL, zip_path)
        except Exception as exc:
            print(f"\n❌ Download failed: {exc}")
            sys.exit(1)

        print("[+] Extracting ...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # Locate the top-level CodeIgniter-* folder
        try:
            ci3_root = next(
                os.path.join(extract_dir, entry)
                for entry in os.listdir(extract_dir)
                if entry.startswith("CodeIgniter-")
                and os.path.isdir(os.path.join(extract_dir, entry))
            )
        except StopIteration:
            print("❌ Could not locate CodeIgniter-* folder inside the archive.")
            sys.exit(1)

        system_src = os.path.join(ci3_root, "system")
        if not os.path.isdir(system_src):
            print(f"❌ system/ directory not found inside {ci3_root}")
            sys.exit(1)

        print(f"[+] Copying system/ → {TARGET_DIR} ...")
        shutil.copytree(system_src, TARGET_DIR)
        # tmpdir and all its contents are auto-deleted here

    php_count = _count_php_files(os.path.join("data", "test_benchmark"))

    print()
    print(f"✅ test_benchmark ready — {php_count} PHP files in data/test_benchmark/system")
    print()
    print("   You can now start the stack:")
    print("   docker compose up --build -d")
    print("=" * 70)


if __name__ == "__main__":
    main()
