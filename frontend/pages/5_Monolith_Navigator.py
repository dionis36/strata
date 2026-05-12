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
st.markdown("---")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
RUN_ID = st.sidebar.number_input("Target Run ID:", min_value=1, step=1, value=1)

def get_graph_data(run_id):
    try:
        # We fetch the raw graph JSON from the data directory
        # In a real product, we'd have a dedicated API endpoint for this
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

if not graph_data:
    st.info("Awaiting Topological Data. Ensure a project analysis has been completed for this Run ID.")
else:
    # 1. GRAPH CONSTRUCTION
    st.sidebar.header("Filter & View")
    node_limit = st.sidebar.slider("Node Visibility Limit", 10, 500, 100)
    
    # Initialize Pyvis Network
    net = Network(height="700px", width="100%", bgcolor="#0e1117", font_color="white", directed=True)
    
    # Physics options for a professional feel
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": { "iterations": 150 }
      }
    }
    """)

    # Map Colors based on Risk
    def get_color(risk_val):
        if risk_val > 0.7: return "#ff4b4b" # High Risk
        if risk_val > 0.4: return "#ffa500" # Moderate
        return "#00cc96" # Low Risk

    nodes = graph_data.get("nodes", [])[:node_limit]
    node_ids = {n["id"] for n in nodes}
    
    for n in nodes:
        name = n.get("name", "Unknown")
        risk_info = risk_map.get(name, {})
        risk_val = risk_info.get("final_risk", 0.0)
        role = risk_info.get("type", "Unknown")
        
        color = get_color(risk_val)
        
        label = f"{name}\n({role})"
        title = f"FQN: {n.get('fqn')}\nRisk: {risk_val:.2f}\nRole: {role}"
        
        net.add_node(n["id"], label=label, title=title, color=color, border_width=2)

    for link in graph_data.get("links", []):
        source = link.get("source") or link.get("caller")
        target = link.get("target") or link.get("callee")
        if source in node_ids and target in node_ids:
            net.add_edge(source, target, color="#444", arrowsize=0.5)

    # 2. RENDER
    path = "/tmp/nx_graph.html"
    net.save_graph(path)
    
    with open(path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    components.html(html_content, height=750)

    st.markdown("---")
    st.caption("🔍 **Interactive Tips**: Use your mouse to zoom and drag. Hover over nodes to see FQN and Risk Coefficients.")

st.sidebar.markdown("---")
st.sidebar.caption("Strata Visualization Engine v0.1")
