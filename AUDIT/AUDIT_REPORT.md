# Deep Architectural & UX Audit Report
## Strata Modernization Advisory System

This document contains a highly critical, logic-level assessment of the Strata repository against the foundational requirements defined in `IMPORTANT.md` and `IMPORTANT2.md`. 

While the system successfully extracts metrics and renders views, a deep inspection of the backend heuristics and frontend UX flow reveals that **the platform is currently an elaborate data dashboard, not a true Modernization Decision Support System.**

---

## 1. The UX and Pipeline Failure (`IMPORTANT2.md`)

The primary directive of `IMPORTANT2.md` was: *"If I removed every table from this page, would the page still be useful? If the answer is no, the page is data-centric. Not decision-centric."*

**Verdict: The majority of the system fails this test.**

### A. Static, Data-Centric "Insights"
While the UI uses the requested `METRIC → INTERPRETATION → EVIDENCE → RECOMMENDATION` layout, the actual content of these blocks is superficial. 
*   In `risk_audit.py` and `boundary_intelligence.py`, the "Interpretation" blocks are static strings that merely interpolate table counts (e.g., `f"{critical_count} files are classified as CRITICAL"`).
*   If you remove the data table from these pages, the user is left with a generic paragraph explaining what "Cyclomatic Complexity" is, rather than receiving specific guidance on what to do next. The system is showing *information*, not providing *guidance*.

### B. Broken Mental Context Pipeline
The spec explicitly demands a workflow where a user can click:
`Risk → View Evidence → View Recommendation → Add To Modernization Plan → Export Plan` without changing mental context.
*   **Current State:** Pages are entirely stateless and isolated. A user viewing a massive God Object in the `Monolith Navigator` cannot click it to simulate its extraction or add it to a roadmap. 
*   The sidebar organizes the pages linearly, but the *data* does not flow. The user must manually navigate between disconnected tables.

### C. The 1000+ Files Problem
The system attempts to solve this via PyVis graphs and Streamlit tables. However, progressive disclosure (Drill-Down Design) is missing. 
*   `risk_audit.py` renders a single flat `st.dataframe` containing every file.
*   There is no native "System Level → Module Level → Component Level → File Level" click-through drill-down as specified.

---

## 2. Logic-Level Deficiencies (Backend Heuristics)

The backend services powering the "Intelligence" are relying on superficial metrics rather than deep architectural analysis.

### A. Superficial Advisory Logic (`AdvisoryService.py`)
The `Modernization Decision Engine` relies on highly reductive, hardcoded `if/else` logic to generate strategies.
*   It clusters "Contexts" simply by looking at the first folder directory (`if len(parts) > 2: ctx_name = parts[2]`), entirely defeating the purpose of AST-based Bounded Context inference.
*   The strategy output (`Option A, B, C`) is decided by rudimentary thresholding (e.g., `if m["avg_mi"] < 40 and m["avg_cc"] > 10: return "REWRITE"`). This is not an expert system; it is a basic calculator. 

### B. Weak Candidate Ranking
While `candidate_ranker.py` and the `Extraction Simulator` exist, they lack dynamic intelligence. The "Algorithmic Verdict" is a static string selection based on arbitrary metric cutoffs (e.g., `if impact.interface_complexity >= 15`). It lacks the semantic understanding required to provide true advisory context.

---

## 3. Artifact System Failure (`IMPORTANT.md`)

The requirement stated: *"You need two artifact families: human artifacts and machine artifacts... A dedicated page for downloads and exports."*

**Verdict: The artifact system is functionally incomplete and structurally disorganized.**

### A. Missing Dedicated Artifact Center
There is no `Artifact Center` page in the Level 1 Sidebar Navigation. Artifacts are currently hidden within tabs inside the `Executive Roadmap` page, heavily violating the UX specification.

### B. Missing Required Machine Artifacts
The most critical interoperability artifacts are completely absent:
*   **SARIF Export:** Missing. Cannot integrate findings into GitHub Code Scanning.
*   **Rector-ready Configs:** Missing. The system does not output `rector.php` upgrade paths.
*   **Deptrac-style Layer Rules:** Missing. The layer analysis does not export to `deptrac.yaml`.

### C. Mediocre Existing Artifacts
The artifacts that *do* exist are poorly formatted:
*   The `Roadmap MD` is a simple string concatenation in `report_service.py` that dumps high-level stats. It is not a prioritized, phase-by-phase execution plan.
*   The `AI Chunks` are generic strings injected with variables, lacking the deep schema context required for LLM RAG pipelines.

---

## 4. Upgrade Roadmap: The Path to "Consultant-Grade" Software

To elevate Strata from a "Data Dashboard" to a true "Modernization Advisory System", the following architectural upgrades are required:

### Phase 1: Rebuild the Artifact Engine & Hub
1.  **Create `/views/artifact_center.py`:** A dedicated Level 1 Sidebar page that centralizes all exports.
2.  **Implement SARIF Builder:** Map the `ComponentRisk` and `Security Sink` outputs into a valid JSON SARIF v2.1.0 schema so users can load findings into standard CI/CD tooling.
3.  **Refactoring Generators:** Build specific exporters for `deptrac.yaml` (using the detected `Layered Structure` edges) and `rector.php` (targeting the specific patterns found in `Legacy Intelligence`).

### Phase 2: Implement True Drill-Down UX Pipeline
1.  **Interactive Pipelines:** Replace massive flat `st.dataframe` tables with hierarchical expanders. A user must be able to click `Auth Module` → See Risks → Click `Add to Plan`. 
2.  **State Management:** Use `st.session_state` to carry selected components across pages. Clicking a node in the topology graph should allow the user to immediately "Simulate Extraction" in the simulator without manually re-typing the FQN.

### Phase 3: Deepen the Heuristics Engine
1.  **Semantic Clustering:** Rewrite `AdvisoryService._group_by_context()` to use the actual `scc_size` (Strongly Connected Components) and `betweenness` centrality from the NetworkX graph, rather than just splitting file path strings.
2.  **Dynamic Recommendations:** Use LLM synthesis or much deeper deterministic rule-trees to explain *why* a cycle is bad based on the actual node names involved, rather than just printing `"High coupling detected"`.

### Phase 4: Implement "Tell Me What Matters" Mode
1.  On the Dashboard, implement a "Analyze Modernization Risks" button that bypasses tables entirely and outputs a conversational, top-down strategy report dynamically generated from the worst architectural chokepoints.
