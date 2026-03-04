# Strata — Phase 1 Prototype Presentation

> **What does Strata do in Phase 1?**
> It takes a folder of PHP files, maps the class dependencies into a graph, stores the result, and displays a structural summary — end to end, in one click.

---

## The Flow

```
1. You place a PHP project inside the data/ folder
         ↓
2. You select it in the browser UI (or call the API directly)
         ↓
3. Strata scans every .php file in that folder
         ↓
4. It reads each file and extracts:
   - Class names
   - Which classes instantiate or call other classes
         ↓
5. A dependency graph is built:
   - Each class = a Node
   - Each call between classes = an Edge
         ↓
6. The graph is saved as a JSON file (graph_1.json, graph_2.json, ...)
         ↓
7. A run record is written to the database (SQLite)
   - Status: completed
   - File count, class count, edge count
         ↓
8. The API returns a 4-number summary
         ↓
9. The browser UI displays the result card
```

---

## What You See at the End

After running analysis on a simple 2-class PHP project:

| Metric           | Value |
| ---------------- | ----- |
| Run ID           | 1     |
| Files Evaluated  | 2     |
| Classes (Nodes)  | 2     |
| Structural Edges | 1     |

> **Edge = 1** means Class A calls Class B — the dependency was successfully detected.

---

## What the System Can Do in Phase 1

| Capability                                         | Status |
| -------------------------------------------------- | ------ |
| Scan a mounted PHP project folder                  | ✅     |
| Detect PHP classes                                 | ✅     |
| Detect class instantiations (`new ClassName()`)    | ✅     |
| Detect static method calls (`ClassName::method()`) | ✅     |
| Detect inheritance (`extends`)                     | ✅     |
| Detect interface implementation (`implements`)     | ✅     |
| Build a directed dependency graph                  | ✅     |
| Drop calls to classes not found in the codebase    | ✅     |
| Prevent duplicate edges (weight instead)           | ✅     |
| Save graph as a JSON file per run                  | ✅     |
| Persist run metadata to SQLite                     | ✅     |
| Isolate each run (no overwriting)                  | ✅     |
| Handle malformed PHP without crashing              | ✅     |
| Display results in Streamlit UI                    | ✅     |
| REST API with Swagger docs                         | ✅     |

---

## Where to Test It

| Interface        | URL                        |
| ---------------- | -------------------------- |
| Streamlit UI     | http://localhost:8501      |
| Swagger API Docs | http://localhost:8000/docs |

**To start:**

```bash
docker compose up --build -d
```

**To reset:**

```bash
docker compose down -v
rm -f data/app.db data/*.json
docker compose up --build -d
```

---

## What Phase 1 Does NOT Do

- No risk scoring
- No centrality metrics (betweenness, blast radius)
- No ranking of risky components
- No multi-file upload
- No cloud storage

> Those belong to Phase 2 and beyond.
