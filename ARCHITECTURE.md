# Architectural Blueprint

Strata implements a **Layered Clean Architecture** adapted for a local-first static analysis tool.

## Philosophy

- Separation of concerns
- One-directional dependency flow (top-down)
- Testability at every layer
- Replaceable components
- Deterministic execution

## The Layered Model

```text
UI Layer (Streamlit)
        ↓
API Layer (FastAPI)
        ↓
Application Layer (Orchestrators / Use Cases)
        ↓
Domain Layer (Graph + Scoring Logic)
        ↓
Infrastructure Layer (Persistence, PHP bridge, filesystem)
```

## Layer Responsibilities

### 1. UI Layer (`frontend/`)

Strictly a presentation layer built in Streamlit. It fetches all data via HTTP requests to the API. It has zero awareness of the underlying graph algorithms or database.

### 2. API Layer (`api/`)

The interface boundary (FastAPI). It defines endpoints, parses requests using Pydantic, calls application-layer services, and formats the responses.

### 3. Application Layer (`application/`)

The orchestration layer. It executes full workflows (e.g., triggering a file scan, passing it to the parser, sending the AST to the domain model, and persisting the result). It orchestrates but does not perform the raw mathematical scoring itself.

### 4. Domain Layer (`domain/`)

The intellectual core of the application. Contains the Graph Models, Centrality Algorithms, Blast Radius rules, and Risk Scoring math.
**Constraint**: Must be framework-independent. Zero FastAPI or SQLite imports allowed. Pure, mathematically verifiable functions.

### 5. Infrastructure Layer (`infrastructure/`)

Handles the messy interactions with the outside world. Contains the PHP subprocess bridge, file system scanning operations, SQLite persistence, and repository patterns.

## Dependency Rules (Non-Negotiable)

- Top layers can import bottom layers. Bottom layers **cannot** import top layers.
- The `domain` layer is pure and must never import from `infrastructure` or `application`.
