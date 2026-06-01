import streamlit as st
import os
import requests
import json
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

def fetch_ghost_graph(run_id: int, fqn: str):
    try:
        res = requests.get(f"{FASTAPI_URL}/simulation/ghost-graph/{run_id}?fqn={fqn}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to run ghost graph simulation: {e}")
    return None

def show_extraction_simulator():
    st.markdown("## Extraction & Impact Simulator")
    st.caption("Perform simulated topological rewiring to preview the 'To-Be' network boundaries and systemic risk shift.")

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
                "Select Extraction Target", 
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

    if st.button("Run Impact Simulation"):
        with st.spinner(f"Simulating extraction of {os.path.basename(target_fqn)}..."):
            data = fetch_simulation(run_id, target_fqn)
            ghost_data = fetch_ghost_graph(run_id, target_fqn)
            if data:
                st.session_state["last_sim"] = data
            if ghost_data:
                st.session_state["last_ghost"] = ghost_data

    sim = st.session_state.get("last_sim")
    ghost = st.session_state.get("last_ghost")
    
    if sim and sim.get("target") == target_fqn:
        tab_as_is, tab_to_be = st.tabs(["As-Is Blast Radius", "To-Be Ghost Graph"])
        
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
                if total_nodes > 150:
                    st.warning(f"Graph too large for interactive rendering ({total_nodes} nodes). Please rely on the metrics panel.", icon=":material/warning:")
                else:
                    net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
                    net.add_node(sim["target"], label=os.path.basename(sim["target"]), color="#f85149", size=25, title=f"Target: {sim['target']}")
                    
                    for f in sim["blast_radius"]["files"]:
                        if f != sim["target"]:
                            net.add_node(f, label=os.path.basename(f), color="#d29922", size=15, title=f"Downstream: {f}")
                            net.add_edge(f, sim["target"], title="depends on", color="#d29922")
                    
                    for f in sim["dependency_payload"]["files"]:
                        if f != sim["target"]:
                            try:
                                net.add_node(f, label=os.path.basename(f), color="#58a6ff", size=10, title=f"Upstream: {f}")
                            except: pass
                            net.add_edge(sim["target"], f, title="calls", color="#58a6ff")

                    net.save_graph("/tmp/extraction_sim.html")
                    with open("/tmp/extraction_sim.html", "r", encoding="utf-8") as f:
                        html = f.read()
                    html = html.replace("</head>", "<style>#loadingBar { display: none !important; }</style></head>")
                    components.html(html, height=550)

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
                        
                    net_g.save_graph("/tmp/ghost_sim.html")
                    with open("/tmp/ghost_sim.html", "r", encoding="utf-8") as f:
                        html_g = f.read()
                    components.html(html_g, height=550)
                    
                st.markdown("---")
                st.markdown("#### Architecture Export & Documentation")
                
                exp_col1, exp_col2 = st.columns(2)
                
                with exp_col1:
                    st.markdown("**1. Raw Topology Schema (JSON)**")
                    st.caption("Download the simulated nodes and edges coordinates for modeling inside external toolings.")
                    json_str = json.dumps(ghost, indent=2)
                    st.download_button(
                        label="Download JSON Topology",
                        data=json_str,
                        file_name=f"ghost_graph_{os.path.basename(target_fqn).replace('.php', '')}.json",
                        mime="application/json"
                    )
                    
                with exp_col2:
                    st.markdown("**2. Mermaid Decoupling Diagram**")
                    st.caption("Copy the flowchart definition below to paste into architecture wiki pages or RFC documents.")
                    
                    # Construct Mermaid Flowchart
                    mermaid_lines = ["flowchart TD"]
                    
                    # Subgraph for surviving monolith
                    mermaid_lines.append("    subgraph Monolith [Surviving Monolith Container]")
                    for n in ghost["nodes"]:
                        if n["group"] == "monolith":
                            mermaid_lines.append(f"        {n['id']}[\"{n['label']}\"]")
                    mermaid_lines.append("    end")
                    
                    # Subgraph for extracted service
                    mermaid_lines.append(f"    subgraph ExtractedService [Remote Microservice Proxy]")
                    mermaid_lines.append(f"        {ghost['proxy_node']}[\"{ghost['proxy_node']}\"]")
                    mermaid_lines.append("    end")
                    
                    # Database nodes
                    for n in ghost["nodes"]:
                        if n["group"] == "database":
                            mermaid_lines.append(f"    {n['id']}[(\"{n['label']}\")]")
                            
                    # Edges
                    for e in ghost["edges"]:
                        mermaid_lines.append(f"    {e['source']} -->|{e['type']}| {e['target']}")
                        
                    mermaid_code = "\n".join(mermaid_lines)
                    st.code(mermaid_code, language="mermaid")
            else:
                st.info("Simulating target decoupled architecture... Please run simulation above.")

if __name__ == "__main__":
    show_extraction_simulator()
