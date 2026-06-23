# Strata: Modernization Advisory Suite
## FYP Viva Frontend Presentation Q&A Guide

This guide contains page-by-page supervisor questions and concise, direct answers tailored for your Streamlit UI walkthrough.

---

# Page 1: Executive Dashboard (`dashboard.py`)
### 🔍 Focus: High-level KPIs, Modernization Readiness, Action Center Scan Controller.

#### Q1: What is the "Modernization Readiness Score", and how is it calculated?
*   **Answer**: The Readiness Score (0-100%) represents how prepared the codebase is for modernization. It is calculated by taking the inverse of the average component risk score:
    $$\text{Readiness} = 100 \times (1.0 - \text{Average Component Risk})$$
    A higher percentage indicates a codebase that already uses structured abstractions (namespaces, low coupling, high test coverage) and is ready for automated service extraction.

#### Q2: How does the Action Center prevent redundant scans when a developer clicks "Initialize Deep Scan" multiple times?
*   **Answer**: It uses a SHA256 file-caching mechanism. The backend scanner hashes the binary contents of every PHP file. If the hash matches the record in the SQLite `file_cache` table, the system skips the AST parsing subprocess and loads the cached node/edge metadata. It only parses new or modified files.

---

# Page 2: Monolith Navigator (`monolith_navigator.py`)
### 🔍 Focus: Directory breakdown, Search inventory, OOP Manifest, God Classes (Gravity Wells).

#### Q3: How does the navigator classify code files into architectural roles like "Controller" or "View" dynamically?
*   **Answer**: The `FileClassifier` runs AST pattern matching:
    *   **Controllers**: Classes that extend a base controller class, or files containing routing declarations.
    *   **Views**: Files that contain a UI Entanglement Ratio $> 15\%$ (proportion of HTML echo tokens in AST) and lack heavy class definitions.
    *   **Entry Points**: Scripts located in public directories containing direct procedural execution statements.

#### Q4: What is a "Gravity Well" (God Object) in this view, and what metrics define it?
*   **Answer**: A Gravity Well is a class that accumulates massive responsibilities, attracting dependencies from across the system. The engine flags a component as a God Object if:
    *   **Weighted Method Count (WMC)** $> 50$ (sum of method complexities).
    *   **Lack of Cohesion in Methods (LCOM)** $> 0.8$ (methods operate on disjoint property sets).

---

# Page 3: Layered Structure & System Topology (`layered_architecture.py`)
### 🔍 Focus: Directory trees, PyVis topology graphs, Bounded Context mappings.

#### Q5: How is the Force-Directed Network Graph generated, and what do the node shapes and colors represent?
*   **Answer**: The graph is generated in Python using `NetworkX`, serialized to JSON, and rendered using `PyVis` (vis.js).
    *   **Shapes**: Stars represent God Classes; Diamonds represent Controllers; Squares represent Utilities; Circles represent Entities.
    *   **Colors**: Red indicates high-risk components; blue indicates standard domain classes; orange indicates database table nodes.
    *   **Edges**: Red solid lines are static calls; orange solid lines are direct instantiations; green dashed lines are dependency injections.

#### Q6: How does the "Bounded Context" algorithm group files into logical domains?
*   **Answer**: The domain engine clusters components based on two criteria: physical directory hierarchies (folders) and coupling cohesion. It calculates the **Coupling Ratio**:
    $$\text{Coupling Ratio} = \frac{\text{External Method Calls}}{\text{Internal Method Calls}}$$
    A directory with a low ratio (e.g., $< 0.3$) is highly self-contained and is classified as an independent Bounded Context.

---

# Page 4: Database Intelligence (`database_intelligence.py`)
### 🔍 Focus: CRUD patterns, duplicate query audits, table ownership, Graphviz ERD.

#### Q7: How do you extract SQL table reads/writes and construct the ERD without a live database connection?
*   **Answer**: The PHP AST visitor extracts raw SQL string literals and ORM query builders. The Python `WriteAnalyzer` tokenizes these strings to match keywords like `FROM`, `JOIN`, `INSERT INTO`, and `UPDATE` to isolate table names. The ERD is rendered using Graphviz dot format by mapping tables that share write contexts in the same class.

#### Q8: What is a "Cross-Module Write Conflict," and why is it a critical blocker for microservice migration?
*   **Answer**: A write conflict occurs when two different directories (modules) execute `INSERT` or `UPDATE` queries on the same database table. This blocks microservices because extracting the modules would violate the "Database-per-Service" pattern, requiring shared database schemas or slow distributed transactions (like Sagas).

---

# Page 5: Runtime & Global State (`global_state_intelligence.py`)
### 🔍 Focus: Superglobals (`$_SESSION`, `$_POST`), mutable global state.

#### Q9: Why is tracking PHP superglobals (like $_SESSION, $_POST) critical for refactoring a monolith?
*   **Answer**: Superglobals represent hidden state channels that bypass class methods. If a class relies on `$_SESSION['user_id']` directly rather than accepting a parameter, it cannot be isolated into a stateless service or containerized. Tracing these helps developers refactor global state into formal parameter injections.

---

# Page 6: Legacy PHP Intelligence (`legacy_intelligence.py`)
### 🔍 Focus: PHP Era profiling, framework fingerprinting, deprecated APIs.

#### Q10: How does the framework fingerprinter detect if the legacy project is Joomla, WordPress, or Laravel?
*   **Answer**: The fingerprinter runs static signature checks on the AST definition tree:
    *   **WordPress**: Detects call configurations containing hook functions like `add_action()` or `apply_filters()`.
    *   **Laravel**: Detects namespace usage like `Illuminate\Routing\Controller` or classes extending Eloquent models.
    *   **Joomla/Legacy**: Detects globals like `$mainframe` or direct entry point tokens.

---

# Page 7: Modernization Risk & Security Audit (`risk_audit.py`)
### 🔍 Focus: File Matrix, Maintainability Index, security sink logs.

#### Q11: How is the "Maintainability Index" scored, and how should an architect interpret it?
*   **Answer**: It is scored 0-100 using the Halstead Volume ($V$), Cyclomatic Complexity ($G$), and Lines of Code ($LOC$):
    $$\text{MI} = \max\left(0, \frac{171 - 5.2 \ln(V) - 0.23 G - 16.2 \ln(LOC)}{171} \times 100\right)$$
    *   **$> 65$**: High maintainability (safe to refactor).
    *   **$25\text{--}65$**: Moderate maintainability (requires unit testing).
    *   **$< 25$**: Unmaintainable (rewrite recommended).

#### Q12: What constitutes a "Security Sink" in the vulnerability log?
*   **Answer**: A security sink is an AST execution node that invokes dangerous built-in PHP functions, such as `eval()` (Remote Code Execution), `exec()` (Command Injection), or legacy `mysql_query()` (SQL Injection). The audit flags these as "Critical" if user-controlled input tokens flow into them without dynamic sanitization.

---

# Page 8: Modernization Decision Engine (`decision_engine.py`)
### 🔍 Focus: ROI scatter plot, effort estimation, AI playbooks.

#### Q13: How is the "Modernization ROI" (Return on Investment) calculated on the scatter plot?
*   **Answer**: It is a weighted score combining structural risk and modularity. If a component is highly critical (high betweenness centrality and blast radius) but is relatively easy to extract (low size and low coupling), it has high ROI because resolving its debt brings immediate systemic stability for low effort (a "Quick Win").

#### Q14: What is the difference between the "Extract" and "Strangler Fig" recommendations?
*   **Answer**:
    *   **Extract**: Assigned to cohesive, low-coupling components. They can be immediately moved out of the monolith as microservices.
    *   **Strangler Fig**: Assigned to highly critical, deeply coupled components. They cannot be easily extracted. The strategy is to wrap them in an API facade inside the monolith, routing new features to modern services while slowly strangling the legacy implementation.

---

# Page 9: Extraction Simulator (`extraction_simulator.py`)
### 🔍 Focus: Upstream/Downstream blast radius, To-Be Ghost Graphs, Mermaid flowcharts.

#### Q15: What is the "Ghost Graph" simulation, and how does it help the developer verify a migration path?
*   **Answer**: The simulator dynamically creates a post-extraction model: it deletes the class node from the monolith, inserts a new green "Proxy Service" node, and reroutes all edges. This provides the developer with visual and metric-based evidence of the **Interface Complexity** (cross-calls) and **Data Isolation Difficulty** (shared tables) *before* they write any refactoring code.

#### Q16: Why does the simulator display a "DANGER ZONE" warning if the target component has low test coverage?
*   **Answer**: If test coverage is low (e.g., $< 20\%$), extracting the component is highly risky because there is no automated test suite to guarantee that the behavior of the extracted microservice matches the legacy implementation, increasing the probability of silent regression bugs.

---

# Page 10: Artifact Center (`artifact_center.py`)
### 🔍 Focus: Synthesis status loops, Human vs. Machine Artifacts, Workspace bundles, dynamic config generators.

#### Q17: What is the distinction between "Human" and "Machine" Artifacts in this center?
*   **Answer**: 
    *   **Human Artifacts** (PDF, DOCX, HTML, MD, CSV) are rich, readable, narrative-driven summaries designed for stakeholder reviews, project managers, and architectural presentations.
    *   **Machine Artifacts** (SARIF, YAML, PHP configs, JSON dumps) are strictly schematized configurations. They are parsed by automated tools—such as Rector for code refactoring, Deptrac for structural boundary verification, or GitHub Actions for code scanning alerts.

#### Q18: How does the system dynamically synthesize `rector.php` and `deptrac.yaml` configurations?
*   **Answer**: The backend runs the `EvidenceBuilder` to build a unified system metadata model (`CanonicalModel`). 
    *   For **Rector**: The `RectorGenerator` maps AST-identified legacy structures (e.g., legacy `mysql_*` functions, procedural files) and outputs a PHP file declaring target migration rule sets (like `DeadCode`, `Php74`, or specific legacy database replacement policies).
    *   For **Deptrac**: The `DeptracGenerator` outputs a YAML file configuring custom directories as independent layers and specifies dependency rules prohibiting cross-layer imports (e.g., prohibiting the View layer from importing the Database layer).

#### Q19: What is the purpose of the "Workspace Export Bundle" (.zip), and what does it include?
*   **Answer**: It compiles all generated reports, configurations, and raw data dumps into a single ZIP file. It includes the Master HTML Report (`index.html`), technical markdown report, risk CSV, results in SARIF format, `rector.php`, `deptrac.yaml`, and the raw relational JSON graph. This creates a portable, versioned snapshot of the codebase's health for documentation and CI/CD ingestion.

---

# Page 11: Master Navigatable HTML Application (`index.html.j2` & `HtmlRenderer`)
### 🔍 Focus: Single-page application structure, responsive Tailwind grid, AlpineJS reactivity, ChartJS/VisJS/Mermaid data visualization.

#### Q20: What front-end technologies drive the generated Master HTML Report, and how is it styled?
*   **Answer**: The report is a self-contained, single-page web application compiled using **Jinja2 templates** on the backend.
    *   **Styling**: Powered by **TailwindCSS** (loaded via CDN) with a custom CSS root defining dark and light theme variables (`--bg-main`, `--bg-surface`, `--text-heading`).
    *   **Reactivity**: Powered by **Alpine.js** to handle theme toggling, active section tracking via an `IntersectionObserver`, and collapsible navigation menus without heavy external dependencies.

#### Q21: How are the visual charts and interactive dependency graphs rendered in the HTML document?
*   **Answer**: The document embeds raw JSON data directly from the backend model, which is consumed by three visualization libraries:
    *   **Chart.js**: Renders a multi-axis **Radar Chart** displaying the *Architecture Modernization Index* (Security, DB Layering, Testability, Namespace, and Coupling).
    *   **Vis.js (vis-network)**: Renders the **Interactive System Topology Graph**, using a force-directed layout engine to cluster nodes representing files and database tables.
    *   **Mermaid.js**: Dynamically renders sequence and flow diagrams inside the *Extraction Playbook* blocks to illustrate decoupled request patterns.

#### Q22: What are the core sections of the Master HTML Report, and how do they map to the Strata system?
*   **Answer**: The report features 8 primary sections:
    1.  **Executive Command Center**: Modernization Readiness progress indicator, Radar dimension scorecard, and AI-synthesized roadmap.
    2.  **Architectural Discovery**: Vis.js system topology map, MVC separation ratios, and an interactive tree-view Monolith Navigator.
    3.  **Boundary Intelligence**: MVC deficit ratings, "Fat Views", unmanaged entry point listings, and vendor library maps.
    4.  **Database Intelligence**: Access Taxonomy showing raw SQL vs ORM calls, unguarded writes, table ownership maps, and a Graphviz ERD.
    5.  **Runtime & Global State**: Global variable access locations and static call dependencies.
    6.  **Legacy PHP Intelligence**: PHP Era footprint profiling and deprecated function usage.
    7.  **Structural Risk Audit**: Multi-column sorting risk matrix showing Maintainability Index (MI), Cyclomatic Complexity (CC), and Fan-Out per file.
    8.  **Extraction Playbooks**: Deep refactoring instructions, raw `rector.php` snippets, and dependency constraints (`deptrac.yaml`).
