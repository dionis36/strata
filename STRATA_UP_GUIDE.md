# 🚀 Strata: The Complete Up Guide

Welcome to **Strata**, the professional Modernization Advisory Suite for legacy PHP monoliths. This guide will take you from a bare machine to a fully functional analysis environment in minutes.

---

## 🛠️ 1. System Requirements

Before you begin, ensure your machine meets the following criteria:

*   **Operating System**: Linux (recommended), macOS, or Windows (WSL2).
*   **Docker & Docker Compose**: Installed and running.
*   **Python 3.8+**: Installed on the host machine for bootstrap scripts.
*   **Git**: Installed for repository management.

---

## ⚡ 2. One-Click Bootstrap

We provide a comprehensive Python script to automate the environment preparation. This script checks requirements, sets up environment variables, and provisions test datasets.

```bash
# From the project root
python3 scripts/setup_fixtures.py
```

### What this script does:
1.  **Requirement Check**: Verifies Docker and Git are in your system path.
2.  **Environment Setup**: Generates a `.env` file from the template if missing.
3.  **Data Provisioning**: 
    *   Downloads **CodeIgniter 3** (Structural Benchmark).
    *   Downloads **OWASP WebGoat PHP** (Real-world Legacy Monolith).
    *   Generates **Synthetic Test Projects** for immediate validation.

---

## 🏗️ 3. Starting the Engine

Once the bootstrap is complete, you can launch the entire Strata stack using Docker Compose. This starts the **FastAPI Backend** and the **Streamlit Frontend** side-by-side.

```bash
# Build and start in detached mode
docker compose up --build -d
```

### Verify the Stack:
*   **Frontend UI**: [http://localhost:8501](http://localhost:8501)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **System Status**: Check the sidebar in the Streamlit UI to confirm "Database: connected".

---

## 🔍 4. Running Your First Analysis

1.  Open the [Streamlit UI](http://localhost:8501).
2.  In the **Project Path** input, enter one of the pre-provisioned paths:
    *   `/data/test_project` (Minimal sanity check)
    *   `/data/test_benchmark/system` (CodeIgniter benchmark)
    *   `/data/OWASPWebGoatPHP-master` (Complex monolith)
3.  Click **Run Minimal Analysis**.
4.  Navigate to **Metrics Inspection** in the sidebar to explore the structural chokepoints.

---

## 📂 5. Setting Up Your Own Legacy Projects

Strata uses a Docker **volume mount** to see your local files. 

1.  Place your legacy PHP project inside the `strata/data/` directory on your host machine.
2.  In the Strata UI/API, refer to it using the container path prefix `/data/`.
    *   *Example*: If your project is at `strata/data/my_legacy_app/`, enter `/data/my_legacy_app` in the UI.

> [!TIP]
> You do **not** need to restart Docker when adding new projects to the `data/` folder. They are visible instantly!

---

## 🛑 6. Stopping vs. Resetting

Depending on your goal, you have two ways to power down the environment.

### Option A: Pause (Stop)
Use this if you just want to free up system resources but keep your database and progress intact.

```bash
docker compose stop
```
*   **What happens**: Containers are stopped.
*   **Persistence**: Your SQLite database (`data/app.db`) and all logs are **PRESERVED**.
*   **Resume**: Simply run `docker compose start` or `docker compose up -d` to continue where you left off.

### Option B: Hard Reset (Wipe)
Use this if you want to start from absolute scratch or if the environment becomes corrupted.

```bash
python3 scripts/reset_environment.py
```
*   **What happens**: Stops containers, removes them, and deletes built images.
*   **Persistence**: Your SQLite database (`data/app.db`) and generated JSON graphs are **PERMANENTLY DELETED**.
*   **Safety**: Your test projects in `data/test_project*` are **PRESERVED**.

---

> [!IMPORTANT]
> For detailed testing protocols for each development phase, refer to the [phase-checks/](file:///home/dio/Documents/strata/phase-checks/) directory.
