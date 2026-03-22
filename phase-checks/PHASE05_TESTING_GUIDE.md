# Strata: Phase 5 Testing Guide

## What This Validates

The **Extraction Intelligence & Simulation Engine**. This phase evaluates sets of components as unified extraction candidates (modules) by simulating their isolation and measuring structural impact.

---

## 1. Reset & Rebuild

```bash
./scripts/reset_environment.sh
docker compose up --build -d
```

## 2. Unit Tests

```bash
docker compose exec api pytest tests/test_extraction_engine.py
```

**Expected:** All tests pass, validating SCC grouping, greedy conflict resolution, and the proxy node rewiring simulation.

## 3. API Verification

1. Run analysis: `POST /analyze` via `http://localhost:8000/docs`
2. Call `GET /extraction/{run_id}`
   **Expected:** A JSON list of `ExtractionCandidate` models, containing the unit grouping, overall quality score, dimensional impact (dependency breaks, interface complexity, data isolation, risk change), and a recommendation (e.g., `SAFE_TO_EXTRACT`).

## 4. UI Walkthrough

1. Open Streamlit on `http://localhost:8501/`
2. Navigate to **Extraction Simulation** via the sidebar.
3. Query the `Run ID`
4. Observe the Ranked Candidates table showing the extracted unit names, score, and safe/caution recommendation.
5. Use the select box at the bottom to dive deep into a specific component. Notice the simulated risk shift and data isolation difficulty metrics presented.
