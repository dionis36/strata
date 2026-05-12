
# Strata: The Master User Workflow Guide

Strata is a specialized **Modernization Advisory Platform**. This guide outlines the end-to-end journey an architect takes to move a legacy monolith from "Unknown Risk" to a "Verified Modernization Strategy."

---

## 📂 Step 1: Data Provisioning (Host-Side)
Strata analyzes code directly from your filesystem. It does **not** require you to upload source code through a web browser, ensuring your intellectual property remains within your controlled environment.


1.  **The "In-Box" Method (Recommended)**: Simply copy or move your monolith directory into the `data/` folder of the Strata project on your host.
    - *Result*: It will automatically appear inside the Strata container at `/data/your-monolith-name`.
2.  **The "Live Mount" Method**: If you prefer to keep your code in its original location, add a volume mapping to the `api` service in `docker-compose.yml` (e.g., `- /path/to/my/project:/data/my-project`).

3.  **Stability Check**: Strata is built for **Ancient Monoliths**. It supports codebases ranging from **PHP 5.x to PHP 8.x**. Even if your code is too old to run on modern servers, Strata can still parse it and provide a modernization roadmap.

---

## 🚀 Step 2: Analysis Ignition (The Dashboard)
Once your files are provisioned, you trigger the **Intelligence Engine**.

1.  **Access the Hub**: Open your browser to the Strata Landing Page (typically `http://localhost:8501`).
2.  **Identify Project**: Enter the **Source Path** (as seen by the container, e.g., `/data/monolith`) and a **Project Name**.
3.  **Execute Scan**: Click **"Run Deep Intelligence Scan"**.
    -   *Behind the scenes*: Strata activates its Parallel Parsing Pipeline, calculates systemic risk, and builds the Topological Manifest.

---

## 🕸️ Step 3: Immersive Discovery (The Navigator)
With the analysis complete, you begin the exploration phase to find the "God Objects" and architectural bottlenecks.

1.  **Open Navigator**: Select **"Monolith Navigator"** from the sidebar.
2.  **Interpret Heatmaps**: Look for **Red Nodes** (High Systemic Risk). These are your primary candidates for modernization or immediate refactoring.
3.  **Audit Dependencies**: Hover over nodes to see their **Fully Qualified Name (FQN)** and **Risk Coefficients**. Use the interactive drag-and-zoom to understand the "Gravity" of your architecture.

---

## 🕹️ Step 4: Surgical Planning (The Cockpit)
This is where "Insight" becomes "Action." You use the **Modernization Cockpit** to simulate the future state of your system.

1.  **Open Cockpit**: Select **"Modernization Cockpit"** from the sidebar.
2.  **Select Strategy**: Choose an **Extraction Candidate** from the prioritized list. Strata ranks these based on their "Decoupling ROI."
3.  **Simulate Extraction**: Inspect the **Topological Foresight** graph. This shows you the "Ghost Architecture"—how the system will look after the component is moved to its own service.
4.  **Verify Safety**: Check the **Acyclic Guarantee** and **Risk Delta**. If the system shows a "Risk Reduction," your plan is mathematically sound.

---

## 📋 Step 5: Finalization & Reporting
The final step is to generate the professional documentation required to execute the plan and gain stakeholder consensus.

1.  **Generate Protocol**: Review the **Surgical Implementation Protocol**. This provides the step-by-step logic for the code transformation.
2.  **Export Technical Blueprint (.md)**: Download the Markdown file. Commit this directly to your repository or include it in your Technical RFC.
3.  **Download Executive Summary (.pdf)**: Download the professional PDF report. This contains the **Modernization ROI %** and **Risk Heatmaps** designed for non-technical leadership.

---

## 🏁 Summary: From Monolith to Modernized
By following this workflow, you transition from **Architectural Uncertainty** to a **Surgical Modernization Blueprint** backed by technical determinism and executive-ready documentation.
