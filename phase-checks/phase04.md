Perfect. Now we move into **Phase 4 as a serious system expansion**, not just “add SQL detection”.

This is where your system transitions from:

> **Structural Risk Analyzer → Context-Aware Modernization Intelligence Engine**

I’ll give you a **code-level blueprint**, strict **phase boundaries**, **what NOT to miss**, and **real exit criteria**.

---

# 📊 PHASE 4 — BEHAVIORAL INTELLIGENCE (DATA INTERACTION LAYER)

---

# 🎯 CORE OBJECTIVE

Introduce **data mutation awareness** into the system by:

* Detecting database write operations
* Extracting table interactions
* Expanding graph to heterogeneous model
* Computing behavioral metrics
* Integrating into risk model (without breaking Phase 3)

---

# 🚫 PHASE 4 STRICT BOUNDARIES

## ❌ MUST NOT DO

* No extraction ranking
* No service decomposition
* No clustering
* No microservice suggestions
* No LLM usage
* No UI over-complexity
* No performance optimization (Phase 7)

---

## ✅ MUST DO

* SQL + pattern detection
* Table node creation
* Class → Table edges
* Behavioral metrics
* Risk amplification (multiplicative)

---

# 🧠 PHASE 4 SYSTEM ARCHITECTURE

---

## 🧱 New Domain Modules

```text
domain/
  behavior/
    sql_detector.py
    orm_detector.py
    table_extractor.py
    write_analyzer.py
    behavioral_metrics.py

  models/
    node_type.py  (extend)
    edge_type.py  (extend)
```

---

## 🔗 Graph Model Extensions

### NodeType

```python
class NodeType(Enum):
    CLASS = "class"
    METHOD = "method"
    TABLE = "table"
```

---

### EdgeType

```python
class EdgeType(Enum):
    METHOD_CALL = "method_call"
    INHERITS = "inherits"
    WRITES = "writes"
```

---

# 🧠 PIPELINE FLOW (CRITICAL)

```text
PHP Files
   ↓
Parser (existing)
   ↓
SQL + ORM Detection (NEW)
   ↓
Table Extraction
   ↓
Graph Expansion (CLASS → TABLE)
   ↓
Behavioral Metrics
   ↓
Risk Amplification
   ↓
Persistence
   ↓
API
   ↓
UI
```

---

# 🔍 STEP-BY-STEP IMPLEMENTATION

---

# 1️⃣ SQL + ORM DETECTION ENGINE

## File: `sql_detector.py`

### Responsibilities:

* Detect raw SQL queries
* Identify write operations
* Extract query strings

---

### Core Patterns

```python
WRITE_KEYWORDS = ["INSERT INTO", "UPDATE", "DELETE FROM"]
```

---

### Detection Example

```python
def detect_sql_queries(code: str) -> List[str]:
    queries = []
    for line in code.splitlines():
        if any(keyword in line.upper() for keyword in WRITE_KEYWORDS):
            queries.append(line)
    return queries
```

---

## File: `orm_detector.py`

### Detect:

* `$model->save()`
* `Model::create()`
* `$db->table('users')->update()`

---

### Example

```python
ORM_PATTERNS = [
    r"\->save\(",
    r"::create\(",
    r"->update\("
]
```

---

# 2️⃣ TABLE EXTRACTION

## File: `table_extractor.py`

### Responsibilities:

Extract table names from SQL.

---

### Example

```python
def extract_table_name(query: str) -> Optional[str]:
    match = re.search(r"(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)", query, re.IGNORECASE)
    if match:
        return match.group(2)
    return None
```

---

# 3️⃣ WRITE ANALYZER

## File: `write_analyzer.py`

### Responsibilities:

* Map class → tables
* Aggregate writes per class

---

### Output Example

```python
{
  "UserController": ["users", "orders"],
  "OrderService": ["orders"]
}
```

---

# 4️⃣ GRAPH EXPANSION

## CRITICAL STEP

Modify existing graph builder.

---

### Add TABLE nodes

```python
graph.add_node(
    table_name,
    type=NodeType.TABLE.value
)
```

---

### Add WRITES edges

```python
graph.add_edge(
    class_name,
    table_name,
    type=EdgeType.WRITES.value
)
```

---

## ⚠️ IMPORTANT

* DO NOT mix edge types blindly in metrics
* Ensure graph supports **edge filtering (from Phase 2 fix)**

---

# 5️⃣ BEHAVIORAL METRICS

## File: `behavioral_metrics.py`

---

### 1️⃣ Write Intensity

```python
write_intensity[class] = number_of_writes
```

Normalize later.

---

### 2️⃣ Table Centrality

```python
table_centrality[table] = number_of_classes_writing
```

---

### 3️⃣ Shared Table Pressure

```python
shared_pressure = count(classes writing same table)
```

---

# 🧠 WHY THESE MATTER

* High write intensity → volatile component
* Shared tables → coupling via data
* Table centrality → DB bottleneck

---

# 6️⃣ RISK INTEGRATION (CRITICAL DESIGN)

---

## DO NOT TOUCH Phase 3 logic

You extend it.

---

## Final Risk Formula

```python
risk_final = structural_risk * (1 + behavioral_factor)
```

---

## Behavioral Factor Example

```python
behavioral_factor =
    0.5 * normalized_write_intensity +
    0.5 * normalized_table_dependency
```

Clamp:

```python
behavioral_factor = min(1.0, behavioral_factor)
```

---

## 🔥 IMPORTANT

* Behavioral factor must NOT dominate structural risk
* Keep amplification bounded

---

# 7️⃣ DATABASE CHANGES

---

## New Table: `component_behavior`

```sql
component_name TEXT
write_intensity REAL
table_dependencies INTEGER
shared_table_pressure REAL
```

---

## Extend risk table:

```sql
behavioral_factor REAL
final_risk REAL
```

---

# 8️⃣ API EXTENSION

---

## Endpoint:

```http
GET /risk/{run_id}
```

---

## Response:

```json
{
  "component": "UserController",
  "structural_risk": 0.6,
  "behavioral_factor": 0.5,
  "final_risk": 0.9
}
```

---

# 9️⃣ UI (STREAMLIT)

---

Add columns:

```text
Component | Structural Risk | Behavioral Factor | Final Risk
```

Optional:

* highlight high DB writers
* show tables per component

---

# 🔟 CRITICAL PITFALLS (DO NOT SKIP)

---

## ❌ 1. SQL Detection Overfitting

Do NOT assume perfect SQL parsing.

Goal:

> detect signals, not correctness

---

## ❌ 2. Table Name Noise

Handle:

* aliases
* lowercase/uppercase
* backticks

---

## ❌ 3. Graph Pollution

Do NOT:

* create duplicate table nodes
* mix string inconsistencies

Normalize:

```python
table = table.lower()
```

---

## ❌ 4. Risk Explosion

If behavioral factor > 1 → risk breaks

Always clamp.

---

## ❌ 5. Breaking Phase Separation

DO NOT:

* recompute structural metrics
* mix new logic into Phase 3 modules

---

# 🧪 PHASE 4 EXIT CRITERIA (STRICT)

---

## ✔ Detection

* SQL write detection works on real PHP samples
* ORM patterns detected

---

## ✔ Graph

* TABLE nodes exist
* WRITES edges correct
* No duplicate nodes

---

## ✔ Metrics

* write_intensity computed
* table_centrality computed
* values normalized

---

## ✔ Risk

* final risk differs from structural risk when writes exist
* no overflow (>1)
* deterministic across runs

---

## ✔ API

* returns behavioral + final risk
* consistent output schema

---

## ✔ UI

* displays behavioral factor
* sorted correctly

---

## ✔ Edge Cases

* no SQL → system stable
* many tables → no crash
* mixed SQL styles → partial detection works

---

# 🧠 FINAL STRATEGIC STATE AFTER PHASE 4

Your system becomes:

> **Context-Aware Risk Engine for Legacy PHP Systems**

Now it understands:

* structure
* * data mutation

This is a **major leap toward modernization intelligence**.

---

# 🚀 NEXT (AFTER THIS)

After Phase 4:

👉 Phase 4.5 — Explanation Engine
👉 Then Phase 5 — Extraction Intelligence

---

# 🎯 FINAL CHECK

Before you start coding Phase 4:

Answer this (important for implementation precision):

👉 Do you want SQL detection to operate:

A) Line-by-line scanning
B) Tokenized / preprocessed code blocks (slightly smarter, still lightweight)

I’ll refine the detector design based on that.
