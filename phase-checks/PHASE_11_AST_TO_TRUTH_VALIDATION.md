
# Phase 11: AST to Truth — Final Validation Guide

This guide details the verification steps to ensure the high-fidelity AST parsing lineup and Centralized Source of Truth (CSOT) are functioning with academic and production precision.

## 1. Environment & Infrastructure Check
**Goal**: Verify that the dual-runtime (Python + PHP) bridge is established.

- [ ] **Docker Presence**: Run `docker exec -it <container_id> php -v`. Ensure PHP 8.2+ is active.
- [ ] **Composer Integrity**: Check `infrastructure/php/vendor/autoload.php` exists inside the container.
- [ ] **Sidecar Connectivity**: Run `python -c "from infrastructure.parser_bridge import PHPRuntime; r=PHPRuntime(); r.start(); print('Bridge Active' if r._process else 'Failed')"` inside the container.


## 2. AST Extraction Accuracy (The "Kitchen Sink" Test)
**Goal**: Ensure complex PHP features are correctly parsed.


- [ ] **Run Unit Test**: Run this command from your host terminal:
    ```bash
    docker compose exec api pytest tests/test_ast_bridge.py
    ```
- [ ] **Check FQN Resolution**: Verify that `App\Services\UserService` is extracted correctly, not just `UserService`.
- [ ] **Check Side-Effects**: View the metadata output for `kitchen_sink.php` and ensure the `find()` method is tagged with `DB` and `NET` side-effects.

## 3. Semantic Resolution & Hierarchy
**Goal**: Verify the global inheritance graph and role recognition.

- [ ] **Hierarchy Test**: Run inside the container:
    ```bash
    docker compose exec api python -c "
from domain.services.hierarchy_resolver import HierarchyResolver
"
    ```
    from domain.models.graph_model import GraphModel
    # Load your graph...
    hr = HierarchyResolver(graph.graph)
    print(hr.get_all_ancestors("App\\Services\\UserService"))
    ```
- [ ] **Role Validation**: Ensure `UserService` is tagged as `Service` and `UserRepository` as `Repository` via `ArchitecturalService`.

## 4. Persistence & CSOT Integrity
**Goal**: Verify the "Source of Truth" is queryable in SQLite.

- [ ] **DB Inspection**: Use `sqlite3 data/strata.db` (or your configured DB):
    ```sql
    SELECT * FROM component_dependencies LIMIT 10;
    ```
- [ ] **Referential Integrity**: Ensure no `source_id` exists without a corresponding entry in `component_metrics`.

## 5. Knowledge Synthesis (The "Brain" Test)
**Goal**: Ensure the summary generated for the LLM/Decision Engine is high-density.

- [ ] **Generate Manifest**: Run a script to call `KnowledgeSynthesisService.serialize_for_system(run_id)`.
- [ ] **Review Output**: Ensure the JSON contains:
    - `top_hotspots` (The 10 most "risky" nodes).
    - `behavioral_summary` (List of components with heavy DB side-effects).
    - `recommendation_engine` hints.

---

## 🚦 Exit Criteria for Phase 11
1. **Zero Regex**: The system produces a complete graph without a single regex match for class/method detection.
2. **Deterministic IDs**: Running the same code twice produces identical SHA256 IDs.
3. **Synthesis Latency**: Generating a full intelligence manifest takes < 1 second for 1,000 components.

---

**Authorized by**: Antigravity (AI Architect)
**Date**: 2026-05-12
