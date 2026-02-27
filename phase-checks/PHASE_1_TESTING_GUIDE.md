# Strata: Phase 1 Minimal Vertical Slice (Testing Guide)

This guide documents how to clone, set up, and test the Phase 1 Minimal Vertical Slice from absolute scratch on any new machine.

Phase 1 proves the structural flow of the application:
`Files → AST Parser Stub → NetworkX Graph → SQLite Persistence → JSON Serialization → UI`

---

## 1. Initial Setup & Cloning

If you are setting this up on a new machine:

```bash
# 1. Clone the repository
git clone <your-repository-url> strata
cd strata

# 2. Checkout the Phase 1 baseline tag to ensure you are testing the right version
git checkout tags/v0.2-vertical-slice -b testing-phase1

# 3. Create the environment file
cp .env.example .env

# 4. Create the required data directory (if Git hasn't already)
mkdir -p data
```

---

## 2. Understanding the Docker Volume Mount

The Strata backend cannot read your local computer's files directly due to Docker container isolation. We use a **volume mount** to bridge a specific local folder into the container.

In our `docker-compose.yml`, we mapped:
`- ./data:/data`

### How to pass legacy PHP code to Strata:

Any folder or file you place inside the `strata/data/` directory on your laptop instantly becomes visible to the API at `/data/`.

**When to paste your files?**
Because the volume mount acts as a live, transparent window, it does not matter if you place the folders into `data/` BEFORE or AFTER you start Docker.

- If you place them before: Docker sees them the millisecond it boots.
- If you place them after: Docker sees them instantly without needing a restart. You do not need to reboot the server to scan new test directories.

**Example:**
If you download a client's legacy codebase and place it at:
`~/strata/data/old_website/`

Inside Streamlit or the API, you must tell Strata to analyze:
`/data/old_website`

---

## 3. Starting the Environment

The `docker compose up` command is the orchestrator for the entire application.

**Important Runtime Rules:**

1. **Execution Location:** You must run `docker compose up` from the absolute root of the project (e.g., `/home/dio/Documents/strata`). If you try to run it inside an inner folder, Docker will fail.
2. **All Services Start Simultaneously:** Running the command boots both the FastAPI backend and the Streamlit frontend. They run side-by-side.
   - Backend API Docs are immediately available at `http://localhost:8000/docs`
   - Frontend UI is immediately available at `http://localhost:8501`

Ensure Docker is running on your host machine, then build and start the application:

```bash
# Build the containers and start in detached mode
docker compose up --build -d

# Verify logs to ensure the database auto-created successfully
docker compose logs -f api
```

_(You should see `Database initialized` in the logs. Stop following logs with `Ctrl+C`)_

---

## 4. Executing The Phase 1 Tests

Before triggering the analysis, let's create a minimal test project within the volume mount to validate the parser.

### Step 4a: Create the Test Subject

Create a small, controlled PHP dataset inside your local `data` directory:

```bash
mkdir -p data/test_project
```

Create `data/test_project/A.php`:

```php
<?php
class A {
    public function foo() {
        $b = new B();
        $b->bar();
    }
}
```

Create `data/test_project/B.php`:

```php
<?php
class B {
    public function bar() {}
}
```

### Step 4b: Trigger Analysis via the API (Swagger)

The most professional way to validate backend execution without UI interference is through the interactive API docs.

1. Open http://localhost:8000/docs
2. Scroll to `POST /analyze` and click **Try it out**.
3. In the Request Body, enter the container path to your test project:

```json
{
  "project_path": "/data/test_project",
  "project_name": "Phase1_Validation"
}
```

4. Click **Execute**.

**Expected Phase 1 Result**:
You should receive an HTTP 200 response immediately:

```json
{
  "run_id": 1,
  "files": 2,
  "classes": 2,
  "edges": 1
}
```

_(If you get `edges: 1`, the Regex AST parser correctly linked Class A calling Class B!)_

### Step 4c: Verify Artifact Persistence

Check if the architectural rules preserved the metadata securely.

1. **Graph JSON Verification**
   Look inside your local `data/` folder. You should see a new file `data/graph_1.json`.
   Open it and confirm that the `NetworkX` serialization mapped `"ClassA"` and `"ClassB"` as nodes, and drew a `method_call` link between them.

2. **Database Verification (Optional but Recommended)**
   Use a SQLite viewer (or run `sqlite3 data/app.db`) to check the `analysis_run` table.
   Confirm a row exists where `status='completed'`, `total_files=2`, and `total_edges=1`.

### Step 4d: Verify Frontend Integration

Now that the backend is proven, verify the presentation layer.

1. Open http://localhost:8501.
2. Confirm the **System Status** sidebar reports `Status: ok` and `Database: connected`.
3. In the "Project Path" input box, enter exactly `/data/test_project`.
4. Click **Run Minimal Analysis**.
5. The UI should instantly display the 4 metrics returned by the API (Run ID: 2, Files: 2, Classes: 2, Edges: 1).

_(Notice that the `Run ID` incremented to `2`! This proves the DB isolation works accurately across multiple idempotent runs)._

---

## 5. Teardown & Reset

To cleanly shut down the environment:

```bash
docker compose down
```

### To Reset Phase 1 Completely:

If you want to blow away the database and clear all stored runs and graphs:

```bash
rm -rf data/*
```

The next time you run `docker compose up`, the API will automatically rebuild `app.db` containing empty tables.
