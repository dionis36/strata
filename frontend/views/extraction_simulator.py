import streamlit as st
import os
import requests
import json
import streamlit.components.v1 as components
from pyvis.network import Network
import pandas as pd

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
from views import page_registry

import urllib.parse

def fetch_simulation(run_id: int, fqn: str):
    try:
        encoded_fqn = urllib.parse.quote(fqn, safe="")
        res = requests.get(f"{FASTAPI_URL}/simulation/impact/{run_id}?fqn={encoded_fqn}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to run simulation: {e}")
    return None

def fetch_ghost_graph(run_id: int, fqn: str):
    try:
        encoded_fqn = urllib.parse.quote(fqn, safe="")
        res = requests.get(f"{FASTAPI_URL}/simulation/ghost-graph/{run_id}?fqn={encoded_fqn}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to run ghost graph simulation: {e}")
    return None

def show_extraction_simulator():
    st.title("Extraction & Impact Simulator")
    st.caption("Perform simulated topological rewiring to preview the 'To-Be' network boundaries and systemic risk shift.")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
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
                "Select Extraction Target", 
                unique_files,
                index=0,
                format_func=lambda x: f"{os.path.basename(x)} ({os.path.dirname(x).replace('/data/', '', 1)})",
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

    sim_key = f"last_sim_{run_id}"
    ghost_key = f"last_ghost_{run_id}"

    if st.button("Run Impact Simulation"):
        with st.spinner(f"Simulating extraction of {os.path.basename(target_fqn)}..."):
            data = fetch_simulation(run_id, target_fqn)
            ghost_data = fetch_ghost_graph(run_id, target_fqn)
            if data:
                st.session_state[sim_key] = data
            if ghost_data:
                st.session_state[ghost_key] = ghost_data

    sim = st.session_state.get(sim_key)
    ghost = st.session_state.get(ghost_key)
    
    if sim and sim.get("target") == target_fqn:
        total_nodes = len(sim["blast_radius"]["files"]) + len(sim["dependency_payload"]["files"])
        tab_as_is, tab_to_be = st.tabs([f"As-Is Blast Radius ({total_nodes} nodes)", "To-Be Ghost Graph"])
        
        with tab_as_is:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### Simulation Metrics")
                
                # Phase 11: Safety Rails Danger Zone Warning
                cov = sim.get("target_coverage")
                if cov is not None and cov < 0.20:
                    st.error(f"**DANGER ZONE**: Target component has {cov*100:.1f}% test coverage. Extracting this module without writing Characterization Tests first poses an extreme regression risk.", icon=":material/error:")
                elif cov is not None:
                    st.success(f"**Safe to Extract**: Target component has {cov*100:.1f}% test coverage.", icon=":material/check_circle:")

                st.metric("Blast Radius (Downstream)", f"{sim['blast_radius']['count']} files")
                st.metric("Dependency Payload (Upstream)", f"{sim['dependency_payload']['count']} files")
                
                st.markdown("#### Isolation Score")
                st.info(sim["isolation_score"])
                st.caption(f"*Ratio of Blast Radius (downstream) to Payload (upstream). Lower ratio = easier to extract safely.*")
                
                st.markdown("#### State Tear")
                if sim["state_tear"]["globals"]:
                    st.warning(f"Shared Globals: {len(sim['state_tear']['globals'])}")
                    st.caption(", ".join(sim["state_tear"]["globals"][:5]) + ("..." if len(sim["state_tear"]["globals"]) > 5 else ""))
                else:
                    st.success("No shared globals detected.")
                
                if sim["state_tear"]["db_dependencies"]:
                    st.warning("Database Operations Detected")
                    st.caption("This module has direct DB calls that will need a Data Access Layer or API Proxy.")

            with col2:
                st.markdown("### Extraction Blast Radius")
                total_nodes = len(sim["blast_radius"]["files"]) + len(sim["dependency_payload"]["files"])
                target_file = sim["target"]
                upstream_full = [f for f in sim["dependency_payload"]["files"] if f != target_file]
                downstream_full = [f for f in sim["blast_radius"]["files"] if f != target_file]
                
                if total_nodes > 500:
                    st.warning(f"Graph too large for full interactive rendering ({total_nodes} nodes). Truncating preview.", icon=":material/warning:")
                    max_nodes = st.slider("Interactive Graph Render Limit", min_value=50, max_value=500, value=250)
                    
                    half_budget = max_nodes // 2
                    upstream_preview = upstream_full[:half_budget]
                    downstream_preview = downstream_full[:(max_nodes - len(upstream_preview))]
                else:
                    upstream_preview = upstream_full
                    downstream_preview = downstream_full
                    
                net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
                net.toggle_physics(True)
                net.set_options("""
                {
                  "physics": {
                    "forceAtlas2Based": { "gravitationalConstant": -50, "springLength": 100, "avoidOverlap": 0.5 },
                    "solver": "forceAtlas2Based",
                    "stabilization": false
                  },
                  "edges": { "smooth": { "type": "continuous" } }
                }
                """)
                net.add_node(target_file, label=os.path.basename(target_file), color="#f85149", size=25, title=f"Target: {target_file}")
                
                for f in downstream_preview:
                    net.add_node(f, label=os.path.basename(f), color="#d29922", size=15, title=f"Downstream: {f}")
                    net.add_edge(f, target_file, title="depends on", color="#d29922")
                
                for f in upstream_preview:
                    try:
                        net.add_node(f, label=os.path.basename(f), color="#58a6ff", size=10, title=f"Upstream: {f}")
                    except: pass
                    net.add_edge(target_file, f, title="calls", color="#58a6ff")

                net.save_graph(f"/tmp/extraction_sim_{run_id}.html")
                with open(f"/tmp/extraction_sim_{run_id}.html", "r", encoding="utf-8") as f:
                    html = f.read()
                    
                custom_css = """
                <style>
                    body { margin: 0 !important; padding: 0 !important; background-color: #0e1117 !important; }
                    #mynetwork { 
                        border: 1px solid #1e2430 !important; 
                        border-radius: 12px !important; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
                        background-color: #0e1117 !important;
                    }
                    #loadingBar { display: none !important; }
                </style>
                """
                html = html.replace("</head>", custom_css + "</head>")
                html = html.replace('border: 1px solid lightgray;', 'border: none;')
                components.html(html, height=520)
                
                with st.expander("View Raw Dependency Tables"):
                    st.markdown("##### 🔌 Upstream Dependencies (What this needs)")
                    if upstream_full:
                        st.dataframe(pd.DataFrame({"File Path": upstream_full}), hide_index=True, use_container_width=True)
                    else:
                        st.info("No upstream dependencies detected.")
                        
                    st.markdown("##### 💥 Blast Radius (What breaks if this is removed)")
                    if downstream_full:
                        st.dataframe(pd.DataFrame({"File Path": downstream_full}), hide_index=True, use_container_width=True)
                    else:
                        st.info("No downstream blast radius detected.")

            st.markdown("---")
            st.markdown("#### Simulation Findings")
            st.markdown(
                f"Extracting **{os.path.basename(target_fqn)}** will require moving or mocking **{sim['dependency_payload']['count']}** files. "
                f"Conversely, **{sim['blast_radius']['count']}** files in the monolith depend on this module and will break unless a backward-compatible proxy is provided."
            )

        with tab_to_be:
            if ghost and not ghost.get("error"):
                col_m, col_g = st.columns([1, 2])
                
                with col_m:
                    st.markdown("### Comparative Metrics")
                    
                    metrics = ghost["metrics"]
                    risk_diff = metrics["risk_change"]
                    
                    # Risk Delta Display
                    if risk_diff > 0:
                        st.metric(
                            label="Systemic Risk Profile", 
                            value=f"{metrics['after_risk']:.3f}", 
                            delta=f"+{risk_diff:.3f} (Penalty)", 
                            delta_color="inverse"
                        )
                    else:
                        st.metric(
                            label="Systemic Risk Profile", 
                            value=f"{metrics['after_risk']:.3f}", 
                            delta=f"{risk_diff:.3f} (Reduced)", 
                            delta_color="normal"
                        )
                        
                    st.metric("Interface Complexity", f"{metrics['interface_complexity']} cross-calls")
                    st.metric("Data Isolation Difficulty", f"{metrics['data_isolation_difficulty']} shared tables")
                    
                    st.markdown("#### Decoupled Architecture")
                    st.info("The selected class and all its declared methods have been removed from the monolith. All incoming and outgoing connections are consolidated into the new green Proxy Service node.")
                    
                with col_g:
                    st.markdown("### Target Architecture Blueprint")
                    
                    # PyVis configuration for Ghost Graph
                    net_g = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
                    net_g.toggle_physics(True)
                    net_g.set_options("""
                    {
                      "physics": {
                        "forceAtlas2Based": { "gravitationalConstant": -50, "springLength": 100, "avoidOverlap": 0.5 },
                        "solver": "forceAtlas2Based",
                        "stabilization": false
                      },
                      "edges": { "smooth": { "type": "continuous" } }
                    }
                    """)
                    
                    # Add nodes
                    for n in ghost["nodes"]:
                        color = "#30363d" # Monolith Node
                        size = 12
                        if n["group"] == "extracted":
                            color = "#2ea44f" # Extracted Service Proxy
                            size = 25
                        elif n["group"] == "database":
                            color = "#f0883e" # Database Table
                            size = 18
                            
                        net_g.add_node(
                            n["id"], 
                            label=n["label"], 
                            color=color, 
                            size=size, 
                            title=f"{n['group'].capitalize()}: {n['label']}"
                        )
                        
                    # Add edges
                    for e in ghost["edges"]:
                        # Style boundary edges nicely
                        net_g.add_edge(e["source"], e["target"], color="#388bfd", width=2, title=e["type"])
                        
                    net_g.save_graph(f"/tmp/ghost_sim_{run_id}.html")
                    with open(f"/tmp/ghost_sim_{run_id}.html", "r", encoding="utf-8") as f:
                        html_g = f.read()
                        
                    custom_css = """
                    <style>
                        body { margin: 0 !important; padding: 0 !important; background-color: #0e1117 !important; }
                        #mynetwork { 
                            border: 1px solid #1e2430 !important; 
                            border-radius: 12px !important; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
                            background-color: #0e1117 !important;
                        }
                        #loadingBar { display: none !important; }
                    </style>
                    """
                    html_g = html_g.replace("</head>", custom_css + "</head>")
                    html_g = html_g.replace('border: 1px solid lightgray;', 'border: none;')
                    components.html(html_g, height=520)
                    
                st.markdown("---")
                st.markdown("#### Extraction Details & Data Contracts")
                
                tab_comp, tab_db, tab_edges = st.tabs(["🧩 Monolith Components", "🗄️ Database Access", "🔀 Network Interfaces"])
                
                with tab_comp:
                    st.caption("These surviving monolith components will communicate with the new Microservice Proxy.")
                    monolith_nodes = [{"ID": n["id"], "Name": n["label"], "Type": n["type"]} for n in ghost["nodes"] if n["group"] == "monolith"]
                    if monolith_nodes:
                        st.dataframe(pd.DataFrame(monolith_nodes), hide_index=True, use_container_width=True)
                    else:
                        st.info("No upstream monolith components detected.")
                        
                with tab_db:
                    st.caption("These database tables will need to be accessible by the extracted microservice.")
                    db_nodes = [{"Table ID": n["id"], "Label": n["label"]} for n in ghost["nodes"] if n["group"] == "database"]
                    if db_nodes:
                        st.dataframe(pd.DataFrame(db_nodes), hide_index=True, use_container_width=True)
                    else:
                        st.success("No direct database dependencies detected for this module.")
                        
                with tab_edges:
                    st.caption("These are the simulated network edges (API calls) that must be preserved over gRPC/REST.")
                    if ghost["edges"]:
                        edge_data = [{"Source": e["source"], "Target": e["target"], "Connection Type": e["type"]} for e in ghost["edges"]]
                        st.dataframe(pd.DataFrame(edge_data), hide_index=True, use_container_width=True)
                    else:
                        st.info("No proxy edges simulated.")
                
                with st.expander("Developer Exports (JSON / Mermaid)"):
                    exp_col1, exp_col2 = st.columns(2)
                    
                    with exp_col1:
                        st.markdown("**1. Raw Topology Schema (JSON)**")
                        st.caption("Download the simulated nodes and edges coordinates for external modeling.")
                        json_str = json.dumps(ghost, indent=2)
                        st.download_button(
                            label="Download JSON Topology",
                            data=json_str,
                            file_name=f"ghost_graph_{os.path.basename(target_fqn).replace('.php', '')}.json",
                            mime="application/json"
                        )
                        
                    with exp_col2:
                        st.markdown("**2. Mermaid Decoupling Diagram**")
                        st.caption("Copy the flowchart definition below to paste into architecture wiki pages.")
                        
                        mermaid_lines = ["flowchart TD"]
                        mermaid_lines.append("    subgraph Monolith [Surviving Monolith Container]")
                        for n in ghost["nodes"]:
                            if n["group"] == "monolith":
                                mermaid_lines.append(f"        {n['id']}[\"{n['label']}\"]")
                        mermaid_lines.append("    end")
                        
                        mermaid_lines.append(f"    subgraph ExtractedService [Remote Microservice Proxy]")
                        mermaid_lines.append(f"        {ghost['proxy_node']}[\"{ghost['proxy_node']}\"]")
                        mermaid_lines.append("    end")
                        
                        for n in ghost["nodes"]:
                            if n["group"] == "database":
                                mermaid_lines.append(f"    {n['id']}[(\"{n['label']}\")]")
                                
                        for e in ghost["edges"]:
                            mermaid_lines.append(f"    {e['source']} -->|{e['type']}| {e['target']}")
                            
                        mermaid_code = "\n".join(mermaid_lines)
                        st.markdown(f"```mermaid\n{mermaid_code}\n```")
            else:
                st.info("Simulating target decoupled architecture... Please run simulation above.")
    else:
        st.info("Select a target file from the dropdown and click **Run Impact Simulation** to preview the architectural boundary and structural impact.")

if __name__ == "__main__":
    show_extraction_simulator()
