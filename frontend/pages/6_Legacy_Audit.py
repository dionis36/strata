import streamlit as st
import requests
import os
import networkx as nx
import json
from domain.models.edge import EdgeType

st.set_page_config(page_title="Legacy Dependency Audit", layout="wide")

st.title("🕵️ Legacy Dependency Audit")
st.markdown("---")

run_id = st.session_state.get("active_run_id")

if not run_id:
    st.warning("⚠️ No active analysis run found. Please run a scan from the Home page first.")
else:
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    
    # --- Load Graph Data ---
    with st.spinner("Loading Architectural Topology..."):
        # We assume the graph is saved as graph_{run_id}.json in /data
        graph_path = f"/data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            st.error(f"Graph file not found at {graph_path}")
        else:
            with open(graph_path, 'r') as f:
                graph_data = json.load(f)
            
            G = nx.DiGraph()
            for node in graph_data.get("nodes", []):
                G.add_node(node["id"], **node)
            for edge in graph_data.get("edges", []):
                G.add_edge(edge["source_id"], edge["target_id"], type=edge["edge_type"])

            # Filter for Include/Dependency Tree (Requirement 3B)
            # Only include FILE nodes and DEPENDS_ON edges
            include_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == EdgeType.DEPENDS_ON.value]
            include_G = nx.DiGraph(include_edges)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🔄 Circular Include Detection")
                cycles = list(nx.simple_cycles(include_G))
                if not cycles:
                    st.success("✅ No circular dependencies detected in the include tree.")
                else:
                    st.error(f"🚨 Found {len(cycles)} recursive include loops!")
                    for i, cycle in enumerate(cycles[:10]): # Limit display
                        st.markdown(f"**Loop {i+1}**:")
                        # Show path
                        path_names = [G.nodes[n].get('name', n) for n in cycle]
                        st.code(" -> ".join(path_names + [path_names[0]]))

            with col2:
                st.subheader("🔗 Bootstrap Chain Analysis")
                # Identify the "Entry Points" (in-degree 0)
                entry_points = [n for n, d in include_G.in_degree() if d == 0]
                if not entry_points:
                    st.info("No clear entry points found (possible total circularity).")
                else:
                    # Find the longest path in the include graph
                    try:
                        longest_path = nx.dag_longest_path(include_G)
                        st.markdown("**Longest Include Chain (Bootstrap Path):**")
                        path_names = [G.nodes[n].get('name', n) for n in longest_path]
                        st.code(" -> ".join(path_names))
                    except nx.NetworkXUnfeasible:
                        st.warning("⚠️ Cannot calculate longest path due to circular dependencies.")

            st.markdown("---")
            st.subheader("💀 Dead & Dynamic Include Audit")
            
            # Find nodes that are targets of DEPENDS_ON but don't exist as FILE nodes in the scan
            # (Heuristic for missing files or unresolved dynamic includes)
            missing_files = []
            for u, v, d in G.edges(data=True):
                if d['type'] == EdgeType.DEPENDS_ON.value and v not in G.nodes:
                    missing_files.append(v)
            
            if not missing_files:
                st.success("✅ All static includes resolved successfully.")
            else:
                st.warning(f"Found {len(set(missing_files))} unresolved include targets.")
                st.markdown("These targets were detected in `include/require` statements but the files were not found during the scan. These often represent **dynamic includes** or **dead code**.")
                st.write(list(set(missing_files))[:20])

            # Visualization
            st.markdown("### 🕸️ Include Topology")
            st.info("This graph shows the 'Include Tree' structure. Tight clusters indicate high procedural coupling.")
            # Simple list for now, we have Monolith Navigator for full viz
            st.write(f"Total Include Edges: {len(include_edges)}")
