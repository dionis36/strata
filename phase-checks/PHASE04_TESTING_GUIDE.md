# Strata: Phase 4 Testing Guide

This guide validates the **Phase 4 Behavioral Intelligence Layer**. Phase 4 introduces automated detection of raw database mutations (SQL writes, ORM updates), expands the dependency graph to include `TABLE` nodes, computes behavioral intensity metrics, and mathematically amplifies the base structural risk.

**What Phase 4 proves:**

```
Tokenized String Extraction → SQL/ORM Detection → Graph Expansion [TABLE nodes, WRITES edges] → Behavioral Factor Amplification → Final Risk Scaling
```

---

## §1. Environment Readiness

Ensure you are operating against the legacy benchmark (CodeIgniter 3).

```bash
# Wipe state and reboot the environment
./scripts/reset_environment.sh
docker compose up --build -d
```

---

## §2. Tokenized Engine Unit Tests

Phase 4 avoids the high cost of ASTs by using a tokenized sanitizer. Run the test suite to ensure the sanitizer correctly ignores SQL keywords inside PHP comments:

```bash
# Run tests natively within the API container
docker compose exec api python3 tests/test_behavioral_engine.py
```

**What this validates:**

1. **Comment Resilience**: A commented out `// UPDATE users...` line does not erroneously register as a component write intensity.
2. **Table Normalization**: `"Orders"`, `` `Orders` ``, and `orders` all map safely to `orders` to prevent graph splintering.
3. **ORM Detection**: Automatically supports Model `save()`, `create()`, and active-record `update()` chains.
4. ** Mathematical Integrity**: The Risk Base multiplier enforces a strict upper limit. A max scale `1.0` modifier cannot push `[0,1]` Base Risk beyond `[0,1]` Final Risk.

---

## §3. Manual API Payload Verification

Check that the new data columns are correctly propagated to the response interface.

1. Open **http://localhost:8000/docs**
2. Send an Analysis on `test_project_2` or `/data/test_benchmark/system`.
3. Execute `GET /risk/{run_id}`.

**Expected Shape Update:**

```json
{
  "name": "UserController",
  "type": "class",
  "risk_score": 0.88,
  "behavioral_factor": 0.5,
  "final_risk": 1.0,
  "risk_level": "CRITICAL"
}
```

> **Key check:** Ensure `final_risk` never surpasses `1.0` and the array is naturally sorted descending by `final_risk`.

---

## §4. Web UI Validation (Behavioral Amplification Matrix)

Strata's Streamlit frontend now exposes the Behavioral metrics to engineers natively.

1. Open **http://localhost:8501**, target an inspection `Run ID`.
2. Inspect the **Risk Matrix**.

**Behavior to confirm:**

- A new column **"Behavioral Factor"** appears.
- A new column **"Final Risk"** dominates the sort ordering.
- If a component does no database writes, its Behavioral Factor is `0.0`, resulting in its Final Risk being exactly identical to its Structural Risk (`Risk Score`).
- If a component touches many tables (e.g. `CI_DB_driver`), its Behavioral Factor acts as a modifier (e.g. `0.70`), pulling its Final Risk upward toward `1.0` (CRITICAL).

---

## §5. Real-World Assessment

By testing against the `test_benchmark/system` CodeIgniter 3 workload, you will notice:

- Components like `core/Model` or `database/DB_query_builder` automatically get augmented by high Table Interactions.
- Strict "view" logic classes stay at their base structural risk value.
