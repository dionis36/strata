import streamlit as st
import requests
import pandas as pd
import os
import json

def show_risk_audit():
    st.title("Security & Risk Audit")
    st.markdown("##### Maintainability Index · Security Sinks · Architectural Deficits")

    with st.expander("💡 About the Security & Risk Audit", expanded=True):
        st.markdown("""
        This view is the **Technical Debt & Security Ledger** of the platform. It translates the 
        structural flaws of the codebase into prioritized, actionable risk registers.
        
        It utilizes a **Deterministic Threshold Engine**: raw metrics extracted from the Abstract Syntax Tree (AST) 
        are compared against industry-standard limits (e.g., maximum Cyclomatic Complexity, minimum Maintainability Index) 
        to mathematically prove the Risk Magnitude (CRITICAL / HIGH / MEDIUM).
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
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

    # Apply Emojis to Risk Magnitudes
    LEVEL_ICON = {"CRITICAL": "🔴 CRITICAL", "HIGH": "🟠 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW"}
    
    lvl_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in file_matrix:
        raw_risk = f.get("Overall Risk", "LOW")
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
    k1.metric("🔴 Critical Risk Files", lvl_counts["CRITICAL"], delta="Urgent Action", delta_color="inverse", help="Files containing active security sinks or extreme complexity.")
    k2.metric("🟠 High Risk Files", lvl_counts["HIGH"], delta="Careful Extraction", delta_color="inverse", help="Files with high structural complexity.")
    k3.metric("🟡 Moderate Risk Files", lvl_counts["MEDIUM"])
    k4.metric("🟢 Stable Files", lvl_counts["LOW"], delta="Safe Candidate", delta_color="normal")

    st.markdown("---")

    tabs = st.tabs([
        "📋 The File-Level Risk Matrix",
        "🛡️ Security Vulnerability Log",
        "🏗️ Architectural Rot & Extensibility",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 — File-Level Risk Matrix
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### The Risk Matrix (Wide Table)")
        st.caption(
            "Every file scored against the Maintainability Index and Cyclomatic Complexity standard. "
            "Sort by any column to find the most structurally dangerous components."
        )

        if file_matrix:
            df_matrix = pd.DataFrame(file_matrix)
            st.dataframe(
                df_matrix,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "File Name": st.column_config.TextColumn("File Path", width="large"),
                    "Overall File Risk": st.column_config.TextColumn("Overall File Risk", help="CRITICAL if Security Sinks > 0 or CC > 20"),
                    "Maintainability Index": st.column_config.ProgressColumn("Maintainability (0-100)", min_value=0, max_value=100, format="%d"),
                    "Cyclomatic Complexity": st.column_config.NumberColumn("Cyclomatic Complexity"),
                    "Security Sinks": st.column_config.NumberColumn("Sinks"),
                    "Global Accesses": st.column_config.NumberColumn("Global Accesses"),
                }
            )
        else:
            st.info("No file metrics available.")

        # Insight Block
        high_cc = sum(1 for f in file_matrix if f.get("Cyclomatic Complexity", 0) > 15)
        avg_mi = kpis.get("Average Maintainability", 0)
        st.markdown("---")
        st.info("#### 📋 File Risk Assessment")
        st.markdown("**METRIC**: Maintainability Index & Cyclomatic Complexity")
        st.markdown(
            "**INTERPRETATION**: The Maintainability Index (MI) calculates the relative ease of maintaining the code. "
            "An MI below 50 indicates that a file is too convoluted to safely refactor without causing regressions. "
            "Cyclomatic Complexity measures the number of decision branches (if/else/for) inside the file. Industry standard maximum is 15."
        )
        st.markdown(
            f"**EVIDENCE**: There are `{high_cc}` files in this codebase with a Cyclomatic Complexity exceeding the maximum threshold of 15. "
            f"The codebase average Maintainability Index is `{avg_mi}/100`."
        )
        st.markdown(
            "**RECOMMENDATION**: Do not attempt to automatically migrate or refactor files with an MI below 50 or CC above 20. "
            "They must be manually audited and heavily unit-tested before extraction, or entirely rewritten (Strangler Fig pattern)."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 — Security Vulnerability Log
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
            st.success("✅ No critical security sinks (eval, unsafe includes, etc.) detected.")

        # Insight Block
        st.markdown("---")
        total_vulns = len(vulns)
        rce_count = sum(1 for v in vulns if v.get("Vulnerability Type") == "DANGER")
        st.warning("#### 🛡️ Security Assessment") if total_vulns > 0 else st.success("#### 🛡️ Security Assessment")
        st.markdown("**METRIC**: Detected Security Sinks (RCE, SQLi, LFI)")
        st.markdown(
            "**INTERPRETATION**: This registry lists exact occurrences of highly dangerous PHP functions. "
            "`DANGER` indicates Remote Code Execution (RCE) vectors like `eval()` or `exec()`. "
            "`INCLUDE_ROUTING` indicates Local File Inclusion (LFI) via variable-based includes."
        )
        st.markdown(
            f"**EVIDENCE**: `{total_vulns}` critical security incidents logged. `{rce_count}` instance(s) of potential RCE (`DANGER`) detected."
        )
        st.markdown(
            "**RECOMMENDATION**: Immediate remediation required. Security sinks cannot be migrated to a modern microservice. "
            "Any file listed here containing `DANGER` must have the `eval/exec` removed and replaced with standard language constructs."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 — Architectural Rot
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Architectural Debt & Extensibility Blockers")
        st.caption("Structural violations that prevent automated refactoring or containerization. **HIGH** indicates a severe blocker (e.g., extreme global coupling, missing PSR-4 autoloading).")

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
            st.success("✅ No severe architectural rot detected.")

        # Insight Block
        st.markdown("---")
        total_rot = len(rot)
        st.info("#### 🏗️ Extensibility Assessment")
        st.markdown("**METRIC**: Global State Coupling & Structural Anti-Patterns")
        st.markdown(
            "**INTERPRETATION**: Architectural rot represents design choices that actively block modernization. "
            "For example, 'Global State Coupling' means a file relies heavily on `$GLOBALS`, making it impossible to unit test in isolation. "
            "Defining multiple classes in a single file breaks PSR-4 autoloading, a prerequisite for Composer adoption."
        )
        st.markdown(
            f"**EVIDENCE**: `{total_rot}` instances of architectural debt recorded. See the 'Impact' column for exact technical blockers."
        )
        st.markdown(
            "**RECOMMENDATION**: Prioritize resolving 'Multiple Classes per File' first by splitting them into separate files. "
            "Then, begin injecting the required `$GLOBALS` via constructor injection to break the temporal coupling."
        )

if __name__ == "__main__":
    show_risk_audit()
