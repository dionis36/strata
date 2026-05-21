import streamlit as st
import os
import requests
import pandas as pd
import streamlit.components.v1 as components
from pyvis.network import Network

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def fetch_simulation(run_id: int, fqn: str):
    try:
        res = requests.get(f"{FASTAPI_URL}/simulation/impact/{run_id}?fqn={fqn}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to run simulation: {e}")
    return None

def show_extraction_simulator():
    st.markdown("## 🧪 Extraction & Impact Simulator")
    st.caption("Simulate the 'Blast Radius' of removing or extracting a specific module from the monolith.")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("Please select a valid analysis run in the sidebar.")
        return

    # Let user select a target for simulation
    try:
        res = requests.get(f"{FASTAPI_URL}/boundary-intelligence/{run_id}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            unique_files = data.get("unique_files", [])
            
            if not unique_files:
                st.info("The graph engine is still indexing the system topology. Please check back in a few moments.")
                return

            target_fqn = st.selectbox(
                "🎯 Select Extraction Target", 
                unique_files,
                index=0,
                format_func=lambda x: f"{os.path.basename(x)} ({os.path.dirname(x).replace('/data/OWASPWebGoatPHP-master', '')})",
                help="Search and select any file to calculate its blast radius within the monolith."
            )
        else:
            st.error("Failed to load project topology.")
            return
    except Exception as e:
        st.error(f"Discovery failed: {e}")
        return

    if not target_fqn:
        st.info("Select a file above to begin the impact simulation.")
        return

    if st.button("🚀 Run Impact Simulation"):
        with st.spinner(f"Simulating extraction of {os.path.basename(target_fqn)}..."):
            data = fetch_simulation(run_id, target_fqn)
            if data:
                st.session_state["last_sim"] = data

    sim = st.session_state.get("last_sim")
    if sim and sim.get("target") == target_fqn:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 📊 Simulation Metrics")
            st.metric("Blast Radius (Downstream)", f"{sim['blast_radius']['count']} files")
            st.metric("Dependency Payload (Upstream)", f"{sim['dependency_payload']['count']} files")
            
            st.markdown("#### ⚡ Isolation Score")
            st.info(sim["isolation_score"])
            
            st.markdown("#### 🔓 State Tear")
            if sim["state_tear"]["globals"]:
                st.warning(f"Shared Globals: {len(sim['state_tear']['globals'])}")
                st.caption(", ".join(sim["state_tear"]["globals"][:5]) + ("..." if len(sim["state_tear"]["globals"]) > 5 else ""))
            else:
                st.success("No shared globals detected.")
            
            if sim["state_tear"]["db_dependencies"]:
                st.warning("Database Operations Detected")
                st.caption("This module has direct DB calls that will need a Data Access Layer or API Proxy.")

        with col2:
            st.markdown("### 🕸️ Extraction Blast Radius")
            
            total_nodes = len(sim["blast_radius"]["files"]) + len(sim["dependency_payload"]["files"])
            if total_nodes > 150:
                st.warning(f"⚠️ Graph too large for interactive rendering ({total_nodes} nodes). Please rely on the metrics panel.")
            else:
                # Use PyVis for graph rendering
                net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
                
                # Add target node
                net.add_node(sim["target"], label=os.path.basename(sim["target"]), color="#f85149", size=25, title=f"Target: {sim['target']}")
                
                # Add blast radius nodes (Downstream)
                for f in sim["blast_radius"]["files"]:
                    if f != sim["target"]:
                        net.add_node(f, label=os.path.basename(f), color="#d29922", size=15, title=f"Downstream: {f}")
                        net.add_edge(f, sim["target"], title="depends on", color="#d29922")
                
                # Add dependency payload (Upstream)
                for f in sim["dependency_payload"]["files"]:
                    if f != sim["target"]:
                        # Check if node already added as downstream
                        try:
                            net.add_node(f, label=os.path.basename(f), color="#58a6ff", size=10, title=f"Upstream: {f}")
                        except: pass
                        net.add_edge(sim["target"], f, title="calls", color="#58a6ff")

                net.save_graph("/tmp/extraction_sim.html")
                with open("/tmp/extraction_sim.html", "r", encoding="utf-8") as f:
                    html = f.read()
                
                components.html(html, height=550)

        st.markdown("---")
        st.markdown("#### 📝 Simulation Findings")
        st.markdown(
            f"Extracting **{os.path.basename(target_fqn)}** will require moving or mocking **{sim['dependency_payload']['count']}** files. "
            f"Conversely, **{sim['blast_radius']['count']}** files in the monolith depend on this module and will break unless a backward-compatible proxy is provided."
        )

if __name__ == "__main__":
    show_extraction_simulator()
