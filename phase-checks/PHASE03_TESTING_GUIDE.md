# Strata: Phase 3 Testing Guide

This guide validates the **Phase 3 Structural Risk Framework** end-to-end. Phase 3 transforms pure structural metrics (from Phase 2) into actionable risk indicators (criticality, instability, cycle participation, coupling pressure) and computes a final, normalized Risk Score ∈ `[0.0, 1.0]`.

**What Phase 3 proves:**

```
Phase 2 Metrics → Feature Normalization → Structural Indicator Engine → Risk Model → Classification → /risk/{run_id} API
```

---

## §1. Environment Readiness

> [!IMPORTANT]
> **First-time setup required on any new machine.**
> Before testing, ensure you have the legacy benchmark fixture by running:
>
> ```bash
> ./scripts/setup_fixtures.sh
> ```
>
> This downloads CodeIgniter 3 into `data/test_benchmark/system`.

```bash
# Clean the environment (preserves data fixtures)
./scripts/reset_environment.sh

# Rebuild and start fresh
docker compose up --build -d
```

> **Note:** The Phase 3 risk pipeline triggers automatically at the end of every Phase 2 analysis run. No separate command is needed to "start" Phase 3.

---

## §2. Risk Engine Unit Tests (Core Exit Criteria)

Phase 3 introduces a robust unit testing suite to validate the 6 core mathematical exit criteria defined in the specification.

Run the automated unit tests inside the Docker container:

```bash
docker compose exec api pytest tests/test_risk_engine.py -v
```

_(Alternatively, run it locally if you have Python + pytest installed: `PYTHONPATH=. pytest tests/test_risk_engine.py -v`)_

**Expected output:**

```
collected 6 items

tests/test_risk_engine.py::test_risk_score_bounds PASSED
tests/test_risk_engine.py::test_risk_determinism PASSED
tests/test_risk_engine.py::test_high_risk_components_match_intuition PASSED
tests/test_risk_engine.py::test_weight_override_changes_scores PASSED
tests/test_risk_engine.py::test_cycle_flag_set_for_scc_gt_1 PASSED
tests/test_risk_engine.py::test_normalizer_handles_all_zero_run PASSED

6 passed
```

**What each test validates:**

| Test                                        | Validates                                                                                                  |
| :------------------------------------------ | :--------------------------------------------------------------------------------------------------------- |
| `test_risk_score_bounds`                    | All calculated risk scores are clamped strictly between `[0.0, 1.0]`.                                      |
| `test_risk_determinism`                     | Identical metric inputs yield mathematically identical risk outputs across multiple executions.            |
| `test_high_risk_components_match_intuition` | A central node with high blast radius is ranked riskier than an isolated dummy node.                       |
| `test_weight_override_changes_scores`       | Passing custom config weights successfully perturbs the model output (Required for Phase 6 experiments).   |
| `test_cycle_flag_set_for_scc_gt_1`          | Any component in a strongly connected component (SCC > 1) reliably triggers `cycle_flag=1`.                |
| `test_normalizer_handles_all_zero_run`      | A pathologically degenerate graph (e.g. no edges) degrades gracefully without divide-by-zero fatal errors. |

---

## §3. Manual API Verification (Swagger)

Verify the Phase 3 endpoint payload manually via the interactive API docs.

1. Open **http://localhost:8000/docs**
2. `POST /analyze` → **Try it out** → enter the default `test_project_2` or benchmark project path.
3. Note the returned `run_id`.
4. `GET /risk/{run_id}` → enter your `run_id` → **Execute**.

**Expected response shape (Phase 3 Risk Payload):**

```json
{
  "run_id": 1,
  "components": [
    {
      "name": "UserController",
      "type": "class",
      "risk_score": 0.72456,
      "risk_level": "HIGH",
      "criticality_index": 0.81,
      "instability": 0.65,
      "cycle_flag": 0,
      "coupling_pressure": 0.55
    },
    ...
  ]
}
```

> **Key check:** The array must be pre-sorted with the highest `risk_score` at the top of the list.

---

## §4. Real-World Benchmark Analysis (CodeIgniter 3)

This section executes a live Phase 3 run against `test_benchmark/system`.

```bash
# Trigger an analysis run (API runs on port 8000)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/data/test_benchmark/system", "project_name": "ci3_risk_benchmark"}'
```

Once the run completes, fetch the risk payload or open the Streamlit UI (see §5).

**What to look for (Phase 3 Semantic Validation):**

| Indicator               | What to confirm on the Benchmark output                                                                                        |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **Risk Score ∈ [0,1]**  | Ensure no score surpasses 1.0.                                                                                                 |
| **CRITICAL Classes**    | Components heavily integrated (e.g. `core\CI_Router`, `core\CI_Loader`) should surface near the top with HIGH/CRITICAL status. |
| **Cyclic Components**   | Search for nodes like `CI_Xmlrpc` and `XML_RPC_...` — they must have `Cycle = 1` due to circular dependency coupling.          |
| **LOW Risk Components** | Uncoupled leaf classes (e.g. `CI_Zip`, `CI_Ftp`) should sit at the bottom with scores near `0.0` and `LOW` status.             |

---

## §5. Web UI Validation (Streamlit Risk Matrix)

The Streamlit interface now includes a dedicated Phase 3 view.

1. Open **http://localhost:8501**
2. Trigger an analysis on the Home page (or reuse your existing `Run ID`).
3. Expand the sidebar and click on **Risk Analysis**.
4. Enter the `Run ID` and click **Query Risk Matrix**.

**Expected UI Behavior:**

- Top summary metrics card showing total components and counts of 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW.
- A fully sortable dataframe with all derived Risk indicators (Risk Score, Level, Criticality, Instability, Cycle, Coupling).
- Risk is sorted descending by default to highlight the most structurally dangerous components.
- Ability to download the raw JSON matrix payload using the "Download Raw JSON" button.

---

## §6. Teardown / Reset

To wipe the analysis runs and test data for a clean re-test:

```bash
./scripts/reset_environment.sh
```

_(This respects your fixtures and only cleans database states and graph runtime files.)_
