# Strata: Modernization Intelligence Platform

![Version](https://img.shields.io/badge/version-1.0.0--enterprise-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)

**Strata** is an enterprise-grade platform designed to de-risk the transformation of legacy PHP monoliths into modern, distributed architectures. By converting raw source code into a **Structural Intelligence Graph**, Strata identifies architectural anchors, hidden technical debt, and optimized service seams.

---

##  Core Methodology

Strata moves beyond simple static analysis. It parses Abstract Syntax Trees (AST) and projects them into a **mathematically rigorous model** to detect:
*   **Structural Gravity**: High-centrality nodes that prevent decomposition.
*   **Circular Entanglements**: Tightly coupled clusters (SCCs) that must be extracted together.
*   **Global Pollution**: Side effects from superglobals and mutable shared state.
*   **Modernization Readiness**: Data-driven feasibility scores for extraction.

---

##  System Pillars

The platform is organized into four strategic modules:

### 1. Architectural Discovery
*   **Monolith Navigator**: Deep structural exploration and file classification.
*   **Layered Structure**: Automated inference of UI, Service, and Data layers.
*   **System Topology**: High-level relationship mapping and Bounded Context clustering.

### 2. Intelligence Reports
*   **Database Intelligence**: SQL operation extraction and table ownership mapping.
*   **Runtime & Global State**: Audit of superglobals (`$_SESSION`, `$_POST`) and mutable state.
*   **Legacy PHP Audit**: Expert-system detection of legacy anti-patterns (e.g., `mysql_*`).
*   **Modernization Risk**: Multi-dimensional risk scoring (Structural & Behavioral).

### 3. Strategic Advisory
*   **Modernization Decision Engine**: Rule-based strategy selection (Refactor vs. Strangler).
*   **Extraction Simulator**: Predictive impact analysis and component blast radius.
*   **Strategic Roadmap**: Prioritized modernization timeline and effort estimation.

### 4. Enterprise Reporting
*   **Graphviz/Neo4j Exports**: Visualizing architectural complexity.
*   **AI-Ready Knowledge**: Generating structural context for LLM-assisted refactoring.

---

##  Quick Start

### 1. Bootstrap Environment
Ensure you have Docker and Python 3 installed. Run the automated bootstrap script to check requirements and download legacy benchmarks:

```bash
python3 scripts/setup_fixtures.py
```

### 2. Launch Stack
Spin up the analyzer using Docker Compose:

```bash
docker compose up --build -d
```

### 3. Access Platform
*   **Executive Dashboard (Streamlit)**: [http://localhost:8501](http://localhost:8501)
*   **Interactive API Docs (Scalar)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

##  Documentation

For a detailed walkthrough on setting up test fixtures, running your first analysis, and resetting the environment, see the **[STRATA UP GUIDE](STRATA_UP_GUIDE.md)**.

---
*Developed by the Strata Team*
