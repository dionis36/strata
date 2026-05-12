import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Strata - Topological Manifest", layout="wide")

# Minimal, High-Contrast Dark Mode Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1a1c24; border-radius: 5px; padding: 15px; border: 1px solid #333; }
    .stAlert { background-color: #1a1c24; border: 1px solid #444; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)


st.title("📂 Topological Manifest: Structural Diagnostics")

# --- 💡 Architect's Guidance: Page Purpose ---
with st.sidebar:
    st.markdown("### 💡 Page Purpose")
    st.info("""
    **The Manifest** is your formal technical record. It provides the 'Structural Signature' 
    of the system, identifying cycles and coupling pressures that must be addressed 
    to achieve a clean modernization.
    """)
    st.markdown("### 🔍 Technical Metrics")
    st.write("**Efferent Pressure**: The 'Weight' of a node's outgoing dependencies.")
    st.write("**Topology Integrity**: A score representing how 'Acyclic' and clean the graph is.")
    st.write("**Cyclic Nodes**: Components stuck in a dependency loop (The 'Ball of Mud').")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
RUNS_URL = FASTAPI_URL + "/runs"

# 1. Fetch available runs
try:
    runs_res = requests.get(RUNS_URL, timeout=5)
    if runs_res.status_code == 200:
        available_runs = runs_res.json()
        run_options = {f"Run {r['id']} - {r['started_at'][:10]}": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
    else:
        run_options = {}
except Exception:
    run_options = {}

if not run_options:
    st.warning("⚠️ No completed runs found. Please run an analysis from the Home page first.")
    st.stop()

with st.sidebar:
    st.header("Manifest Controls")
    selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
    RUN_ID = run_options[selected_run_label]
    st.markdown("---")
    st.caption("Strata Topological Engine v0.1")

def fetch_intel(run_id):
    try:
        risk_res = requests.get(f"{FASTAPI_URL}/risk/{run_id}")
        metrics_res = requests.get(f"{FASTAPI_URL}/metrics/{run_id}")
        if risk_res.status_code == 200:
            return risk_res.json(), metrics_res.json()
        return None, None
    except:
        return None, None

risk_data, metrics_data = fetch_intel(RUN_ID)

if not risk_data:
    st.info("Awaiting System Synchronization. Select a Run ID to generate the Topological Manifest.")
else:
    # 1. TOPOLOGICAL SIGNATURE
    st.header("🔬 Topological Signature")
    st.markdown("Quantitative structural profile derived from the Centralized Source of Truth (CSOT).")
    
    components = risk_data["components"]
    df = pd.DataFrame(components)
    
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = df["final_risk"].mean()
    total_cycles = len(df[df["cycle_flag"] == 1])
    
    col1.metric("Topology Integrity", f"{100 - (avg_risk * 100):.1f}%", delta_color="normal")
    col2.metric("Cyclic Nodes", f"{total_cycles}", delta="Critical" if total_cycles > 0 else "Optimal")
    col3.metric("Efferent Pressure", f"{df['coupling_pressure'].mean():.3f}")
    col4.metric("Analyzed Nodes", f"{len(df)}")

    # Fingerprint Visualization: Risk vs Instability
    fig = px.scatter(
        df, x="instability", y="final_risk", 
        size="criticality_index", color="type",
        hover_name="name",
        title="Structural Distribution: Risk vs Instability (Size = Node Criticality)",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        labels={"instability": "Efferent Instability (Ce / (Ca+Ce))", "final_risk": "Aggregated Risk Coefficient"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. BOTTLENECK DIAGNOSTICS
    st.header("⚡ Structural Diagnostics")
    st.markdown("High-priority architectural bottlenecks and cross-component pressures.")
    
    hotspots = df.sort_values("final_risk", ascending=False).head(10)
    
    # Narrative Table
    st.dataframe(
        hotspots[["name", "type", "final_risk", "criticality_index", "coupling_pressure", "risk_level"]],
        hide_index=True,
        use_container_width=True
    )
    
    # 3. TECHNICAL INSIGHTS
    st.header("📋 Technical Rationale")
    
    with st.expander("Topology Insight Engine", expanded=True):
        if total_cycles > 0:
            st.error(f"🚨 **Cyclic Dependency Fault**: {total_cycles} nodes detected in a strongly connected component. This creates a monolithic 'Ball of Mud' that resists granular extraction.")
        
        top_node = hotspots.iloc[0]
        st.warning(f"⚠️ **High-Criticality Chokepoint**: `{top_node['name']}` maintains a risk coefficient of {top_node['final_risk']:.2f}. Its topological position makes it a high-risk candidate for direct mutation.")
        
        high_coupling = len(df[df["coupling_pressure"] > 0.7])
        if high_coupling > 0:
            st.info(f"ℹ️ **Coupling Pressure Threshold**: {high_coupling} nodes exceeded the 0.7 pressure threshold, indicating significant integration debt.")

st.sidebar.markdown("---")
st.sidebar.caption("Strata Topological Engine v0.1")
