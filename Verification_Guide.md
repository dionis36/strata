# Verification Guide: Strata UX & Architecture Remediation

This guide provides step-by-step instructions to verify that all critical flaws (F01–F13) and secondary bugs (NEW-01–NEW-08) identified in the UX Evaluation Report have been successfully resolved. The application is now fully demo-safe and stable.

---

## Part 1: Critical Stability & Routing

### 1. The Database Intelligence Crash (F01)
**How to verify:**
1. Navigate to the **Database Intelligence** page from the sidebar.
2. Verify the page loads successfully without throwing an `IndexError`.
3. Check the tabs: The non-existent "Domain Model" tab has been safely bypassed and the crash logic removed.

### 2. Navigation & Label Consistency (F02, F03)
**How to verify:**
1. Look at the sidebar nav item **Legacy Bootstrapper**. Click it. Verify the page title is exactly `Legacy Bootstrapper` (it is no longer "Modernization Factory").
2. Look at the sidebar nav item **Modernization Risk**. Click it. Verify the page title is exactly `Modernization Risk` (it is no longer "Security & Risk Audit").
3. Go to **Boundary Intelligence**. Click the "Analyze Structural Risk" buttons. Verify they seamlessly navigate to Modernization Risk without visual stutter.

### 3. Dead-End States & Fragile Routing (F04, F05)
**How to verify:**
1. In the sidebar Context Switcher, select a state that causes no data to load, or temporarily stop your backend server.
2. Click through any of the analysis pages (e.g., *Database Intelligence*).
3. Verify you see a warning block with a native **"← Go to Executive Dashboard"** button that actually works, rather than being stranded with plain text.

### 4. Global Context Switcher (F10)
**How to verify:**
1. Look at the top of the sidebar.
2. Verify the dropdown now clearly says **"Select Workspace / Run"** and is cleanly isolated by horizontal lines. It is no longer "visually collapsed."
3. If you stop the backend API, verify it displays a red "API Unreachable" error with a retry button, rather than a tiny, ignorable caption.

---

## Part 2: UX, Visuals & Taxonomy

### 5. Standardized Severity Taxonomy (F08)
**How to verify:**
1. Go to **Modernization Risk**. Verify the top KPI cards say "Critical", "High", "Medium", "Stable" (It no longer contradicts itself with "Moderate").
2. Go to **Monolith Navigator** -> OOP table. Verify the "Complexity" column uses the exact same 4-tier scale (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) instead of the old 3-tier string scale.

### 6. Executive Dashboard Polish (F09, Group 9)
**How to verify:**
1. Go to the **Executive Dashboard**.
2. Hover over the 5 metrics (Total Files, Avg Complexity, etc.) to see the newly added **tooltips (`?`)** explaining what the metrics mean.
3. Verify the **Avg Complexity** metric shows a green "Healthy" or red "Elevated" semantic delta directly beneath it, providing instant context.

### 7. Graceful Graph Fallbacks (F07)
**How to verify:**
1. Go to **Extraction Simulator**.
2. Run a simulation that generates a massive blast radius (>500 nodes).
3. Verify that instead of a blank screen, you see a warning followed by two clean **data tables** detailing the Upstream and Downstream dependencies. You are never left without data.

### 8. Inline Mermaid Diagrams (F12)
**How to verify:**
1. Go to **Extraction Simulator**.
2. Run a simulation, then click the **To-Be Ghost Graph** tab.
3. Verify that the flowchart renders as an actual visual diagram, rather than a wall of syntax-highlighted code.

### 9. Blind Tab Navigation (F13)
**How to verify:**
1. Click through pages like **Risk Audit**, **Database Intelligence**, or **Legacy Intelligence**.
2. Verify the tabs now contain dynamic count badges (e.g., `Security Vulnerability Log (14)`), preventing users from clicking into empty tabs.

### 10. Data Table UX & Search (Group 9)
**How to verify:**
1. Go to **Layered Structure**. Verify there is a native `🔍 Search files...` text box that dynamically filters the massive directory tree below it.
2. Go to **Modernization Risk**. Verify the previously unreadable 12-column table is now cleanly split into a **Core Risk Profile** table and a **Detailed Complexity Metrics** table, eliminating horizontal scrolling.

---

## Part 3: Under-the-Hood Fixes

### 11. Concurrency & Hardcoded Paths (NEW-04)
**How to verify (Code Level):**
1. Check `extraction_simulator.py` and `layered_architecture.py`. Verify that temporary HTML saves now use `/tmp/graph_{run_id}.html` to prevent multi-user collisions if two users run the app simultaneously.
2. Verify the topology graph uses `os.getenv("DATA_DIR")` instead of a hardcoded `/data/` path, ensuring it works on cloud deployments.

### 12. Destructive Action Confirmations (F11)
**How to verify:**
1. Go to the **Dashboard** and click **Re-Scan**.
2. Go to **Artifact Center** and click **Sync with Database**.
3. Verify both actions now trigger a centered popup dialog asking for confirmation before firing.

### 13. Automated Status Polling (F06)
**How to verify:**
1. Go to the **Artifact Center**.
2. Trigger an analysis or synthesis run.
3. Verify that the system automatically loops and refreshes (`*(Auto-refreshing status every 3 seconds...)*`) without requiring you to manually mash a "Refresh" button.
