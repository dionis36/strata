import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

def show_extraction_simulator():
    st.title("Extraction Simulation")
    st.markdown("### Surgical Modernization Protocol")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=300, show_spinner=False)
    def fetch_candidates(rid):
        try:
            r = requests.get(f"{FASTAPI_URL.rstrip('/')}/extraction/{rid}", timeout=120)
            r.raise_for_status()
            return r.json().get("candidates", [])
        except:
            return []

    candidates = fetch_candidates(run_id)

    if not candidates:
        st.info("No viable extraction candidates identified for this run.")
        st.markdown("""
        **Why am I seeing this?**
        The extraction engine evaluates components based on **Modular Cohesion** and **Coupling Pressure**. 
        If a component is too deeply entangled with the rest of the monolith (High Blast Radius), 
        it is marked as a 'Critical Hotspot' but not a 'Viable Extraction Candidate'.
        
        **Recommendations:**
        1.  Check **Modernization Risk** to identify the most entangled hotspots.
        2.  Review **Layered Architecture** to see if the directory structure prevents logical grouping.
        3.  Consider manual decoupling of 'God Objects' identified in the **Monolith Navigator**.
        """)
        return

    # --- Core Metrics ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Identified Candidates", len(candidates))
    m2.metric("Optimal Strategy", candidates[0]["unit"])
    m3.metric("Peak Quality Score", f"{max(c['score'] for c in candidates):.2f}")

    st.markdown("---")
    
    selected_idx = st.selectbox(
        "Target Extraction Strategy",
        options=range(len(candidates)),
        format_func=lambda i: f"{candidates[i]['unit']} (Feasibility: {candidates[i]['recommendation']})"
    )

    if selected_idx is not None:
        strategy = candidates[selected_idx]
        impact = strategy.get("impact", {})
        
        # --- ROI Brief ---
        st.markdown("#### Strategic Impact Analysis")
        col_roi, col_risk, col_feas = st.columns(3)
        
        before_risk = impact.get("before_risk", 0.0)
        after_risk = impact.get("after_risk", 0.0)
        roi = ((before_risk - after_risk) / before_risk * 100) if before_risk > 0 else 0
        
        col_roi.metric("Complexity Reduction (ROI)", f"{roi:.1f}%")
        col_risk.metric("Risk Shift", f"{impact.get('risk_change', 0.0):.3f}")
        col_feas.metric("Feasibility Class", strategy.get("recommendation").replace("_", " "))

        st.markdown("---")

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### Selection Rationale")
            for reason in strategy.get("reasoning", []):
                st.markdown(f"- {reason}")

        with c_right:
            st.markdown("#### Proposed Service Topology")
            proxy_name = f"{strategy.get('unit').replace(' ', '')}_Service"
            dot = f"digraph {{ rankdir=LR; bgcolor='transparent'; node [shape=box, style=filled, fontname='Monospace']; "
            dot += f"'{proxy_name}' [fillcolor='#1e293b', fontcolor='white']; "
            dot += f"'Legacy_Monolith' -> '{proxy_name}' [label='API']; }}"
            st.graphviz_chart(dot)

        st.markdown("---")
        st.markdown("#### Implementation Protocol")
        for node in strategy.get("node_details", []):
            with st.expander(f"Entity Isolation: {node['name']}"):
                st.markdown(f"**Source FQN**: `{node['fqn']}`")
                st.markdown(f"**Source Path**: `{node['file_path']}`")
                st.code(f"// Step: Encapsulate and migrate {node['name']}\n// Target: \\Strata\\Services\\{strategy['unit']}\\{node['name']}", language="php")

if __name__ == "__main__":
    show_extraction_simulator()
