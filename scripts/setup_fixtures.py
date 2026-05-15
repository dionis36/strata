#!/usr/bin/env python3
"""
setup_fixtures.py
Enhanced Cross-platform bootstrap script for Strata.

Performs:
1. Requirements check (Docker, Git, Python).
2. Environment setup (.env creation).
3. Data directory initialization.
4. Legacy project downloads (CodeIgniter 3 and OWASP WebGoat PHP).
5. Synthetic test project generation.

Usage:
    python scripts/setup_fixtures.py
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import tempfile
import subprocess

# ── Configuration ─────────────────────────────────────────────────────────────

FIXTURES = {
    "codeigniter3": {
        "url": "https://github.com/bcit-ci/CodeIgniter/archive/refs/heads/develop.zip",
        "target": os.path.join("data", "test_benchmark", "system"),
        "extract_path": "system",
        "description": "CodeIgniter 3 (Structural Benchmark)"
    },
    "webgoat": {
        "url": "https://github.com/OWASP/WebGoatPHP/archive/refs/heads/master.zip",
        "target": os.path.join("data", "OWASPWebGoatPHP-master"),
        "extract_path": "", # Extract everything
        "description": "OWASP WebGoat PHP (Legacy Monolith)"
    }
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def _banner(text: str) -> None:
    line = "=" * 70
    print(line)
    print(text)
    print(line)


def _check_cmd(cmd: str) -> bool:
    """Check if a command is available in the system path."""
    return shutil.which(cmd) is not None


def _count_php_files(path: str) -> int:
    count = 0
    for root, _, files in os.walk(path):
        count += sum(1 for f in files if f.endswith(".php"))
    return count


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
    print()


# ── Step 1: Requirements Check ────────────────────────────────────────────────

def check_requirements():
    print("[+] Checking system requirements...")
    missing = []
    
    if not _check_cmd("docker"):
        missing.append("Docker")
    if not _check_cmd("git"):
        missing.append("Git")
        
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("   Please install them before proceeding.")
        # We don't exit here to allow setting up files even if docker isn't running
    else:
        print("✓ Docker and Git found.")


# ── Step 2: Environment Setup ─────────────────────────────────────────────────

def setup_env_file():
    if not os.path.isfile(".env"):
        print("[+] Creating .env from .env.example...")
        if os.path.isfile(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ .env created.")
        else:
            print("⚠️  .env.example not found. Creating a default .env...")
            with open(".env", "w") as f:
                f.write("DEBUG=True\n")
    else:
        print("✓ .env file already exists.")


# ── Step 3: Synthetic Projects ────────────────────────────────────────────────

def generate_synthetic_projects():
    print("[+] Generating synthetic test projects...")
    
    # test_project
    path1 = os.path.join("data", "test_project")
    os.makedirs(path1, exist_ok=True)
    with open(os.path.join(path1, "A.php"), "w") as f:
        f.write("<?php\nclass A {\n    public function foo() {\n        $b = new B();\n        $b->bar();\n    }\n}\n")
    with open(os.path.join(path1, "B.php"), "w") as f:
        f.write("<?php\nclass B {\n    public function bar() {}\n}\n")

    # test_project_2 (MVC)
    path2 = os.path.join("data", "test_project_2")
    os.makedirs(path2, exist_ok=True)
    # Simplified content for brevity in script
    files = {
        "UserController.php": "<?php class UserController { public function index() { $db = new Database(); $view = new UserView(); } }",
        "UserView.php": "<?php class UserView { }",
        "Database.php": "<?php class Database { }",
        "Helper.php": "<?php class Helper { }"
    }
    for name, content in files.items():
        with open(os.path.join(path2, name), "w") as f:
            f.write(content)
            
    print(f"✓ Synthetic projects ready in data/")


# ── Step 4: Legacy Fixtures ───────────────────────────────────────────────────

def setup_fixture(name, config):
    target = config["target"]
    if os.path.isdir(target):
        print(f"✓ {config['description']} already exists.")
        return

    print(f"[+] Setting up {config['description']}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "archive.zip")
        extract_dir = os.path.join(tmpdir, "extracted")

        print(f"    Downloading from {config['url']}...")
        try:
            _download_with_progress(config['url'], zip_path)
        except Exception as exc:
            print(f"    ❌ Download failed: {exc}")
            return

        print("    Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # Find root folder in zip
        root_folder = next(os.path.join(extract_dir, d) for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d)))
        
        src = os.path.join(root_folder, config["extract_path"]) if config["extract_path"] else root_folder
        
        print(f"    Installing to {target}...")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copytree(src, target, dirs_exist_ok=True)
        
    php_count = _count_php_files(target)
    print(f"✓ {name} ready ({php_count} PHP files).")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not os.path.isfile("docker-compose.yml"):
        print("❌ Error: Run this script from the root of the Strata project.")
        sys.exit(1)

    _banner(" Strata: Full Environment Bootstrap ")

    check_requirements()
    setup_env_file()
    generate_synthetic_projects()
    
    for name, config in FIXTURES.items():
        setup_fixture(name, config)

    print("\n" + "="*70)
    print("✅ STRATA BOOTSTRAP COMPLETE")
    print("="*70)
    print("Next steps:")
    print("1. Start the stack:  docker compose up --build -d")
    print("2. Access UI:        http://localhost:8501")
    print("3. Access API Docs:  http://localhost:8000/docs")
    print("="*70)


if __name__ == "__main__":
    main()
