# Strata: Legacy PHP Monolith Modernization Analyzer

Strata is a local-first web platform for analyzing legacy PHP monoliths, prioritizing structural guarantees and privacy (no source code leaves your machine).

## Architectural Boundaries

This project enforces strict layering, following Clean Architecture principles:

- **`api/`**: FastAPI endpoints (No domain/business logic).
- **`application/`**: Use-cases and orchestration (e.g., `AnalysisService`).
- **`domain/`**: Mathematical reasoning, algorithms, and models (pure functions).
- **`infrastructure/`**: Database persistence, file scanning, and raw PHP parsing bridge.
- **`frontend/`**: Streamlit visualization (Only communicates via HTTP API).

## Running the Application

This tool runs fully containerized. A `./data` directory will be created to store your `.db` and analysis artifacts locally.

### 1. Configuration

Create a `.env` file by copying the template:

```bash
cp .env.example .env
```

### 2. Startup

Spin up the application using Docker Compose:

```bash
docker compose up --build
```

### 3. Access

- **Frontend Dashboard**: [http://localhost:8501](http://localhost:8501)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Phase 0: Foundation

Currently, Strata is in Phase 0. The current phase establishes the deterministic project structure, Docker environment, SQLite auto-generation, API routing, and logging. Analysis logic (AST parsing and Graph evaluation) belongs to Phase 1.
