#!/bin/bash

# Ensure the script is run from the project root
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: This script must be run from the root of the Strata project."
    echo "Usage: ./scripts/reset_environment.sh"
    exit 1
fi

echo "======================================================================"
echo "⚠️  WARNING: STRATA ENVIRONMENT RESET ⚠️"
echo "======================================================================"
echo "This will permanently destroy the local database (data/app.db),"
echo "all generated JSON graph artifacts, and the built Docker images."
echo "Your test PHP files in data/test_project* will be preserved."
echo "----------------------------------------------------------------------"

read -p "Are you absolutely sure you want to perform a hard reset? (y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Reset aborted."
    exit 0
fi

echo ""
echo "[+] Shutting down Docker containers and pruning volumes..."
docker compose down -v 

echo "[+] Removing strata-api and strata-frontend images..."
docker rmi strata-api strata-frontend 2>/dev/null

echo "[+] Purging local artifacts and database..."
rm -f data/app.db data/*.json

echo ""
echo "✅ Strata Environment has been securely sanitized!"
echo "Run 'docker compose up --build -d' to start completely fresh."
echo "======================================================================"
