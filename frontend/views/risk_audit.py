import streamlit as st
import requests
import pandas as pd
import os
import json
from views import page_registry
from views.severity import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW

def show_risk_audit():
    st.title("Modernization Risk")
    st.markdown("##### Maintainability Index · Security Sinks · Architectural Deficits")

    with st.expander("Security & Risk Audit Blueprint Key", expanded=True):
        st.markdown("""
        This view is the **Technical Debt & Security Ledger** of the platform. It translates the 
        structural flaws of the codebase into prioritized, actionable risk registers using a **Deterministic Threshold Engine**.
        
        ### Risk Matrix Metric Glossary
        * **Test Coverage**: The percentage of the file's logic executed during automated testing. **Note:** In legacy systems, this often displays as `N/A`, indicating the complete absence of unit tests for the module.
        * **Maintainability Index (MI)**: A composite score (0-100) calculating how difficult the file is to support based on volume and logic. Below 65 is dangerous; below 25 is unmaintainable.
        * **Cyclomatic Complexity (CC)**: The count of distinct logical branches (if, else, loops). A CC over 15 indicates a module that is extremely difficult to test and risky to modify.
        * **Max Nesting Depth**: How deeply logic is indented. Deep nesting (e.g., > 4) exponentially increases developer cognitive load.
        * **Max Method LOC**: The Lines of Code in the single largest function. Massive functions hide business logic and block independent extraction.
        * **Fan-Out**: The number of external modules this file depends on. High fan-out equals high coupling-you cannot easily extract this file without breaking things.
        * **Security Sinks**: Dangerous execution vectors (e.g., `eval`, raw SQL, dynamic includes) found in the AST. 
        * **Global Accesses**: Reliance on global runtime state. This explicitly prevents safe containerization and makes unit testing impossible without heavy mocking.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    @st.cache_data(ttl=60)
    def fetch_security_risk(rid):
        res = requests.get(f"{FASTAPI_URL}/security-risk/{rid}", timeout=30)
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_security_risk(run_id)
    if not data or "file_matrix" not in data:
        st.error("Could not retrieve security & risk data.")
        return

    kpis = data.get("kpis", {})
    file_matrix = data.get("file_matrix", [])
    vulns = data.get("vulnerabilities", [])
    rot = data.get("architectural_rot", [])

    # Text labels for Risk Magnitudes
    LEVEL_ICON = {SEVERITY_CRITICAL: SEVERITY_CRITICAL, SEVERITY_HIGH: SEVERITY_HIGH, SEVERITY_MEDIUM: SEVERITY_MEDIUM, SEVERITY_LOW: SEVERITY_LOW}
    
    lvl_counts = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0}
    for f in file_matrix:
        raw_risk = f.get("Overall Risk", SEVERITY_LOW)
        if raw_risk in lvl_counts:
            lvl_counts[raw_risk] += 1
        f["Overall File Risk"] = LEVEL_ICON.get(raw_risk, raw_risk)
        f.pop("Overall Risk", None) # Remove old key to prevent duplication
        
    for v in vulns:
        v["Vulnerability Severity"] = LEVEL_ICON.get(v.get("Risk Magnitude", "LOW"), v.get("Risk Magnitude"))
        v.pop("Risk Magnitude", None)

    for r in rot:
        r["Blocker Severity"] = LEVEL_ICON.get(r.get("Risk Magnitude", "LOW"), r.get("Risk Magnitude"))
        r.pop("Risk Magnitude", None)

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Critical Risk Files", lvl_counts[SEVERITY_CRITICAL], delta="Urgent Action", delta_color="inverse", help="Files containing active security sinks or extreme complexity. These are immediate blockers — do not attempt extraction until they are stabilized.")
    k2.metric("High Risk Files", lvl_counts[SEVERITY_HIGH], delta="Careful Extraction", delta_color="inverse", help="Files with high structural complexity. They can be extracted but require careful dependency mapping and a robust test harness first.")
    k3.metric(
        "Medium Risk Files",
        lvl_counts[SEVERITY_MEDIUM],
        help="Files with moderate structural complexity or isolated security concerns. They require careful code review before extraction but are not immediate blockers."
    )
    k4.metric(
        "Stable Files",
        lvl_counts[SEVERITY_LOW],
        delta="Safe Candidate",
        delta_color="normal",
        help="Files with low cyclomatic complexity, no security sinks, and a high Maintainability Index. These are the safest candidates for early extraction or direct reuse in a new service."
    )

    st.markdown("---")

    tabs = st.tabs([
        f"The File-Level Risk Matrix ({len(file_matrix)})",
        f"Security Vulnerability Log ({len(vulns)})",
        f"Architectural Rot & Extensibility ({len(rot)})",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 - File-Level Risk Matrix
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### The Risk Matrix (Wide Table)")
        st.caption(
            "Every file scored against the Maintainability Index and Cyclomatic Complexity standard. "
            "Sort by any column to find the most structurally dangerous components."
        )

        if file_matrix:
            df_matrix = pd.DataFrame(file_matrix)
            st.markdown("##### Core Risk Profile")
            st.dataframe(
                df_matrix[["File Name", "Overall File Risk", "Maintainability Index", "Test Coverage", "Security Sinks"]],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "File Name": st.column_config.TextColumn("File Path", width="large"),
                    "Overall File Risk": st.column_config.TextColumn("Overall File Risk", help="CRITICAL if Security Sinks > 0 or CC > 20"),
                    "Maintainability Index": st.column_config.ProgressColumn("Maintainability (0-100)", min_value=0, max_value=100, format="%d"),
                    "Test Coverage": st.column_config.TextColumn("Coverage"),
                    "Security Sinks": st.column_config.NumberColumn("Sinks")
                }
            )
            
            st.markdown("##### Detailed Complexity Metrics")
            st.dataframe(
                df_matrix[["File Name", "Cyclomatic Complexity", "Max Nesting Depth", "Max Method LOC", "Fan-Out", "Global Accesses", "Domain Archetype", "Semantic Multiplier"]],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "File Name": st.column_config.TextColumn("File Path", width="large"),
                    "Cyclomatic Complexity": st.column_config.NumberColumn("Cyclomatic Complexity", help="Count of distinct logical branches (if, else, loops, catches). CC > 15 means the file is extremely difficult to test and risky to modify safely."),
                    "Max Nesting Depth": st.column_config.NumberColumn("Nesting Depth", help="Max depth of nested loops and conditionals. Depth > 4 exponentially increases cognitive load and makes logic nearly impossible to trace without a debugger."),
                    "Max Method LOC": st.column_config.NumberColumn("Method LOC", help="Lines of Code in the single largest method or function. Massive methods hide multiple responsibilities — each is a refactoring and testing blocker."),
                    "Fan-Out": st.column_config.NumberColumn("Fan-Out", help="The number of external files or modules this file directly depends on. High fan-out means this file cannot be moved or extracted without also moving everything it depends on."),
                    "Global Accesses": st.column_config.NumberColumn("Global Accesses", help="How many times this file reads from PHP superglobals or global scope. A direct measure of hidden runtime coupling — prevents safe unit testing or containerization."),
                    "Domain Archetype": st.column_config.TextColumn("Archetype", help="The engine's classification of this file's role: ENTITY (domain object), CONTROLLER (request handler), UTILITY (stateless helper), or GOD_CLASS (monolithic bottleneck)."),
                    "Semantic Multiplier": st.column_config.NumberColumn("Risk Multiplier", help="An AI-adjusted weight applied based on the file's detected role (e.g., authentication, routing). Files in high-stakes architectural positions receive a higher multiplier to surface them in priority rankings.")
                }
            )
        else:
            st.info("No file metrics available.")

        # Insight Block
        high_cc = sum(1 for f in file_matrix if f.get("Cyclomatic Complexity", 0) > 15)
        critical_count = lvl_counts["CRITICAL"]
        total_files = len(file_matrix)
        avg_mi = kpis.get("Average Maintainability", 0)
        critical_pct = f"{(critical_count / total_files * 100):.1f}" if total_files > 0 else "0"
        st.markdown("---")
        st.markdown("#### File Risk Assessment")
        st.info("Maintainability Index (MI) & Cyclomatic Complexity (CC) — per-file composite structural scoring.", icon=":material/info:")
        st.markdown("**METRIC**: Maintainability Index (MI) & Cyclomatic Complexity (CC) - per-file composite scoring")
        st.markdown(
            f"**INTERPRETATION**: This codebase has an average Maintainability Index of **{avg_mi}/100**. "
            f"Of the {total_files} files analyzed, **{critical_count} ({critical_pct}%) are classified as CRITICAL** - "
            "meaning they combine structural complexity and active security risk in a way that makes safe, automated extraction mathematically improbable. "
            "The Cyclomatic Complexity metric specifically counts decision branches (if/else, loops, catches) - each branch is a separate path a test must cover. "
            "High CC files are not just risky to change; they are expensive to verify after a change."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. `{high_cc}` files exceed the industry-maximum CC threshold of 15 - each one represents a refactoring blocker that requires manual decomposition before it can be safely extracted.\n"
            f"2. The codebase average MI is `{avg_mi}/100`. An MI below 65 is considered 'difficult to maintain'; below 25 is 'unmaintainable' by industry standard (SEI).\n"
            f"3. Sort the matrix by **Sinks** to reveal which high-complexity files also carry active security vulnerabilities - these are your highest-risk intersection points."
        )
        st.markdown(
            "**RECOMMENDATION**: The Risk Matrix above is your structural map. Before moving to the Security or Architectural tabs, "
            "study which files cluster at the intersection of high CC and low MI - those files represent the tightest coupling in the system. "
            "Understanding their role (is this a router, a model, a helper?) will clarify whether they are candidates for extraction or for wrapping."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 - Security Vulnerability Log
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        st.markdown("#### Security Incident Registry")
        st.caption("Discrete security vulnerabilities detected in the AST. **CRITICAL** indicates active remote exploits (RCE, SQLi, LFI). **HIGH** indicates secondary risks (e.g., weak cryptography).")

        if vulns:
            df_vulns = pd.DataFrame(vulns)
            st.dataframe(
                df_vulns,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Vulnerability Severity": st.column_config.TextColumn("Severity")
                }
            )
        else:
            st.success("No critical security sinks (eval, unsafe includes, etc.) detected.", icon=":material/check_circle:")

        # Insight Block
        st.markdown("---")
        total_vulns = len(vulns)
        rce_count = sum(1 for v in vulns if v.get("Vulnerability Type") == "DANGER")
        sqli_count = sum(1 for v in vulns if v.get("Vulnerability Type") == "MYSQL_LEGACY")
        lfi_count = sum(1 for v in vulns if v.get("Vulnerability Type") == "INCLUDE_ROUTING")
        st.markdown("#### Security Assessment")
        if total_vulns > 0:
            st.warning(f"{total_vulns} confirmed security sink(s) detected — RCE, SQLi, or LFI vectors present.", icon=":material/warning:")
        else:
            st.success("No active security sinks detected in this analysis.", icon=":material/check_circle:")
        st.markdown("**METRIC**: AST-detected Security Sinks - functions or patterns that directly enable a known attack class")
        if total_vulns > 0:
            st.markdown(
                f"**INTERPRETATION**: This codebase contains **{total_vulns} confirmed security sink instances**. "
                "The engine has performed a **Taint Flow Discovery** pass: for each sink, it attempted to trace a logical path back to a known entry point (URL or Direct Script). "
                "A sink with a confirmed 'Flow Trace' is exponentially more dangerous because it proves an execution path exists from the external surface to the vulnerability. "
                "The presence of `DANGER` sinks (`eval`, `exec`) with a Flow Trace means the application is likely vulnerable to Remote Code Execution."
            )
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. **{rce_count} RCE vector(s)** detected. Check the 'Evidence' column for 'Flow Trace' to see the data entry point.\n"
                f"2. **{sqli_count} deprecated MySQL API** usage(s). These lack protection and are high-priority for removal.\n"
                f"3. **{lfi_count} dynamic include(s)**. These are candidates for Local File Inclusion if path variables are attacker-controlled."
            )
            st.markdown(
                "**RECOMMENDATION**: Notice how the sinks in this registry map onto specific files in the Risk Matrix. "
                "Cross-reference the **File** column above with the Tab 1 matrix - files that appear in both the 'CRITICAL' risk row *and* this security log "
                "are your highest-priority stabilization targets before any modernization work can begin. The Security tab reveals *what* the risk is; the Matrix reveals *how structurally difficult* fixing it will be."
            )
        else:
            st.markdown("**INTERPRETATION**: No active security sinks were detected in this analysis. This indicates the codebase does not directly use the most dangerous PHP constructs (`eval`, `exec`, legacy `mysql_*`).")
            st.markdown("**EVIDENCE**: 0 security sinks detected across all scanned files.")
            st.markdown("**RECOMMENDATION**: Proceed to the Architectural Rot tab to assess the structural blockers that remain even in a clean codebase - complexity and coupling are often the more costly problem to resolve than security.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 - Architectural Rot
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Architectural Debt & Extensibility Blockers")
        st.caption("Structural violations that prevent automated refactoring or containerization. **HIGH** indicates a severe blocker (e.g., extreme global coupling, missing PSR-4 autoloading).")

        # --- Extraction Feasibility UI ---
        st.markdown("##### Extraction Feasibility Profiles")
        st.markdown("The system runs composite 'Strong Logic' heuristics to determine the exact extraction friction of a module.")
        
        blockers = [r for r in rot if r.get("Defect Type") in ["High Refactor Risk", "Microservice Extraction Blocker"]]
        if blockers:
            for b in blockers[:5]:
                with st.container():
                    st.error(f"**{b.get('File')}** Extraction Profile")
                    st.markdown(f"**Evidence:** {b.get('Impact')}")
                    st.markdown(f"**Conclusion:** Direct microservice extraction is **{b.get('Blocker Severity', 'High Risk')}**.")
            st.markdown("---")
        else:
            st.success("No modules detected with High Refactor Risk or Microservice Extraction Blockers.", icon=":material/check_circle:")
            st.markdown("---")

        if rot:
            df_rot = pd.DataFrame(rot)
            st.dataframe(
                df_rot,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Blocker Severity": st.column_config.TextColumn("Severity")
                }
            )
        else:
            st.success("No severe architectural rot detected.", icon=":material/check_circle:")

        # Insight Block
        st.markdown("---")
        total_rot = len(rot)
        global_coupling = sum(1 for r in rot if r.get("Defect Type") == "Global State Coupling")
        multi_class = sum(1 for r in rot if r.get("Defect Type") == "Multiple Classes per File")
        dead_code = sum(1 for r in rot if r.get("Defect Type") == "Potential Dead Code")
        blocker_count = sum(1 for r in rot if r.get("Defect Type") in ["High Refactor Risk", "Microservice Extraction Blocker"])
        st.markdown("#### Extensibility Assessment")
        st.info("Composite structural anti-patterns — Global State coupling, Dead Code, and PSR violations.", icon=":material/info:")
        st.markdown("**METRIC**: Composite Structural Anti-Patterns - Global State, Dead Code, and PSR violations")
        st.markdown(
            f"**INTERPRETATION**: This codebase carries **{total_rot} architectural debt instances**. "
            "The engine has added a **Dead Code Heuristic**: it identifies 'Orphaned Files' that have zero incoming connections and are not registered entry points. "
            f"**{dead_code} files** are candidates for immediate deletion, reducing the migration surface area. "
            f"**{global_coupling} files** are tightly coupled to global state, blocking isolation."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. **{dead_code} Potential Dead Code file(s)** - orphaned components with zero incoming dependency edges.\n"
            f"2. **{global_coupling} Global State Coupling instance(s)** - hidden runtime dependencies blocking unit testing.\n"
            f"3. **{blocker_count} Composite Extraction Blocker(s)** - high-complexity/high-coupling nodes that failed extraction logic."
        )
        st.markdown(
            "**RECOMMENDATION**: Consider the Extraction Feasibility Profiles above as your primary discovery output from this tab. "
            "Before any further analysis, ask: do the modules listed as 'High Refactor Risk' correspond to features you intend to extract early? "
            "If so, those files reveal the minimum set of dependencies you must untangle *first* - understanding their structure is the prerequisite for planning extraction in the Strategic Advisory module."
        )
        if st.button("Map External Boundaries"):
            st.switch_page(page_registry.PAGE_BOUNDARY_INTELLIGENCE)

if __name__ == "__main__":
    show_risk_audit()
