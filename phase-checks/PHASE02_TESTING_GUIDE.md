# Strata: Phase 2 Testing Guide

This guide validates the **Phase 2 Structural Intelligence Engine** end-to-end. Phase 2 transforms a raw PHP dependency graph into a mathematically rigorous structural analytics layer with typed edges, namespace-qualified node IDs, subgraph metric projections, and a persistence-backed inspection API.

**What Phase 2 proves:**

```
Typed Parser → Namespace IDs → Graph Build → Metric Projection → ComponentMetric DB → /metrics/{run_id}
```

> [!NOTE]
> **Phase 3 is now live.** When you analyse a project using the Phase 2 guide, the backend will automatically compute Phase 3 structural risk scores. You can view these directly on the **Risk Analysis** page in Streamlit.

---

## §1. Environment Readiness

> [!IMPORTANT]
> **First-time setup required on any new machine.**
> Before testing, run the fixture bootstrap script to create `data/test_benchmark`:
>
> ```bash
> ./scripts/setup_fixtures.sh
> ```
>
> This downloads CodeIgniter 3 (~166 PHP files) into `data/test_benchmark/system`.
> The `data/` folder is git-ignored — this fixture is never committed to the repo.
> Run it once; it persists across environment resets.

```bash
# Clean the environment (preserves test_project* and test_benchmark)
./scripts/reset_environment.sh

# Rebuild and start fresh
docker compose up --build -d
```

> **Note:** `data/test_project*` and `data/test_benchmark` are **preserved** by the reset script — they are standard test fixtures, not runtime artifacts. Only `data/app.db` and `data/*.json` are destroyed.

> **Note:** The file scanner has **no hardcoded limit** since Phase A. It will process all `.php` files found in the project path.

---

## §2. Synthetic Determinism Test (Primary Correctness Proof)

Phase 2's core requirement is **mathematical determinism**: the same codebase must produce identical floating-point metrics across all runs.

We use `test_project_2` — our controlled 4-class MVC project (`UserController`, `UserView`, `Database`, `Helper`).

```bash
python3 tests/test_reproducibility.py
```

**Expected output:**

```
Starting 5x reproducibility constraint test...
Executing Run 1/5...
Executing Run 2/5...
Executing Run 3/5...
Executing Run 4/5...
Executing Run 5/5...

SUCCESS: All 5 runs yielded mathematically IDENTICAL structural intelligence metrics.
```

---

## §3. Unit Test Suite

Run the automated unit and performance test battery inside the Docker container:

```bash
docker compose exec api pytest tests/test_metric_calculator.py tests/test_performance_ceiling.py -v
```

**Expected output:**

```
collected 4 items

tests/test_metric_calculator.py::test_metric_calculator_basic_star_topology PASSED
tests/test_performance_ceiling.py::test_performance_ceiling_200_nodes PASSED
tests/test_performance_ceiling.py::test_timeout_guard_triggers PASSED
tests/test_performance_ceiling.py::test_betweenness_skipped_for_large_graph PASSED

4 passed
```

**What each test validates:**

| Test                                         | Validates                                                              |
| :------------------------------------------- | :--------------------------------------------------------------------- |
| `test_metric_calculator_basic_star_topology` | Core metric math is correct on a known graph topology                  |
| `test_performance_ceiling_200_nodes`         | 200-node random graph completes in under 5 seconds (SLA)               |
| `test_timeout_guard_triggers`                | `calculate_all_metrics(timeout=N)` raises `RuntimeError` when exceeded |
| `test_betweenness_skipped_for_large_graph`   | Betweenness returns `-1.0` when node count > 2000 (cost guard)         |

---

## §4. Manual API Verification (Swagger)

Verify the raw Phase 2 metrics payload manually.

1. Open **http://localhost:8000/docs**
2. `POST /analyze` → **Try it out** → enter:

```json
{
  "project_path": "/data/test_project_2",
  "project_name": "Phase2_MVC_Test"
}
```

3. Note the returned `run_id`.
4. `GET /metrics/{run_id}` → enter your `run_id` → **Execute**.

**Expected response shape (Phase 2 — includes `"type"` field):**

```json
{
  "run_id": 1,
  "components": [
    {
      "name": "UserController",
      "type": "class",
      "in_degree": 0,
      "out_degree": 2,
      "betweenness": 0.0,
      "scc_size": 1,
      "blast_radius": 2
    },
    {
      "name": "Database",
      "type": "class",
      "in_degree": 1,
      "out_degree": 0,
      "betweenness": 0.0,
      "scc_size": 1,
      "blast_radius": 0
    }
  ]
}
```

> **Key check:** Every component must have a `"type": "class"` field. This confirms Phase D (component type persistence) is active.

---

## §5. Edge Type Validation

Verify that the parser is generating typed edges (Phase B).

1. Run an analysis on `test_project_2` (inheritance test requires `test_project` with `extends`).
2. Fetch the graph JSON from `data/graph_{run_id}.json`.
3. Inspect the `links` array:

```json
{
  "links": [
    {
      "source": "UserController",
      "target": "Database",
      "type": "instantiation",
      "weight": 1
    }
  ]
}
```

For a project with inheritance, you should see:

```json
{ "type": "inherits" }
{ "type": "implements" }
{ "type": "instantiation" }
{ "type": "method_call" }
```

> **Key check:** No edges should have `"type": "unknown"`. If they do, the parser encountered an unrecognised relationship pattern.

---

## §6. Real-World Benchmark Analysis (CodeIgniter 3)

This section validates Strata against a real legacy PHP framework — the scenario closest to actual client workloads.

**What `test_benchmark` contains:** CodeIgniter 3 system layer — 166 PHP files, minimal namespaces, deep inheritance, PHP 5-era coupling patterns.

```bash
# Run from outside Docker (API is exposed on port 8000)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/data/test_benchmark/system", "project_name": "codeigniter3_benchmark"}'
```

**Expected response:**

```json
{"run_id": N, "files": 166, "classes": 130, "edges": 31}
```

Then inspect the metrics on the returned `run_id` via Swagger or Streamlit.

**What to look for (semantic validation checklist):**

| Indicator          | What to confirm                                                                      |
| :----------------- | :----------------------------------------------------------------------------------- |
| Node IDs           | All use directory-relative fallback: `core\CI_Controller`, `database\CI_DB_driver`   |
| XML-RPC cluster    | `CI_Xmlrpc`, `XML_RPC_Client/Response/Message/Values` should all show `scc_size = 5` |
| DB blast radius    | `database\CI_DB` should have `blast_radius = 4` (touches 4 downstream components)    |
| Isolated libraries | `CI_Email`, `CI_FTP`, `CI_Zip` should have `in_degree = 0`, `out_degree = 0`         |
| `component_type`   | All 130 rows should show `"type": "class"` in the API response                       |

> A `scc_size = 5` on the XML-RPC cluster is the most important sanity check — it proves the SCC algorithm correctly identifies entangled legacy code clusters.

---

## §7. Web UI Validation (Structural Microscope)

The Streamlit frontend is a multi-page inspection interface. Open **http://localhost:8501**.

| Page                   | URL                            | Purpose                                        |
| :--------------------- | :----------------------------- | :--------------------------------------------- |
| **Strata** (Home)      | `http://localhost:8501`        | Trigger analysis, view Structural Summary Card |
| **Metrics Inspection** | Sidebar → `Metrics Inspection` | Query sortable metric matrix by Run ID         |
| **Experiment Results** | Sidebar → `Experiment Results` | Phase 3+ stub                                  |

### Step 7a: Trigger Analysis

1. Open `http://localhost:8501`.
2. Enter a project path (e.g. `/data/test_project_2` or `/data/test_benchmark/system`).
3. Click **Run Minimal Analysis**.
4. Confirm the Structural Summary Card shows Run ID, Files, Nodes, Edges.

### Step 7b: Inspect the Structural Matrix

1. Click **Metrics Inspection** in the sidebar.
2. Enter the `Run ID`.
3. Click **Query Structural Matrix**.
4. Confirm the **Type** column appears alongside Name, In/Out Degree, Betweenness, SCC Size, Blast Radius.
5. Sort by **Betweenness** to identify architectural chokepoints.
6. Sort by **Blast Radius** to identify highest change-propagation components.
7. Use **Download Raw JSON** to export the metric trace.

---

## §8. Teardown / Reset

To wipe the database and graph artifacts for a clean re-test:

```bash
./scripts/reset_environment.sh
```

This destroys: `data/app.db`, `data/*.json`, Docker volumes and images.

This **preserves:** `data/test_project*`, `data/test_benchmark` (permanent fixtures — not runtime data).

After reset, rebuild and start:

```bash
docker compose up --build -d
```
