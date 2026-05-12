import streamlit as st
import requests
import pandas as pd
import json
import os


st.set_page_config(page_title="Strata - Metrics Inspection", layout="wide")

# --- 💡 Architect's Guidance: Page Purpose ---
with st.sidebar:
    st.markdown("### 💡 Page Purpose")
    st.info("""
    **Metrics Inspection** is the raw structural audit of your monolith. 
    It provides the mathematical data points used to identify 'God Objects' 
    and architectural bottlenecks.
    """)
    st.markdown("### 🔍 Dictionary")
    st.write("**In-Degree**: How many things depend on this? (Popularity)")
    st.write("**Out-Degree**: How many things does this depend on? (Fragility)")
    st.write("**Betweenness**: Is this a central hub? (Criticality)")
    st.write("**Blast Radius**: If this fails, how much of the system is impacted?")

st.title("Structural Database Inspection")
st.markdown("Query the raw structural matrix generated per analysis run for specific bottlenecks.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
RUNS_URL = FASTAPI_URL + "/runs"
METRICS_URL = FASTAPI_URL + "/metrics"

# 1. Fetch available runs
try:
    runs_res = requests.get(RUNS_URL, timeout=5)
    if runs_res.status_code == 200:
        available_runs = runs_res.json()
        run_options = {f"Run {r['id']} - {r['created_at'][:10]} ({r['total_classes']} Classes)": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
    else:
        run_options = {}
except Exception:
    run_options = {}

if not run_options:
    st.warning("⚠️ No completed runs found. Please run an analysis from the Home page first.")
    st.stop()

selected_run_label = st.selectbox("Select Analysis Run to Inspect:", list(run_options.keys()))
run_id = run_options[selected_run_label]

if st.button("Query Structural Matrix"):
    with st.spinner(f"Querying Run {run_id} from SQLite..."):
        try:
            response = requests.get(f"{METRICS_URL}/{run_id}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", [])
                
                if not components:
                    st.warning("No components found for this Run ID. This run may have failed during the parsing phase.")
                else:
                    df = pd.DataFrame(components)
                    cols = ["name", "type", "in_degree", "out_degree", "betweenness", "scc_size", "blast_radius"]
                    for c in cols:
                        if c not in df.columns: df[c] = 0
                    df = df[cols]
                    
                    st.subheader(f"Run {run_id} Results Matrix")
                    st.markdown("💡 *Tip: Sort by **Betweenness** to find components that act as central architectural hubs.*")
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "name": "Component Name",
                            "in_degree": "In-Degree (Popularity)",
                            "out_degree": "Out-Degree (Dependency)",
                            "betweenness": st.column_config.NumberColumn("Betweenness (Hub Rank)", format="%.4f"),
                            "scc_size": "SCC Size (Cyclic Complexity)",
                            "blast_radius": "Blast Radius"
                        }
                    )
                    
                    st.markdown("### Export")
                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="Download Raw JSON",
                        data=json_str,
                        file_name=f"run_{run_id}_metrics.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Failed to fetch metrics: {response.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")
