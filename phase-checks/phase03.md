Good. Now we will **treat Phase 3 like a system design review**, not just a coding task.

You already locked the **phase boundaries** in your plan , so now the goal is to understand **exactly what Phase 3 must and must not do**, and how it should be **implemented like a real product module**.

We will break Phase 3 into **5 critical discussions**:

1. What Phase 3 *really introduces* (intelligence shift)
2. Exact **inputs and outputs**
3. Internal **module architecture**
4. Mathematical **risk formulation strategy**
5. Implementation **checklist and pitfalls**

---

# 1️⃣ What Phase 3 Actually Introduces

Up to Phase 2 you built:

> **Structural observation**

Your system observes the architecture:

* nodes
* edges
* centrality
* coupling
* cycles
* reachability

But the system **does not yet interpret anything**.

Phase 3 introduces:

> **Structural interpretation**

Meaning:

Instead of saying:

```
Class A betweenness = 0.48
```

You say:

```
Class A is structurally risky because:
- it is highly central
- it has high blast radius
- it participates in cycles
```

So Phase 3 converts:

```
Metrics → Architectural meaning
```

This is the **first decision-support layer** of the system.

---

# 2️⃣ Phase 3 Boundaries (Extremely Important)

From your execution plan , Phase 3 **must operate only on Phase 2 outputs**.

So the inputs are strictly:

### Inputs

From Phase 2 database:

For each component:

```
component_name
in_degree
out_degree
betweenness
blast_radius
scc_size
coupling_score
```

Nothing else.

---

### Forbidden Inputs

Phase 3 **cannot access**:

* SQL queries
* database writes
* tables
* runtime data
* method bodies
* parsing logic
* graph reconstruction

All of those belong to **later phases**.

---

### Outputs

For each component Phase 3 produces:

```
normalized_features
derived_structural_features
risk_score
risk_classification
```

Example:

```
UserController

normalized_betweenness: 0.72
normalized_blast_radius: 0.61
criticality_index: 0.44
instability: 0.63
cycle_flag: 1

risk_score: 0.78
risk_level: HIGH
```

This output is stored in DB and returned via `/risk/{run_id}`.

---

# 3️⃣ Phase 3 System Architecture

This is how a **clean implementation** should look.

```
domain/
   risk/
      feature_normalizer.py
      structural_features.py
      risk_model.py
      risk_classifier.py

services/
   risk_engine.py

infrastructure/
   persistence/
      risk_repository.py
```

Flow:

```
Phase2 metrics
        │
        ▼
Feature Normalizer
        │
        ▼
Structural Feature Engineering
        │
        ▼
Risk Composition Engine
        │
        ▼
Risk Classifier
        │
        ▼
Persistence + API
```

This separation is **very important** for Phase 6 experiments.

---

# 4️⃣ Feature Normalization Strategy

Metrics must be normalized so different systems remain comparable.

Typical methods:

### Option 1 — Min-Max

```
x_norm = (x - min) / (max - min)
```

Good for:

* centrality
* blast radius
* degree

---

### Option 2 — Relative Rank Percentile

```
rank / total_nodes
```

Better for skewed distributions like betweenness.

---

### Recommended Strategy

Use:

```
min-max normalization
```

inside each run.

Because Phase 3 operates **per analyzed system**.

---

# 5️⃣ Structural Feature Engineering

Now we create **architectural signals**.

These are **derived indicators**.

### 1️⃣ Structural Criticality Index

```
criticality = normalized_betweenness * normalized_blast_radius
```

Meaning:

A component is critical if:

* many paths pass through it
* it affects many downstream components

This is the **chokepoint indicator**.

---

### 2️⃣ Instability Indicator

Classic architecture metric:

```
instability = out_degree / (in_degree + out_degree)
```

Meaning:

High instability means:

> component depends on many others.

These components are **change-sensitive**.

---

### 3️⃣ Cycle Vulnerability

```
cycle_flag = 1 if scc_size > 1 else 0
```

Meaning:

Component participates in **cyclic coupling**.

Cyclic components are harder to extract.

---

### 4️⃣ Coupling Pressure

Example:

```
coupling_pressure = normalized_in_degree + normalized_out_degree
```

Meaning:

Component heavily integrated with system.

---

# 6️⃣ Risk Composition Model

Now we combine the indicators.

You **must avoid naive weighted sums**.

Use a structured model.

Example:

```
BaseRisk =
  0.35 * criticality
+ 0.25 * instability
+ 0.20 * coupling_pressure
+ 0.20 * cycle_flag
```

Then clamp:

```
risk = min(1.0, BaseRisk)
```

This ensures risk ∈ [0,1].

---

# 7️⃣ Risk Classification

Convert numeric risk to categories.

Recommended:

```
0.0 - 0.25  → LOW
0.25 - 0.50 → MEDIUM
0.50 - 0.75 → HIGH
0.75 - 1.00 → CRITICAL
```

OR percentile-based classification.

Percentile is stronger for research.

---

# 8️⃣ Database Changes

Add columns:

```
risk_score REAL
risk_level TEXT

criticality_index REAL
instability REAL
cycle_flag INTEGER
coupling_pressure REAL
```

These allow **Phase 6 ablation studies**.

---

# 9️⃣ API Contract

Endpoint:

```
GET /risk/{run_id}
```

Response example:

```
{
  "components": [
    {
      "name": "UserController",
      "risk_score": 0.78,
      "risk_level": "HIGH",
      "criticality_index": 0.44,
      "instability": 0.63,
      "cycle_flag": 1
    }
  ]
}
```

---

# 🔟 UI Implementation (Minimal)

Streamlit should display:

Table:

```
Component | Risk | Criticality | Instability | Cycle
```

Sorted by risk descending.

No graph visualization yet (Phase 8).

---

# 1️⃣1️⃣ Critical Questions Before Coding Phase 3

You must answer these first.

### Q1

Should risk be **system-relative (per run)** or **absolute**?

Correct answer:

> system-relative normalization

---

### Q2

Should risk model coefficients be:

A) Hard-coded
B) Config-driven

Correct choice:

> **config-driven**

So Phase 6 can perturb them.

---

### Q3

Should derived features be stored or computed on demand?

Correct answer:

> **stored**

This allows experiments later.

---

# 1️⃣2️⃣ Phase 3 Exit Criteria (Realistic)

Before tagging `v0.4-risk-framework`:

You must prove:

1️⃣ Risk scores stable across repeated runs
2️⃣ Risk ∈ [0,1] for all components
3️⃣ Top-risk components logically match graph intuition
4️⃣ Risk model coefficients documented
5️⃣ Risk API works
6️⃣ UI table renders correctly

---

# 🧠 Final Strategic Reality Check

After Phase 3 your system becomes:

> **Structural Risk Analyzer for Legacy PHP Systems**

Not yet modernization engine.

But **now it actually tells engineers where danger lies.**

That’s a **huge jump in capability**.

---

If you want, the **next discussion (very important)** should be:

**The exact mathematical design of the Phase 3 risk model.**

Because if we design that carefully, your system will feel **10× more intelligent** than typical FYP analyzers.
