# Strata: Phase 4.5 Testing Guide

## What This Validates

The **Risk Explainability Engine** — a deterministic, rule-based layer that answers _why_ each component is at risk with structured, evidence-backed explanations.

---

## §1. Reset & Rebuild

```bash
./scripts/reset_environment.sh
docker compose up --build -d
```

---

## §2. Unit Tests (Inside Docker)

```bash
docker compose exec api python3 tests/test_explanation_engine.py
```

**Expected:**

```
✅ All Phase 4.5 Explanation Engine tests passed!
```

Tests cover:

- Rule firing on high-risk component
- Zero-risk → no high-severity explanations
- Cap at 5 explanations even when all 8 rules fire
- Weight-descending order
- Template substitution (no `{` in rendered messages)
- Determinism across 3 identical calls
- Evidence builder: correct dependents, file path, null-graph safety

---

## §3. API Verification

1. Run analysis: `POST /analyze` via `http://localhost:8000/docs`
2. Note the `run_id`
3. Call `GET /explain/{run_id}`

**Expected response shape:**

```json
{
  "run_id": 1,
  "components": [
    {
      "component_name": "system\\database\\DB_query_builder",
      "risk_level": "CRITICAL",
      "final_risk": 0.91,
      "explanations": [
        {
          "type": "high_criticality",
          "category": "structural",
          "severity": "high",
          "message": "Central dependency hub (criticality 0.84) with large blast radius (0.80 components)"
        }
      ],
      "evidence": {
        "metrics": { "criticality_index": 0.84, "final_risk": 0.91 },
        "graph": {
          "dependent_components": ["CI_Controller"],
          "scc_members": []
        },
        "code": { "file_path": "system/database/DB_query_builder.php" }
      }
    }
  ]
}
```

**Key checks:**

- Response is sorted by `final_risk` DESC
- No component has more than 5 explanations
- `GET /risk/{run_id}` and `GET /explain/{run_id}` are independent — calling one does not affect the other

---

## §4. Streamlit UI Modal Walkthrough

1. Open `http://localhost:8501`
2. Enter the `Run ID` and click **Query Risk Matrix**
3. The table displays the full detailed risk matrix (14 columns including all structural and behavioral metrics).
4. Below the table, use the **🔍 Explain a Component** select box to choose a CRITICAL component and click **Open →**
5. Modal opens — verify 3 tabs:
   - **📊 Risk Summary**: Structural Risk, Behavioral Factor, Final Risk metrics
   - **🔍 Why Risky**: Explanation bullets grouped by `🏗️ Structural`, `🗄️ Behavioral`, `⚡ Combined`
   - **📄 Evidence**: Dependent components list, SCC members (if cycle), source file path
6. Click **🔍 Explain** on a LOW-risk component — confirm no HIGH-severity explanations appear

---

## §5. Edge Cases to Check

| Scenario                   | Expected                                                         |
| -------------------------- | ---------------------------------------------------------------- |
| Component has zero metrics | No high/medium explanations                                      |
| Component in a cycle       | `cycle_risk` rule fires, SCC members appear in Evidence tab      |
| No behavioral data         | Behavioral/combined rules don't fire                             |
| Graph JSON missing         | Evidence tab shows "No inbound dependencies detected" gracefully |
