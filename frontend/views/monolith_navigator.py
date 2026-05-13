import streamlit as st
import streamlit.components.v1 as components
import requests
import os
import json
from pyvis.network import Network

def show_monolith_navigator():
    st.title("Monolith Navigator")
    st.markdown("### Topological Dependency Visualization")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    
    # 1. Context Resolution
    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    st.markdown(f"**Analysis Context**: Run `{run_id}`")
    
    with st.expander("Topology Legend & Intelligence", expanded=False):
        st.markdown("""
        The **Monolith Navigator** visualizes the physical and semantic connections between objects.
        *   **Nodes**: Represent classes, methods, or files.
        *   **Edges**: Represent calls, inclusions, or inheritance.
        *   **Heatmap**: Node color indicates the **Risk Magnitude** calculated in the Intelligence phase.
        *   **Clusters**: High-density zones usually represent tightly-coupled 'God Objects' or foundational services.
        """)

    def get_graph_data(run_id):
        try:
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

    graph_data = get_graph_data(run_id)
    risk_map = get_risk_data(run_id)

    if not graph_data:
        st.error("Topological data not found for the selected run.")
        return

    # --- View Configuration ---
    col_ctrl, col_graph = st.columns([1, 4])
    
    with col_ctrl:
        st.markdown("#### View Controls")
        node_limit = st.slider("Visibility Limit", 10, 500, 200)
        st.markdown("---")
        st.markdown("**Node Legend**")
        st.markdown("- <span style='color: #ff4b4b'>High Risk</span>", unsafe_allow_html=True)
        st.markdown("- <span style='color: #f9a825'>Moderate Risk</span>", unsafe_allow_html=True)
        st.markdown("- <span style='color: #00cc96'>Low Risk</span>", unsafe_allow_html=True)

    with col_graph:
        net = Network(height="700px", width="100%", bgcolor="#0b0e14", font_color="#e0e0e0", directed=True)
        net.set_options("""
        var options = {
          "nodes": { "font": { "face": "Inter, sans-serif" } },
          "edges": { "smooth": { "type": "continuous" }, "width": 1.5 },
          "physics": {
            "forceAtlas2Based": { "gravitationalConstant": -60, "springLength": 120 },
            "solver": "forceAtlas2Based",
            "stabilization": { "iterations": 100 }
          }
        }
        """)

        def get_color(risk_val):
            if risk_val > 0.6: return "#ff4b4b"
            if risk_val > 0.25: return "#f9a825"
            return "#00cc96"

        nodes = graph_data.get("nodes", [])[:node_limit]
        node_ids = {n["id"] for n in nodes}
        
        for n in nodes:
            fqn = n.get("fqn", "Unknown")
            risk_info = next((v for k, v in risk_map.items() if k.lower() == fqn.lower()), {})
            risk_val = risk_info.get("final_risk", 0.0)
            color = get_color(risk_val)
            label = n.get("name", "Unknown")
            title = f"FQN: {fqn}\nRisk: {risk_val:.2f}\nType: {n.get('type')}"
            net.add_node(n["id"], label=label, title=title, color=color, border_width=2, size=25 if risk_val > 0.4 else 15)

        for link in graph_data.get("links", []):
            source, target = link.get("source"), link.get("target")
            if source in node_ids and target in node_ids:
                net.add_edge(source, target, color="rgba(100, 100, 100, 0.3)")

        net.save_graph("/tmp/navigator_graph.html")
        with open("/tmp/navigator_graph.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=710)

if __name__ == "__main__":
    show_monolith_navigator()
