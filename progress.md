

# Strata — Critical Capability Assessment

## Overall Verdict: ~65% Capability Complete

The project has **impressive architectural discipline** and a **deep, layered intelligence pipeline** (Phases 0–5) that is mostly real, testable, and coherent. However, it has **three critical weaknesses** that prevent it from being a defensible research artifact or production tool:

1. **The PHP parser is regex-based, not AST-based.** This undermines the validity of every downstream metric.
2. **The Phase 6 evaluation runner is broken** (model/schema mismatches, missing `metrics_service`).
3. **Phases 7–8 (performance, visualization, polish) are essentially absent.**

---

## Phase-by-Phase Capability Audit

| Phase | Claimed Status | Actual Capability | Notes |
|-------|---------------|-------------------|-------|
| **0 — Foundation** | Complete | **~95%** | Docker, DB, API, logging, tests all solid. Clean Architecture boundaries are respected. |
| **1 — Vertical Slice** | Complete | **~90%** | File scan → parse → graph → persist → API → UI works end-to-end. |
| **2 — Structural Graph Intelligence** | Complete | **~90%** | [MetricCalculator](cci:2://file:///home/dio/Documents/strata/domain/services/metric_calculator.py:11:0-141:28) is robust: degrees, betweenness, SCC, blast radius, reachability, fan ratios, density. Timeout guard for large graphs. Deterministic JSON. |
| **3 — Risk Framework** | Complete | **~85%** | Normalization, feature engineering, weighted risk model, classifier all implemented and tested. Weights are overridable for experiments. |
| **4 — Behavioral Intelligence** | Complete | **~80%** | Tokenized SQL detection, table nodes, `WRITES` edges, behavioral amplification formula all exist. Regex-based detection is pragmatic but brittle. |
| **4.5 — Explainability** | Complete | **~85%** | 8 deterministic rules, [RiskReasoner](cci:2://file:///home/dio/Documents/strata/domain/explanation/reasoner.py:13:0-74:73), `EvidenceBuilder`, modal UI with 3 tabs. Well-designed and tested. |
| **5 — Extraction & Simulation** | Complete | **~80%** | Cluster builder (SCC, table-coupled, density, risk-targeted), scorer, conflict resolver, simulator, impact analyzer, ranker all implemented. |
| **6 — Evaluation** | Claimed Complete | **~30%** | Classification metrics, ranking stability, ablation/sensitivity experiment *code* exist. **But [experiment_runner.py](cci:7://file:///home/dio/Documents/strata/evaluation/runners/experiment_runner.py:0:0-0:0) is broken** (imports non-existent `Run` model and `metrics_service`). The UI page references it. Charts are generated but the orchestrator won't run. |
| **7 — Performance** | Not Started | **~5%** | Betweenness skips graphs >2000 nodes. No parallel parsing, no caching, no profiling. |
| **8 — Demo & Finalization** | Not Started | **~20%** | Streamlit UI is functional but unpolished. **No graph visualization.** Export is raw JSON only. |

---

## What's Actually Strong

- **Clean Architecture is real.** Dependency flow is correct: `domain/` has zero FastAPI/SQLite imports. `api/` is thin. `application/` orchestrates.
- **The risk pipeline is academically sound.** Deterministic, explainable, bounded, with configurable weights and thresholds. Ablation-ready design.
- **Test coverage for core logic is good.** Unit tests for metrics, risk, explanation, extraction, behavior all exist.
- **The extraction engine is surprisingly sophisticated.** Proxy-service simulation, cluster conflict resolution, and algorithmic verdicts are all implemented.

---

## Critical Gaps & What's Left

### 🔴 High Priority (Blocks Academic/Production Credibility)

1. **Replace regex parser with a real PHP AST parser**
   - [infrastructure/parser_bridge.py](cci:7://file:///home/dio/Documents/strata/infrastructure/parser_bridge.py:0:0-0:0) uses naive regex (`_CLASS_PATTERN`, `_METHOD_PATTERN`, etc.). It will miss dynamic calls, closures, traits in complex layouts, and cannot resolve aliases.
   - **Required:** Integrate `php-ast` or `nikic/php-parser` via a subprocess bridge, or use a Python PHP parser if available. The docs (`02.SCHEMA_AST_CANONICAL.md`) imply AST was intended.

2. **Fix the Phase 6 evaluation runner**
   - `@/home/dio/Documents/strata/evaluation/runners/experiment_runner.py:7-11` imports [Project](cci:2://file:///home/dio/Documents/strata/infrastructure/persistence/models.py:4:0-9:69) and `Run` from `infrastructure.persistence.models`, but the actual models define [Project](cci:2://file:///home/dio/Documents/strata/infrastructure/persistence/models.py:4:0-9:69) and [AnalysisRun](cci:2://file:///home/dio/Documents/strata/infrastructure/persistence/models.py:11:0-22:49) — no `Run` class exists.
   - It imports `application.services.metrics_service` which **does not exist anywhere in the codebase**.
   - **Required:** Align runner imports with actual models, wire it to the real [AnalysisService](cci:2://file:///home/dio/Documents/strata/application/services/analysis_service.py:13:0-112:19)/[MetricCalculator](cci:2://file:///home/dio/Documents/strata/domain/services/metric_calculator.py:11:0-141:28) pipeline, or build a lightweight in-memory orchestrator that doesn't depend on missing services.

3. **Populate or generate ground truth datasets**
   - `evaluation/ground_truth/` has only 1 file. The evaluation pipeline needs labeled PHP projects with known extraction boundaries to compute meaningful Precision/Recall/F1.

### 🟡 Medium Priority (Significantly Improves Utility)

4. **Add interactive graph visualization to the UI**
   - The frontend shows tables and metrics, but **no visual dependency graph**. Engineers need to *see* the monolith structure.
   - Use `st.graphviz_chart`, `pyvis`, or `plotly` network graphs.

5. **Implement performance hardening (Phase 7)**
   - Parallel file parsing (`multiprocessing` or `ThreadPoolExecutor`)
   - Betweenness centrality approximation for large graphs
   - SQLite write batching optimization
   - Graph caching between runs

6. **Add export functionality beyond raw JSON**
   - PDF report generation
   - CSV/Excel export of risk matrices
   - Graph image export

### 🟢 Lower Priority (Polish & Robustness)

7. **Add integration/E2E tests**
   - Currently only [test_reproducibility.py](cci:7://file:///home/dio/Documents/strata/tests/test_reproducibility.py:0:0-0:0) tests the live API, and it's a standalone script.
9. **Add method-level granularity (future roadmap)**
   - Currently edges are class-to-class. Method-level call graph resolution is required for precise extraction.

---

## 🗺️ Master Product Roadmap: From Intelligence to Extraction (The v1.0 Journey)

This roadmap defines the path to a **finished, competition-winning product**. It is divided into logical modules that build upon the Centralized Source of Truth (CSOT).

### Module 1: The Intelligence Engine (Current Focus)
**Goal**: Transform raw code into a high-fidelity knowledge graph.

#### Phase 1.1: AST Extraction & Bridge
- Implement `nikic/php-parser` sidecar.
- Extract nodes for PHP 7.x-8.3 (Union Types, Attributes, Enums).
- **Exit Criteria**: 100% grammar coverage on "Legacy Monolith" test suite.

#### Phase 1.2: Semantic Resolution
- Resolve FQNs for all class references.
- Implement Trait flattening and Interface implementation mapping.
- **Exit Criteria**: Every symbol in the project has a deterministic, hash-based ID.

#### Phase 1.3: Centralized Source of Truth (CSOT)
- Design the **Strata Canonical Schema** (Nodes: File, Class, Method, Table; Edges: CALLS, WRITES, INHERITS).
- Optimize SQLite persistence for recursive "Blast Radius" queries.
- **Exit Criteria**: Sub-second query response for complex dependency traversals.

---

### Module 2: The Transformation & Refactoring Engine (Action Layer)
**Goal**: The product must not only *see* the problem but *fix* it.

#### Phase 2.1: Transformation Recipes
- Develop a library of deterministic refactoring "Recipes" (Extract Class, Encapsulate Field, Move Method).
- Use LLM-guided intelligence to generate new, PSR-12 compliant PHP code for extracted modules.
- **Exit Criteria**: Automated generation of valid, lint-checked PHP code for a 5-class extraction candidate.

#### Phase 2.2: Automated Dependency Cutting
- Implement the "Edge Severing" logic: Automatically update `use` statements and namespaces.
- Generate "Proxy Bridges" to maintain connectivity between the monolith and the newly extracted service.
- **Exit Criteria**: Successful automated extraction of a "Utility" service with zero manual intervention.

#### Phase 2.3: Safety & Regression Engine
- Implement a "Pre-Refactoring Simulation" that verifies the new graph state before any code is written.
- Auto-generate PHPUnit tests for the extracted module based on its original call sites in the CSOT.
- **Exit Criteria**: 100% test pass rate on a simulated extraction run.

---

### Module 3: The Immersive UI & Strategic Dashboard (UX Layer)
**Goal**: Create a "WOW" factor. The product must feel like a state-of-the-art laboratory.

#### Phase 3.1: 3D Force-Directed Graph Navigator
- Implement an interactive 3D graph (using `Cytoscape` or `Three.js`) that allows users to fly through their codebase.
- Add "Heatmap Overlays": Color-code nodes by Complexity, Risk, or "Blast Radius".
- **Exit Criteria**: Smooth navigation of a 10,000-node graph at 60fps.

#### Phase 3.2: Refactoring Simulator Dashboard
- Build a "What-If" workbench where users can drag nodes to "New Service" buckets and see risk scores update live.
- Implement a "Before/After" side-by-side comparison of architectural health metrics.
- **Exit Criteria**: Real-time recalculation of SCC and Centrality metrics on user interaction.

#### Phase 3.3: Executive Intelligence Exports
- Automated generation of "Strategic Roadmap" PDF reports for technical leaders.
- Export of "Extraction Plans" in Jira/Markdown formats.
- **Exit Criteria**: Professional, white-labeled PDF report generation with embedded charts.

---

### Module 4: Operational Excellence & Enterprise Readiness (Scale Layer)
**Goal**: Ensure the product is robust, fast, and ready for massive codebases.

#### Phase 4.1: Parallel & Incremental Intelligence
- Parallelize file parsing using `multiprocessing` to saturate every CPU core.
- Implement hash-based incremental analysis: Only analyze what changed since the last git commit.
- **Exit Criteria**: Analysis of a 1,000,000 LOC codebase in under 5 minutes.

#### Phase 4.2: CI/CD & Headless Integration
- Develop the `strata` CLI tool for integration into build pipelines.
- Create "Risk Gate" functionality: Fail a build if a PR introduces a circular dependency or a high-risk architectural flaw.
- **Exit Criteria**: Successful deployment of Strata as a GitHub Action.

#### Phase 4.3: Security & Isolation
- Implement sandboxed parsing to protect against malicious code in the target project.
- Secure the API layer with robust authentication for multi-user environments.
- **Exit Criteria**: Passing a basic internal security and isolation audit.

---

### Module 5: Final Validation & GTM (Success Layer)
**Goal**: Victory in competition and academic defense.

#### Phase 5.1: Ground Truth Benchmarking
- Build a curated library of 10 "Gold Standard" projects with manually verified extraction boundaries.
- Benchmark Strata's algorithmic verdicts against human expert recommendations.
- **Exit Criteria**: >90% Precision/Recall on the Gold Standard dataset.

#### Phase 5.2: Documentation & Demo Mastery
- Create "Strata University": A series of guided on-boarding interactive tutorials.
- Produce a high-production-value demo video showcasing the "Monolith to Microservice" transition in under 2 minutes.
- **Exit Criteria**: Final v1.0 release tagged and documented for public distribution.

---

## 💎 Final Checklist for a "Superb" Finished Product

- [ ] **Deterministic Results**: 100% reproducibility across all analysis runs.
- [ ] **Zero-Config Onboarding**: Point it at a directory and click "Analyze".
- [ ] **Visual Dominance**: The graph visualization must be the "Hero" feature.
- [ ] **Actionable Outputs**: The product must provide *code*, not just *advice*.

**Target Release Date**: 6 Weeks from Milestone 1.0  
**Current Status**: *Module 1 Execution in Progress*