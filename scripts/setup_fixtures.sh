#!/bin/bash
# =============================================================================
# setup_fixtures.sh
# Creates the test_benchmark fixture (CodeIgniter 3) under data/test_benchmark.
# This is a one-time setup step — the data folder persists across resets.
#
# Usage: ./scripts/setup_fixtures.sh
# Run this from the project root BEFORE docker compose up on a new machine.
# =============================================================================

set -e

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Run this script from the root of the Strata project."
    echo "   Usage: ./scripts/setup_fixtures.sh"
    exit 1
fi

TARGET="data/test_benchmark/system"

echo "======================================================================"
echo " Strata: Test Fixture Setup"
echo "======================================================================"

if [ -d "$TARGET" ]; then
    echo "✓ $TARGET already exists — nothing to do."
    echo "  (Delete data/test_benchmark and re-run to force a fresh download.)"
    echo "======================================================================"
    exit 0
fi

echo "[+] Creating data/test_benchmark/system ..."
mkdir -p data/test_benchmark

# Download CodeIgniter 3 as a zip (no git required on host machine)
echo "[+] Downloading CodeIgniter 3 source from GitHub ..."
curl -sSL https://github.com/bcit-ci/CodeIgniter/archive/refs/heads/develop.zip \
     -o /tmp/ci3.zip

echo "[+] Extracting ..."
unzip -q /tmp/ci3.zip -d /tmp/ci3_extracted
rm -f /tmp/ci3.zip

# Copy only the system/ folder — the PHP class definitions we benchmark
CI3_ROOT=$(find /tmp/ci3_extracted -maxdepth 1 -type d -name "CodeIgniter-*" | head -1)
cp -r "$CI3_ROOT/system" data/test_benchmark/system
rm -rf /tmp/ci3_extracted

PHP_COUNT=$(find data/test_benchmark -name "*.php" | wc -l | tr -d ' ')
echo ""
echo "✅ test_benchmark ready — ${PHP_COUNT} PHP files in data/test_benchmark/system"
echo ""
echo "  You can now start the stack:"
echo "  docker compose up --build -d"
echo "======================================================================"
