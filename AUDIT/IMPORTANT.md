You are thinking about this the right way: your product should not be “another linter.” It should be a **modernization decision support system** that turns raw static analysis into a migration plan, a risk map, and refactoring-ready artifacts.

What you already have is the foundation for the pipeline. PHPStan is aimed at finding bugs without running code, PhpMetrics reports maintainability/complexity-style metrics, Rector automates upgrades and refactoring, Deptrac focuses on architectural decisions and dependency rules, and PHP-Parser-style AST tooling gives you traversal, location info, and code-to-code transformation capabilities. SARIF is the standard interchange format for static analysis findings, and GitHub can ingest SARIF for code scanning. Graphviz DOT is a practical graph format for dependency and architecture diagrams, while JSON Schema is the right way to lock down your machine-readable outputs. ([GitHub][1])

## What your system should actually be

Your tool should answer five questions, not one:

1. **What is this system?**
   Inventory, structure, modules, entry points, dependencies, frameworks, versions, and runtime shape.

2. **What is risky?**
   Complexity hotspots, tightly coupled areas, dead zones, architectural violations, fragile files, and modernization blockers.

3. **What should be changed first?**
   Prioritized modernization opportunities with justification, effort, and impact.

4. **What refactoring path is safest?**
   Concrete target states: layered architecture, framework upgrade path, service extraction, boundary cleanup, test insertion points.

5. **What artifacts can feed the next toolchain?**
   Outputs that Rector, Deptrac, CI, GitHub code scanning, internal refactoring scripts, or human engineers can directly consume.

That is the uniqueness gap. PHPStan tells you “this is wrong.” PhpMetrics tells you “this is complex.” Deptrac tells you “this dependency violates a rule.” Rector can transform code. Your product should tell the team **“here is the modernization move, why it matters, what it breaks, and what artifact to use next.”** ([GitHub][1])

## The best end-to-end flow

The product should feel like a pipeline with evidence at every stage:

**1. Import and scan**
Repo selection, branch selection, PHP version, composer detection, file indexing, cache, incremental scan support.

**2. Parse and normalize**
AST parse, symbol resolution, file-level metadata, class/function/method inventory, route/controller/template detection, dependency extraction.

**3. Measure**
Complexity metrics, coupling, fan-in/fan-out, inheritance depth, file churn if you later add git history, test coverage hooks if available, architecture layer violations.

**4. Classify**
Group the system into domains/modules/layers and label areas as stable, risky, legacy, critical, or modernization candidates.

**5. Decide**
Rank modernization waves: quick wins, medium-risk refactors, boundary extraction, upgrade blockers, deprecation cleanup, framework migration candidates.

**6. Export**
Generate machine-readable findings, diagrams, rulesets, and migration plans.

This flow matters because ASTs give you the low-level facts, but modernization needs a second layer of reasoning on top of those facts. PHP-Parser-style tooling is good for transformation because it can parse to an AST, traverse/modify it, preserve location info, and turn modified trees back into PHP code; that makes it suitable for both analysis and code-generation workflows. ([Packagist][2])

## Pages your Streamlit frontend should have

Do not build a page for every raw data type. Build pages around decisions.

### 1) Project Overview

This is the landing page.

Show:

* repository name, branch, scan time, PHP version guess, framework guess
* total files, classes, functions, controllers, models, routes
* overall modernization readiness score
* top 5 risks
* top 5 recommended actions

This page should answer “Is this codebase healthy enough to modernize safely?”

### 2) Architecture Map

This is your signature page.

Show:

* module graph
* dependency direction
* layer boundaries
* cycles
* forbidden dependencies
* hotspots between modules

Use a graph view plus a list of the violations that matter most. Deptrac’s own purpose is to communicate, visualize, and enforce architectural decisions and dependency rules, so this page should mirror that idea but present it as modernization guidance rather than only enforcement. ([deptrac.github.io][3])

### 3) Code Health / Risk Dashboard

Show:

* complexity outliers
* coupling outliers
* large files
* dense methods
* long parameter lists
* suspicious inheritance chains
* deeply nested conditional logic
* dead or low-reach code areas

This is where PhpMetrics-style ideas belong, but your version should rank “modernization pain” rather than just show metrics. PhpMetrics explicitly provides maintainability, complexity, difficulty, and coupling-style reporting, which makes it a strong baseline for this page. ([phpmetrics.org][4])

### 4) Inventory Explorer

Show:

* files by type
* namespace map
* class hierarchy
* functions per class
* entry points
* service/container bindings
* routes/controllers/views
* DB access points

This page is for digging from the overview into the system structure. It should be searchable and filterable, not just visual.

### 5) Findings Browser

Show findings in a triage-friendly format:

* severity
* category
* evidence
* file/line
* impact
* confidence
* suggested next action
* related artifacts

Think of this as the “engine room.” Each finding must be traceable back to code evidence and forward to a recommendation. This is the right place to align with SARIF concepts because SARIF is a standard output format for static analysis results and can be uploaded to GitHub code scanning. ([docs.oasis-open.org][5])

### 6) Modernization Opportunities

This is the most important page for your product.

Each opportunity card should include:

* problem statement
* why it matters
* affected scope
* risk level
* estimated effort band
* suggested order
* prerequisite tasks
* related refactoring tools
* expected benefit

Examples:

* “Extract module boundary”
* “Introduce interface around direct DB access”
* “Split god controller”
* “Prepare for PHP version upgrade”
* “Normalize dependency direction”
* “Replace unsafe legacy patterns”

### 7) Refactoring Plan

This page should convert analysis into execution.

Show:

* phased roadmap
* recommended waves
* what to do first
* what to defer
* dependencies between tasks
* rollback or safeguard notes

This is where your system becomes a decision tool rather than a report generator.

### 8) Artifact Center

A dedicated page for downloads and exports.

Show:

* JSON export
* SARIF export
* dependency graph export
* inventory export
* modernization plan export
* ruleset exports
* generated prompts or notes for external refactoring tools

### 9) Compare / Trend page

If you support multiple scans, this becomes very powerful.

Show:

* baseline vs current
* improvement or regression
* complexity trend
* architectural drift
* new violations
* cleanup progress

This is how you turn the product into a governance tool.

## What to display, and what not to display

### Display

Show information that helps a human decide:

* architecture structure
* dependency direction
* risk hotspots
* dead zones
* candidate refactoring targets
* modernization priority
* evidence and confidence
* transformation compatibility

### Do not over-display

Avoid flooding the user with:

* raw AST trees
* every token or node
* every single warning without grouping
* duplicated metrics across multiple views
* low-value file-by-file noise on the main dashboard

Raw AST detail belongs in drill-down panels, not the primary UI. The main UI should operate at the level of “system understanding.”

## What your artifacts should be

You need two artifact families: **human artifacts** and **machine artifacts**.

### Human artifacts

These are for review, planning, and communication:

* executive HTML/PDF report
* architecture diagram
* modernization roadmap
* risk summary
* module map
* remediation backlog

### Machine artifacts

These are for tool integration and automation:

* **JSON** with a strict schema for all findings and inventories
* **SARIF** for findings that map to static-analysis style alerts ([docs.oasis-open.org][5])
* **DOT / SVG** for dependency graphs and architecture diagrams ([Graphviz][6])
* **CSV** for exports to spreadsheets or BI tools
* **YAML** for rulesets, layer definitions, and refactoring plans
* **Rector-ready config suggestions** for upgrade/refactor candidates, because Rector is explicitly built for automated PHP upgrades and refactoring. ([GitHub][7])
* **Deptrac-style layer/rule definitions** for architectural boundaries, because Deptrac exists to define and enforce dependency rules between layers. ([deptrac.github.io][3])

## The most valuable artifact set

If I had to choose only five outputs, I would make them these:

1. **System inventory JSON**
2. **SARIF findings file**
3. **Architecture graph in DOT/SVG**
4. **Modernization roadmap JSON/YAML**
5. **Human-readable report**

That combination covers analysis, automation, visualization, and communication.

## The real competitive advantage

Your uniqueness should come from **translation**, not just analysis.

You are translating:

* code facts → architecture understanding
* architecture understanding → risk
* risk → priority
* priority → refactoring plan
* refactoring plan → tool-compatible artifacts

That is a much stronger product than “static analysis dashboard.”

## A strong internal data model

I would structure the backend around these entities:

* Repository
* ScanRun
* File
* Symbol
* DependencyEdge
* Metric
* Violation
* RiskFinding
* ModernizationOpportunity
* Recommendation
* Artifact
* Rule
* Layer
* Evidence

This lets you keep every finding traceable and every recommendation explainable.

## My recommendation for your MVP scope

Do not try to solve everything at once. The first truly strong version should include:

* repo scan
* inventory
* architecture graph
* risk dashboard
* findings browser
* modernization opportunities
* JSON/SARIF/DOT exports

That is enough to feel like a serious modernization platform.

The next step should be to define your **page-by-page specification** and the **exact JSON schema** for each artifact so the frontend, backend, and exporter all speak the same language.

[1]: https://github.com/phpstan/phpstan?utm_source=chatgpt.com "PHPStan - PHP Static Analysis Tool"
[2]: https://packagist.org/packages/nikic/php-parser?utm_source=chatgpt.com "nikic/php-parser"
[3]: https://deptrac.github.io/deptrac/?utm_source=chatgpt.com "Deptrac"
[4]: https://www.phpmetrics.org/?utm_source=chatgpt.com "PhpMetrics, static analysis for PHP - by Jean-François Lépine"
[5]: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html?utm_source=chatgpt.com "Static Analysis Results Interchange Format (SARIF) Version ..."
[6]: https://graphviz.org/doc/info/lang.html?utm_source=chatgpt.com "DOT Language"
[7]: https://github.com/rectorphp/rector?utm_source=chatgpt.com "Rector - Instant Upgrades and Automated Refactoring"
