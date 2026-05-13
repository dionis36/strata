Your frontend direction is already strong, but before touching UI implementation further, you need a **backend readiness validation framework**.

Right now your biggest risk is:

> Building beautiful pages that your analysis engine cannot properly support.

So the correct next move is:

# Build a backend/engine capability checklist mapped directly to every frontend page, interaction, graph, and decision flow.

This becomes your:

* engineering contract
* system architecture blueprint
* backend completeness validator
* FYP implementation tracker

---

# 1. FIRST — Update the Frontend Structure Slightly

Your current grouping is good, but two important architectural capabilities are underrepresented:

1. Dependency Intelligence
2. Knowledge Graph / System Intelligence

PHPMetrics stops at metrics.
Your tool should become a:

# "System Intelligence Platform"

So I recommend this updated navigation taxonomy.

---

# UPDATED FRONTEND TAXONOMY

```text
A. Command & Strategy
   - Dashboard
   - Executive Roadmap

B. Structural Intelligence
   - Monolith Navigator
   - Dependency Explorer
   - Layered Architecture

C. System Intelligence
   - Database Intelligence
   - Runtime & Global State Intelligence
   - Legacy PHP Intelligence
   - Security & Risk Audit

D. Decision & Simulation
   - Modernization Simulator
   - Extraction Simulator
   - Modernization Decision Engine

E. Automation & Generation
   - Legacy Bootstrapper
   - Documentation Studio
   - Export Center

F. Platform
   - Scan Manager
   - Rules & Profiles
   - Analysis History
```

---

# WHY THIS STRUCTURE IS STRONGER

Your current structure mixes:

* structure
* intelligence
* simulation

This updated structure separates:

* observing
* understanding
* deciding
* generating

Which matches real modernization consulting workflows.

---

# 2. CRITICAL MISSING PAGE — Dependency Explorer

This MUST exist separately from Monolith Navigator.

Because:

* Navigator = file/folder view
* Dependency Explorer = relationship intelligence

These are fundamentally different.

---

# Dependency Explorer Should Show

## Include Graphs

```text
index.php
 ├── config.php
 ├── auth.php
 └── dashboard.php
```

---

## File Coupling

```text
File A imports:
- DB layer
- Session state
- Template engine
```

---

## Hotspot Analysis

Show:

* highly connected files
* dangerous central nodes
* god modules
* fragile chains

---

## Circular Dependencies

```text
A → B → C → A
```

---

# 3. VERY IMPORTANT ADDITION — Runtime & Global State Intelligence

Legacy PHP systems heavily rely on:

* $_SESSION
* $_POST
* $_GET
* globals
* include-time side effects

PHPMetrics barely understands this.

This page becomes one of your strongest differentiators.

---

# 4. NOW — THE REAL BACKEND CHECKLIST

THIS is the important part.

You need to validate whether your backend can support every page.

---

# MASTER BACKEND READINESS CHECKLIST

We will structure this by:

```text
Page
 ├── Required Backend Capability
 ├── Required Data
 ├── Required Analysis Engine
 ├── Required Storage
 ├── Required API/State
 └── Readiness Questions
```

---

# A. DASHBOARD

---

# Backend capabilities required

## Project Registry

Must support:

```text
Project
- id
- name
- root_path
- created_at
- active_run
```

---

## Analysis Run Tracking

Must support:

```text
AnalysisRun
- id
- project_id
- scan_started_at
- scan_finished_at
- php_version_detected
- total_files
- status
```

---

## Aggregate Metrics Engine

Must compute:

* total LOC
* total files
* total complexity
* avg maintainability
* risk score
* coupling score
* modernization readiness

---

# Readiness questions

✅ Can backend persist multiple scans?

✅ Can backend compare scan runs?

✅ Can backend compute global risk score?

✅ Can backend summarize findings quickly?

✅ Can dashboard load without rescanning?

---

# B. MONOLITH NAVIGATOR

---

# Backend capabilities required

## File Inventory Engine

Must detect:

* all PHP files
* assets
* configs
* vendor dirs
* templates
* scripts

---

## File Classification Engine

Must classify:

| Type        | Example            |
| ----------- | ------------------ |
| Entry Point | index.php          |
| Bootstrap   | app.php            |
| Config      | config.php         |
| View        | *.tpl              |
| Controller  | UserController.php |
| Job/Cron    | cron/send.php      |

---

## AST Extraction Engine

Must extract:

* classes
* methods
* functions
* includes
* globals
* namespaces

---

# Readiness questions

✅ Can backend recursively scan huge projects?

✅ Can it classify files reliably?

✅ Can it detect mixed PHP/HTML?

✅ Can it detect entry points?

✅ Can it detect dead files?

---

# C. DEPENDENCY EXPLORER

THIS IS A MAJOR ENGINE COMPONENT.

---

# Backend capabilities required

## Dependency Graph Builder

Must build:

```text
File → File
Class → Class
Function → Function
Module → Module
```

---

## Include Chain Resolver

Must resolve:

```php
include($base . "/config.php");
```

even partially.

---

## Graph Storage

You NEED graph-oriented storage.

At minimum:

```text
nodes
edges
edge_type
weight
```

Preferably:

* Neo4j
  OR
* NetworkX
  OR
* graph tables

---

# Required analyses

## Coupling analysis

## Centrality analysis

## Circular dependency detection

## Fan-in / fan-out

## Hotspot analysis

---

# Readiness questions

✅ Can backend build dependency graphs?

✅ Can it detect circular includes?

✅ Can it identify architectural hubs?

✅ Can it calculate coupling strength?

✅ Can it cluster modules?

---

# D. LAYERED ARCHITECTURE

---

# Backend capabilities required

## Architectural Layer Inference

Must infer:

```text
Presentation
Business Logic
Data Access
Infrastructure
```

from folder structures and usage.

---

## Layer Violation Detection

Example:

```text
View directly accessing DB
```

---

# Readiness questions

✅ Can backend infer architectural layers?

✅ Can it detect cross-layer violations?

✅ Can it group modules semantically?

---

# E. DATABASE INTELLIGENCE

VERY IMPORTANT.

---

# Backend capabilities required

## SQL Extraction Engine

Must detect:

```php
mysql_query(...)
PDO->query(...)
mysqli_query(...)
```

---

## Query Parser

Must infer:

* tables
* joins
* write operations
* read operations

---

## Table Ownership Engine

Must determine:

```text
Which module owns which table?
```

---

## ERD Inference

Should infer:

* relationships
* foreign keys
* implicit joins

---

# Readiness questions

✅ Can backend extract raw SQL?

✅ Can it map tables to modules?

✅ Can it infer write-heavy areas?

✅ Can it detect dangerous queries?

---

# F. GLOBAL STATE INTELLIGENCE

One of your strongest differentiators.

---

# Backend capabilities required

## Superglobal Tracker

Track:

* $_SESSION
* $_POST
* $_GET
* $_COOKIE
* $_FILES

---

## Global Variable Tracker

Track:

* global keyword
* $GLOBALS
* cross-file mutations

---

## Session Flow Analysis

Must infer:

```text
login.php
 → sets $_SESSION['user']
dashboard.php
 → consumes it
```

---

# Readiness questions

✅ Can backend trace session usage?

✅ Can it track mutable globals?

✅ Can it detect side effects?

---

# G. LEGACY PHP INTELLIGENCE

This is your expert-system layer.

---

# Backend capabilities required

## Legacy Pattern Detection

Detect:

* mysql_*
* register_globals assumptions
* include-based routing
* inline HTML/PHP
* no namespaces
* __autoload

---

## PHP Era Estimation

Estimate:

* PHP 4
* early PHP 5
* transitional
* modernized

---

# Readiness questions

✅ Can backend estimate PHP era?

✅ Can it detect hosting assumptions?

✅ Can it detect legacy auth systems?

---

# H. SECURITY & RISK AUDIT

---

# Backend capabilities required

## Security Rule Engine

Detect:

* SQL injection risks
* eval()
* extract()
* file inclusion
* unsafe uploads
* MD5 passwords

---

## Risk Scoring Engine

Must assign:

* severity
* confidence
* exploitability

---

# Readiness questions

✅ Can backend score vulnerabilities?

✅ Can it prioritize risk?

---

# I. MODERNIZATION DECISION ENGINE

THIS IS THE CORE OF YOUR FYP.

---

# Backend capabilities required

## Rule Engine

Must evaluate:

```text
IF
 high coupling
 AND procedural
 AND no namespaces
THEN
 recommend strangler migration
```

---

## Strategy Recommendation Engine

Must support:

* rehost
* replatform
* refactor
* rewrite
* strangler fig

---

## Effort Estimator

Should estimate:

* complexity
* migration effort
* refactor cost

---

# Readiness questions

✅ Can backend generate recommendations?

✅ Can it justify recommendations?

✅ Can it rank modernization priorities?

---

# J. MODERNIZATION SIMULATOR

VERY ADVANCED.

---

# Backend capabilities required

## Impact Analysis Engine

Simulate:

```text
What breaks if module X is removed?
```

---

## Dependency Propagation Engine

Must trace:

* transitive dependencies
* DB dependencies
* auth dependencies

---

# Readiness questions

✅ Can backend simulate extraction?

✅ Can it estimate blast radius?

---

# K. LEGACY BOOTSTRAPPER

---

# Backend capabilities required

## Composer Migration Engine

Must generate:

* composer.json
* PSR-4 mappings
* autoload rules

---

## Namespace Recommendation Engine

Must propose:

* namespace structures
* module mappings

---

# Readiness questions

✅ Can backend generate autoload mappings?

✅ Can it infer namespaces?

---

# L. DOCUMENTATION STUDIO

---

# Backend capabilities required

## Artifact Generation Engine

Must generate:

* markdown
* PDF
* DOCX
* JSON

---

## Narrative Generation Engine

Must convert:

* metrics
* graphs
* findings

into:

* readable explanations

---

# Readiness questions

✅ Can backend generate reports automatically?

✅ Can it generate architecture summaries?

---

# 5. MOST IMPORTANT BACKEND REQUIREMENT

You need a:

# CENTRAL KNOWLEDGE GRAPH

Without this, the system becomes fragmented.

---

# Recommended Internal Model

Everything becomes connected entities.

---

## Nodes

```text
File
Class
Function
Module
Table
SessionVariable
GlobalVariable
API
Risk
```

---

## Edges

```text
INCLUDES
CALLS
WRITES
READS
DEPENDS_ON
USES
OWNS
ROUTES_TO
```

---

# Why this matters

Once you have this:

* all pages become easy
* simulations become possible
* roadmap generation becomes possible
* AI integration becomes possible

This is the architectural core of your entire platform.

---

# 6. MOST IMPORTANT ENGINE QUESTION

Before frontend work continues, ask:

# “Do we already have a normalized analysis model?”

Meaning:
Can ALL engine outputs become:

```text
normalized entities
+
normalized relationships
+
normalized findings
```

If not:
STOP UI EXPANSION.

Because without normalization:

* pages become tightly coupled
* duplicate parsing happens
* graphs become inconsistent
* roadmap logic becomes unreliable

---

# 7. YOUR MOST IMPORTANT NEXT STEP

Do NOT build more frontend yet.

Instead:

# Build a Backend Capability Matrix

Example:

| Capability                    | Exists | Partial | Missing |
| ----------------------------- | ------ | ------- | ------- |
| AST parsing                   | ✅      |         |         |
| Include graph                 | ✅      |         |         |
| Circular dependency detection |        | ✅       |         |
| Session tracking              |        |         | ❌       |
| SQL extraction                | ✅      |         |         |
| Strategy recommendation       |        | ✅       |         |
| Knowledge graph               |        |         | ❌       |

THIS becomes your true engineering roadmap.

---

# 8. FINAL RECOMMENDATION

The single biggest thing separating your project from:

* PHPMetrics
* PHPStan
* Psalm

will NOT be prettier metrics.

It will be:

# SYSTEM-LEVEL INTELLIGENCE

Meaning:

* dependency reasoning
* modernization strategy inference
* extraction simulation
* architectural understanding
* decision support

That is the real innovation layer.
