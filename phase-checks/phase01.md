Excellent.

If Phase 1 is complete, this is the most important moment so far.

You are not testing intelligence.
You are testing **architectural correctness and flow integrity**.

Phase 1 validates:

> Can the system move from raw files → graph → storage → API → UI reliably?

Let’s define exactly what you can and should test now.

---

# 🎯 WHAT PHASE 1 IS SUPPOSED TO PROVE

You should now have:

```
Files
   ↓
Minimal AST extraction
   ↓
Graph construction
   ↓
Run metadata persistence
   ↓
API response
   ↓
UI display
```

No centrality.
No risk.
No ranking.

So we test structural flow only.

---

# ✅ CATEGORY 1 — File Ingestion Tests

## 1️⃣ Valid Small PHP Project

Create a tiny test project:

**File A.php**

```php
class A {
    public function foo() {
        $b = new B();
        $b->bar();
    }
}
```

**File B.php**

```php
class B {
    public function bar() {}
}
```

### Expected Result:

* Files detected = 2
* Classes detected = 2
* Edges detected = 1 (A → B)

If edge = 0 → call detection failing
If edge >1 → duplicate detection issue

---

## 2️⃣ Empty Folder Test

Input: empty directory

Expected:

* Analysis does not crash
* Run marked COMPLETE or EMPTY
* Classes = 0
* Edges = 0

If system crashes → ingestion not robust.

---

## 3️⃣ Non-PHP Files Test

Add:

* README.md
* index.html

Expected:

* Ignored
* Only PHP counted

---

## 4️⃣ Malformed PHP File

Create file:

```php
class X {
    public function foo( {
```

Expected:

* Graceful failure handling
* Run marked FAILED (or partial)
* Error logged
* System does not crash

If container crashes → parsing not isolated.

---

# ✅ CATEGORY 2 — Graph Integrity Tests

After a successful run, verify:

---

## 5️⃣ Graph Node Count Matches Class Count

Load generated graph JSON manually.

Confirm:

* Node count == detected classes
* No phantom nodes

---

## 6️⃣ Edge Validity

For every edge:

* Both source and target must exist
* No edge references missing node

If exists → graph construction broken.

---

## 7️⃣ Duplicate Edge Test

Create file:

```php
class A {
    public function foo() {
        $b = new B();
        $b->bar();
        $b->bar();
    }
}
```

Expected:

* Only 1 edge A → B

If 2 edges → duplication problem.

---

# ✅ CATEGORY 3 — Persistence Tests

---

## 8️⃣ Run Separation Test

Run analysis twice.

Expected:

* Two distinct run IDs
* Two distinct JSON files
* Metadata separate
* No overwriting

---

## 9️⃣ Failure Isolation Test

Force a parsing error in one run.

Then run valid project.

Expected:

* First run marked FAILED
* Second run completes normally
* No cross-run contamination

---

## 🔟 DB Integrity Test

Inspect SQLite manually.

Confirm:

* analysis_run entries correct
* started_at populated
* completed_at populated
* status correct

---

# ✅ CATEGORY 4 — API Tests

---

## 11️⃣ POST /analyze

Test with:

* Valid input
* Invalid path
* Missing parameter

Confirm:

* Proper HTTP status codes
* No 500 unless true internal failure

---

## 12️⃣ Idempotency Behavior

If you send same folder twice:

Does it:

* Create new run? (Correct behavior)
* Or overwrite? (Wrong behavior)

Correct answer: New run.

---

# ✅ CATEGORY 5 — UI Tests

---

## 13️⃣ End-to-End UI Test

From Streamlit:

* Select project
* Run analysis
* See:

  * run ID
  * file count
  * class count
  * edge count

If UI freezes → async/response handling issue.

---

## 14️⃣ UI Error Display Test

If analysis fails:

Does UI:

* Show readable error?
* Or crash?

---

# ✅ CATEGORY 6 — Architectural Discipline Tests

These are subtle but critical.

---

## 15️⃣ Layer Violation Scan

Search your code:

* Does domain import sqlite?
* Does API import networkx directly?
* Does infrastructure know about graph logic?

If yes → architectural leakage.

Fix now, not later.

---

## 16️⃣ Rebuild Test

Delete:

* Containers
* data folder

Run:

```
docker compose up --build
```

If system restores fully → architecture stable.

If manual fixes required → Phase 1 incomplete.

---

# 🔥 MOST IMPORTANT TEST

### 17️⃣ Graph Serialization Stability

Run analysis twice on same files.

Compare JSON.

Expected:

* Identical structure
* Identical node IDs

If node IDs change → your ID generation is unstable.

That will destroy Phase 2 metrics later.

Fix immediately if unstable.

---

# 🎯 What You CANNOT Test Yet

You cannot test:

* Risk model correctness
* Centrality correctness
* Extraction ranking
* DB write attribution
* Metric normalization

Those belong to Phase 2+.

---

# 🧠 PHASE 1 VALIDATION CHECKLIST

You may proceed to Phase 2 only if:

* System survives malformed input
* Graph has no dangling edges
* Runs are isolated
* JSON deterministic
* Architecture boundaries respected
* No duplicate edges
* No crashes on edge cases

---

# 🚨 CRITICAL WARNING

The biggest hidden Phase 1 failure is:

> Unstable component identifiers.

If your node IDs depend on:

* Random ordering
* File iteration order
* Python dictionary ordering

Then Phase 2 centrality metrics will fluctuate.

Confirm deterministic ID generation now.

---



Excellent — this is a very practical and important clarification.

Right now in Phase 1, your system is:

* Dockerized
* Local-first
* FastAPI backend
* Streamlit frontend

So the question is:

> Do I test everything via the browser?
> Or how are files actually passed into the system?

Let’s break this down properly.

---

# 🔷 1️⃣ Where Does Phase 1 Testing Actually Happen?

Phase 1 testing happens in **three places**, not just the browser.

| Layer    | Where You Test           | Why                    |
| -------- | ------------------------ | ---------------------- |
| API      | Postman / curl / Swagger | Validate backend logic |
| Database | SQLite CLI / DB Browser  | Validate persistence   |
| UI       | Browser (Streamlit)      | Validate integration   |

The browser is only for integration testing.

Serious debugging should be done at API + filesystem level first.

---

# 🔷 2️⃣ How Are Files/Folders Mounted or Selected?

There are 3 valid approaches in Phase 1.

Which one you use depends on your current implementation.

---

# ✅ OPTION A — Mounted Local Folder (Recommended for Phase 1)

This is the cleanest approach.

In `docker-compose.yml`:

```yaml
volumes:
  - ./projects:/projects
  - ./data:/data
```

This means:

* Any folder you put inside `./projects` on your machine
* Becomes visible inside container at `/projects`

Example:

On your computer:

```id="p1"
/project-root/projects/test_project/
```

Inside Docker container:

```id="p2"
/projects/test_project/
```

---

### How Testing Works

1. Place test PHP files inside:

   ```
   ./projects/test_project/
   ```
2. In browser UI, input:

   ```
   /projects/test_project
   ```
3. Backend reads from mounted directory.

No file upload required.

This is the most stable method for Phase 1.

---

# ✅ OPTION B — Streamlit File Upload

You can implement:

```python
st.file_uploader(...)
```

But this has limitations:

* It uploads individual files
* Harder to handle full folder structure
* More memory-bound
* Less realistic for larger projects

Better suited for demo phase, not Phase 1 validation.

---

# ✅ OPTION C — API-Only Testing (Direct Path Submission)

You skip UI and call:

```
POST /analyze
{
  "project_path": "/projects/test_project"
}
```

Using:

* Swagger UI ([http://localhost:8000/docs](http://localhost:8000/docs))
* Postman
* curl

This is actually the best debugging method.

---

# 🔥 What You Should Be Doing Now (Correct Workflow)

### Step 1 — Use Mounted Folder Strategy

Have:

```
project-root/
  projects/
    test1/
    test2/
```

---

### Step 2 — Test via API First

Go to:

```
http://localhost:8000/docs
```

Use:

```
POST /analyze
```

Send:

```json
{
  "project_path": "/projects/test1"
}
```

Confirm backend works BEFORE touching UI.

---

### Step 3 — Check DB

Open SQLite manually.

Confirm run stored.

---

### Step 4 — Check JSON Graph

Open:

```
/data/graph_<run_id>.json
```

Confirm structure correct.

---

### Step 5 — Then Test via Streamlit

Only after backend validated.

---

# 🔷 What Is NOT Happening

You are NOT:

* Browsing your entire filesystem from browser
* Directly accessing local disk from frontend
* Running analysis purely client-side

All analysis runs inside backend container.

Frontend only sends request.

---

# 🔷 Important Concept

The browser cannot see your filesystem.

Only the backend container can see mounted volumes.

So folder selection in UI must refer to container paths like:

```
/projects/test1
```

Not:

```
C:\Users\...
```

---

# 🔥 If You Are Currently Typing Windows Paths in Browser

Like:

```
C:\Users\Dio\Desktop\project
```

That will not work inside Docker.

You must mount that directory.

Example:

```yaml
volumes:
  - C:/Users/Dio/Desktop/project:/projects/input
```

Then inside API use:

```
/projects/input
```

---

# 🔷 What Phase 1 Testing Should Look Like Practically

### On your machine:

```id="layout"
/project-root
  ├── projects
  │     └── test_project
  │            ├── A.php
  │            └── B.php
  ├── data
  ├── api
  ├── frontend
  └── ...
```

Then:

* Start Docker
* Open Swagger
* Call analyze with `/projects/test_project`
* Inspect results

That’s Phase 1 validation.

---

# 🎯 Recommended Setup For You

Since you’re in Tanzania on a Linux environment (from metadata), simplest:

```yaml
volumes:
  - ./projects:/projects
  - ./data:/data
```

Keep everything local.

No cloud storage.
No remote uploads.
No complexity.

---

# 🚨 Critical Warning

Do NOT implement complex file upload + zip extraction yet.

That belongs in:

Phase 8 (demo polish).

---

# 🎯 Final Clarification

So answer to your question:

> Is all this testing done in browser?

No.

Proper testing is:

1. API first (Swagger)
2. File system inspection
3. DB inspection
4. UI integration last

---

Now I need to know:

How are you currently passing project paths?

A) Mounted folder volume
B) File uploader
C) Hardcoded test path
D) Something else

Tell me — and I’ll tell you if it’s architecturally correct for Phase 1.
