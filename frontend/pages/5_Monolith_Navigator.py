import streamlit as st
import streamlit.components.v1 as components
import requests
import os
import json
import pandas as pd
from pyvis.network import Network

st.set_page_config(page_title="Strata - Monolith Navigator", layout="wide")

# Minimal, High-Contrast Dark Mode Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)


st.title("🕸️ Monolith Navigator: Topological Explorer")

# --- 💡 Architect's Guidance: Page Purpose ---
with st.sidebar:
    st.markdown("### 💡 Page Purpose")
    st.info("""
    **The Navigator** is your immersive lens into the monolith. It visualizes the 
    'Physical Gravity' of your code—showing which components are the center of 
    your universe and which are safely isolated.
    """)
    st.markdown("### 🎨 Visual Key")
    st.write("🔴 **Crimson**: High Risk / Central Anchor")
    st.write("🟠 **Amber**: Moderate Coupling")
    st.write("🟢 **Emerald**: Low Risk / Extraction Candidate")

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
    st.header("Navigator Controls")
    selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
    RUN_ID = run_options[selected_run_label]
    st.markdown("---")
    st.caption("Strata Visualization Engine v0.1")

def get_graph_data(run_id):
    try:
        # We fetch the raw graph JSON from the data directory
        graph_path = f"/data/graph_{run_id}.json"
        if os.path.exists(graph_path):
            with open(graph_path, "r") as f:
                return json.load(f)
        return None
    except:
        return None

def get_risk_data(run_id):
    try:
        res = requests.get(f"{FASTAPI_URL}/risk/{run_id}")
        if res.status_code == 200:
            return {c["name"]: c for c in res.json()["components"]}
        return {}
    except:
        return {}

graph_data = get_graph_data(RUN_ID)
risk_map = get_risk_data(RUN_ID)

# --- 🛰️ Mission Control Explorer ---
if not graph_data:
    st.info("Awaiting Topological Data. Ensure a project analysis has been completed for this Run ID.")
else:
    st.sidebar.header("Filter & View")
    node_limit = st.sidebar.slider("Node Visibility Limit", 10, 500, 200)
    
    # Initialize Pyvis Network with professional dark styling
    net = Network(height="700px", width="100%", bgcolor="#0b0e14", font_color="#e0e0e0", directed=True)
    
    net.set_options("""
    var options = {
      "nodes": {
        "shadow": { "enabled": true, "color": "rgba(0,0,0,0.5)" },
        "font": { "face": "Inter, sans-serif" }
      },
      "edges": {
        "smooth": { "type": "continuous", "forceDirection": "none" },
        "color": { "inherit": "both" },
        "width": 1.5
      },
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -60, "springLength": 120, "springConstant": 0.08 },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 100 }
      }
    }
    """)

    def get_color(risk_val):
        if risk_val > 0.6: return "#ff4b4b" # Crimson (High)
        if risk_val > 0.25: return "#f9a825" # Amber (Moderate)
        return "#00cc96" # Emerald (Low)

    nodes = graph_data.get("nodes", [])[:node_limit]
    node_ids = {n["id"] for n in nodes}
    
    for n in nodes:
        fqn = n.get("fqn", "Unknown")
        # --- 🔗 SYNCHRONIZED FQN LOOKUP ---
        risk_info = next((v for k, v in risk_map.items() if k.lower() == fqn.lower()), {})
        
        risk_val = risk_info.get("final_risk", 0.0)
        role = n.get("type", "class")
        
        color = get_color(risk_val)
        
        label = n.get("name", "Unknown")
        title = f"<b>{fqn}</b><br>Risk: {risk_val:.2f}<br>Role: {role}"
        
        net.add_node(n["id"], label=label, title=title, color=color, border_width=2, size=25 if risk_val > 0.4 else 15)

    for link in graph_data.get("links", []):
        source, target = link.get("source"), link.get("target")
        if source in node_ids and target in node_ids:
            net.add_edge(source, target, color="rgba(100, 100, 100, 0.3)", arrowsize=0.4)

    # --- 🏗️ THE BOUNDED UI ---
    st.markdown("""
        <div style="border: 2px solid #1f2937; border-radius: 12px; padding: 10px; background: #0b0e14; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #1f2937; padding-bottom: 5px;">
                <span style="color: #6b7280; font-size: 0.8rem; font-family: monospace;">STRATA_VIS_ENGINE_V1.0</span>
                <span style="color: #6b7280; font-size: 0.8rem; font-family: monospace;">REAL_TIME_TOPOLOGY</span>
            </div>
    """, unsafe_allow_html=True)
    
    path = "/tmp/nx_graph.html"
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    components.html(html_content, height=710)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("🔍 **Interactive Tips**: Nodes are sized by Risk Magnitude. Red/Amber nodes represent structural anchors or high-pressure components.")

st.sidebar.markdown("---")
st.sidebar.caption("Strata Visualization Engine v0.1")
