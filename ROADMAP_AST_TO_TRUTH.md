
# Strata Technical Roadmap: From AST to Centralized Source of Truth

This document outlines the strategic engineering path to evolve Strata from a regex-based analyzer into a high-fidelity intelligence platform for PHP monoliths. The goal is to build a **Centralized Source of Truth (CSOT)** that provides the deep understanding required for automated refactoring and risk assessment.

---

## Phase 1: High-Fidelity AST Extraction (Foundation)
**Objective**: Replace the current regex-based extraction with a formal PHP AST parser to achieve 100% grammatical accuracy.

### 1.1. Parser Selection & Bridge Implementation
- **Tooling**: Integrate `nikic/php-parser` via a dedicated PHP sidecar.
- **Protocol**: Develop a high-speed JSON-over-STDIN/OUT bridge between Python and the PHP parser.
- **Coverage**:
    - PHP 7.x to 8.3 compatibility (including Union Types, Enums, Attributes, and Readonly properties).
    - Comprehensive extraction of: Class/Interface/Trait definitions, Method signatures, Property declarations, and Use statements.
    - Extraction of constant values and literal strings (critical for SQL/API detection).

### 1.2. Token-Level Behavioral Detection
- **Task**: Capture logic *within* methods.
- **Details**:
    - Identify all function calls (internal and user-defined).
    - Identify all class instantiations (`new ClassName`).
    - Identify property accesses (`$this->property`).
    - Identify global/static accesses (`StaticClass::method`).

### 1.3. Robust Error Handling
- **Strategy**: Implement a "Partial Parse" mode where syntax errors in legacy files don't crash the entire run.
- **Reporting**: Detailed error log highlighting unparseable files for user intervention.

**Exit Criteria**: 
- [ ] `ParserBridge` successfully extracts nodes from the `nikic/php-parser` JSON output.
- [ ] 0% reliance on `_CLASS_PATTERN` or `_METHOD_PATTERN` regex constants.
- [ ] Test suite verifies 100% node coverage on a complex PHP 8.x codebase.

---

## Phase 2: Global Symbol Resolution & Semantic Mapping
**Objective**: Transform isolated file ASTs into a unified, globally connected semantic model.

### 2.1. Name Resolution (The FQN Mapper)
- **Task**: Resolve all relative class names and aliases to their Fully Qualified Names (FQN).
- **Complexity**: Handle `use` statements, group aliases, and the global namespace.

### 2.2. Inheritance & Implementation Crawler
- **Task**: Build the global hierarchy graph.
- **Details**:
    - Resolve parent classes and interfaces across the entire project.
    - Identify method overrides and "virtual" calls.
    - Implement "Trait Flattening": Logically inject trait methods into the consuming class nodes in the graph.

### 2.3. Call-Graph Construction
- **Static Analysis**: Connect call sites to their definitions.
- **Ambiguity Handling**: For dynamic calls (e.g., `$obj->$method()`), mark as "DynamicEdge" with a probability score or a list of potential targets based on type-hinting.

**Exit Criteria**:
- [ ] Every symbol (Class, Method, Property) has a globally unique, deterministic ID.
- [ ] Graph supports `EXTENDS`, `IMPLEMENTS`, and `CALLS` edge types with 95%+ accuracy.
- [ ] Resolution successfully handles cross-namespace dependencies.

---

## Phase 3: The Centralized Source of Truth (CSOT)
**Objective**: Persist and manage the "Project Intelligence" in a structured, versioned, and queryable format.

### 3.1. Strata Canonical Schema (SCS)
- **Node Types**: `File`, `Namespace`, `Class`, `Interface`, `Trait`, `Method`, `Field`, `Table`, `API_Route`, `Global_Var`.
- **Edge Types**: `DECLARES`, `CALLS`, `WRITES_TO`, `READS_FROM`, `INHERITS`, `DEPENDS_ON`.
- **Metadata**: Every node must store its location (line numbers), complexity metrics, and raw source snippet.

### 3.2. Graph Persistence Layer
- **Implementation**: Optimize SQLite for recursive queries (Common Table Expressions) or integrate a graph library like `NetworkX` for in-memory analysis with persistence to JSON/SQLite.
- **Integrity**: Implement strict referential integrity for edges (no "orphaned" calls).

### 3.3. Determinism & Versioning
- **Task**: Ensure the CSOT is stable.
- **Details**:
    - Hash-based IDs for all nodes (e.g., `SHA256(FQN + type)`).
    - Support for "Differential Analysis": Compare the CSOT of `Run A` vs `Run B` to see how the project evolved.

**Exit Criteria**:
- [ ] CSOT is the single source of data for the UI and Risk Engine.
- [ ] Successful serialization/deserialization of a 10,000+ node graph.
- [ ] Query performance: "Find all impact of changing Class X" returns in < 500ms.

---

## Phase 4: Behavioral Understanding & Logic Profiling
**Objective**: Move beyond structure into "Logic Understanding"—interpreting what the code *does*.

### 4.1. Data Flow & Side-Effect Analysis
- **DB Tracking**: Trace method calls down to DB driver calls (PDO, mysqli, ORM).
- **IO Tracking**: Identify file system operations, session writes, and network requests.
- **State Mutability**: Flag methods that modify object state vs. pure functions.

### 4.2. Pattern Recognition Engine
- **Task**: Automatically tag nodes with "Architectural Roles".
- **Examples**:
    - Detects `Controller` if it handles a Request and returns a Response.
    - Detects `Repository` if it performs CRUD operations on a single Table.
    - Detects `Service` if it coordinates multiple Repositories.

### 4.3. Transactional Boundary Detection
- **Logic**: Identify where transactions start and end. Map which methods are "Safe" to call within a transaction and which are "Risky" (e.g., calling an external API inside a DB transaction).

**Exit Criteria**:
- [ ] The system can generate a "Behavioral Profile" for any class (e.g., "Class UserSvc: 3 DB writes, 1 API call, 0 transactions").
- [ ] 90% accuracy in identifying Repositories and Controllers in standard PHP frameworks (Laravel, Symfony, Slim).

---

## Phase 5: System Integration & Knowledge Synthesis
**Objective**: Transform the CSOT into high-density "Intelligence Inputs" for the downstream system (LLM/Refactoring Engine).

### 5.1. Contextual Chunking & Serialization
- **Task**: Package the graph for LLM consumption.
- **Strategy**: Instead of raw code, send "Semantic Summaries":
    - "Component X depends on Y and Z. It has a high blast radius (15) and performs unsafe DB writes."
- **Reachability Pruning**: Only include nodes relevant to the current refactoring target.

### 5.2. Refactoring Candidate Generator
- **Logic**: Use the CSOT to find "Ideal Extraction Points".
- **Criteria**: High internal cohesion (SCC), low external coupling, and low risk score.
- **Simulation**: Implement a "What-If" engine that simulates removing a node from the graph and calculates the remaining connectivity.

### 5.3. The "System" Feedback Loop
- **Task**: Allow the system to query the CSOT for more details.
- **Capability**: "System asks: Show me all methods in Class A that call the DB directly."

**Exit Criteria**:
- [ ] A "Project Summary" JSON that encapsulates the entire architecture in < 100kb.
- [ ] Demonstration of a "Refactoring Proposal" generated entirely from CSOT data.
- [ ] Integration test: Downstream "System" can correctly identify a circular dependency using only the provided CSOT input.

---

## Final Validation & Competition Readiness

### Performance Targets
- **Parsing**: < 1s per 100 files (parallelized).
- **Resolution**: < 5s for 1,000 classes.
- **Graph Search**: Sub-second responsiveness for UI interactions.

### Quality Checks (Before moving to next Phase)
1. **Semantic Accuracy**: Manual spot-check of 50 random edges against the source code.
2. **Determinism**: Running the analysis 3 times on the same codebase yields 3 identical CSOT hashes.
3. **Robustness**: The system must handle a "Kitchen Sink" PHP file containing every valid (and some invalid) syntax feature.

---

**Status**: *Planning Complete*  
**Next Step**: *Initialize Phase 1 PHP Parser Bridge*
