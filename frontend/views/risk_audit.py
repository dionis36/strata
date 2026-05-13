import streamlit as st
import requests
import pandas as pd
import os
import json

def show_risk_audit():
    st.title("Modernization Risk Audit")
    st.markdown("### Structural & Behavioral Risk Quantization")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=300, show_spinner=False)
    def fetch_risk(rid):
        r = requests.get(f"{FASTAPI_URL.rstrip('/')}/risk/{rid}", timeout=30)
        r.raise_for_status()
        return r.json().get("components", [])

    components = fetch_risk(run_id)

    if not components:
        st.info("No risk telemetry data available for the selected run.")
        return

    # --- Informative Context ---
    with st.expander("Understanding the Risk DNA", expanded=False):
        st.markdown("""
        The **Modernization Risk Score** is a composite metric derived from two distinct architectural vectors:
        
        *   **🏗️ Structural Risk**: Measures the 'Gravity' and 'Blast Radius' of a component. High betweenness centrality or deep dependency chains increase this score.
        *   **🗄️ Behavioral Factor**: Measures the 'Churn' and 'Side-Effects'. Frequent database writes or global state mutations multiply the structural risk.
        *   **📊 Blast Radius**: The percentage of the system that would be structurally impacted if this component was modified or extracted.
        *   **🎯 Criticality Index**: How essential this component is to the overall system connectivity.
        """)

    # --- KPI Overview ---
    lvl_counts = {l: sum(1 for c in components if c["risk_level"] == l) for l in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
    LEVEL_ICON = {"CRITICAL": "🔴 Critical", "HIGH": "🟠 High", "MEDIUM": "🟡 Medium", "LOW": "🟢 Stable"}
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Critical Assets", lvl_counts["CRITICAL"], delta="Urgent Action")
    k2.metric("High Instability", lvl_counts["HIGH"], delta="Careful Extraction")
    k3.metric("Moderate Coupling", lvl_counts["MEDIUM"])
    k4.metric("Stable Entities", lvl_counts["LOW"], delta="Safe Candidate")

    st.markdown("---")
    
    # --- Full Matrix ---
    rows = []
    for c in components:
        rows.append({
            "Component": c.get("name", ""),
            "Structural Risk": c.get("risk_score", 0.0),
            "Behavioral Factor": c.get("behavioral_factor", 0.0),
            "Final Risk": c.get("final_risk", 0.0),
            "Status": LEVEL_ICON.get(c.get("risk_level"), c.get("risk_level")),
            "Blast Radius": c.get("norm_blast_radius", 0.0),
            "Criticality": c.get("criticality_index", 0.0)
        })

    df = pd.DataFrame(rows).sort_values("Final Risk", ascending=False)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Final Risk": st.column_config.ProgressColumn("Risk Magnitude", min_value=0, max_value=1, format="%.3f"),
            "Status": st.column_config.TextColumn("Risk Classification"),
            "Blast Radius": st.column_config.NumberColumn("Blast Radius", format="%.3f"),
            "Criticality": st.column_config.NumberColumn("Criticality", format="%.3f")
        }
    )

    st.markdown("---")
    st.download_button("Export Risk Matrix (JSON)", json.dumps(components, indent=2), file_name=f"risk_{run_id}.json")

if __name__ == "__main__":
    show_risk_audit()
