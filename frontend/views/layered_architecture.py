import streamlit as st
import requests
import pandas as pd
import os
import json
import streamlit.components.v1 as components
from pyvis.network import Network

def show_layered_architecture():
    st.title("Layered Structure")
    st.markdown("##### Physical Layout & Architectural Classification")
    
    with st.expander("💡 About the Layered Structure", expanded=True):
        st.markdown("""
        This view shows your codebase's **physical organization**. Each file is tagged with its 
        **Architectural Role** based on naming patterns, location, and structural signatures.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=60)
    def fetch_layered_data(rid):
        res = requests.get(f"{FASTAPI_URL}/layer-analysis/{rid}")
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_layered_data(run_id)
    if not data:
        st.error("Technical error retrieving layered intelligence data.")
        return

    st.markdown("#### Directory Hierarchy & Classified Files")
    st.info("Expand directories below to see classified files. Look for 🎮 Controllers, 🖼️ Views, and 🚪 Entry Points.")
    l1 = data.get("layer_1", {})
    
    c1, c2 = st.columns([2, 1])
    with c1:
        dirs = l1.get("directories", {})
        tree = {}
        for path, info in sorted(dirs.items()):
            parts = [p for p in path.split('/') if p]
            if not parts: parts = ["root"]
            current = tree
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_info": None, "_children": {}}
                if i == len(parts) - 1:
                    current[part]["_info"] = info
                current = current[part]["_children"]
            
        def generate_html_tree(node, depth=0):
            html = ""
            # Role Icon Mapping
            role_icons = {
                "entry_point": "🚪", "bootstrap": "⚡", "controller": "🎮", 
                "view": "🖼️", "config": "⚙️", "asset": "🎨", "job": "⏰", 
                "vendor": "📦", "file": "📄"
            }

            for name, data in sorted(node.items(), key=lambda x: x[0]):
                info = data["_info"]
                children_html = generate_html_tree(data["_children"], depth + 1)
                open_attr = "open" if depth < 1 else ""
                
                if info:
                    icon = "📁"
                    if info["type"] == "vendor": icon = "📦"
                    elif info["type"] == "entry_point": icon = "🚪"
                    elif info["type"] == "asset": icon = "🎨"
                    
                    summary = f"{icon} <b>{name}/</b> <span style='color:#888; font-size:0.8em;'>[{info['type']}]</span>"
                    
                    # File Classification Display
                    files_html = ""
                    for f_obj in info.get("files", []):
                        if isinstance(f_obj, dict):
                            fname = f_obj["name"]
                            frole = f_obj["role"]
                        else:
                            fname = f_obj
                            frole = "file"
                        
                        ficon = role_icons.get(frole, "📄")
                        files_html += f"<div style='color:#aaa; padding-left: 20px; font-size: 0.85rem;'>{ficon} {fname} <span style='color:#555; font-size:0.75em;'>({frole})</span></div>"

                    html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 5px;'><summary style='cursor: pointer;'>{summary}</summary><div style='border-left: 1px dashed #444; margin-left: 7px; padding-top: 4px;'>{files_html}{children_html}</div></details>"
                else:
                    html += f"<details {open_attr} style='margin-left: 10px;'><summary style='cursor: pointer;'>📁 <b>{name}/</b></summary><div style='border-left: 1px dashed #444; margin-left: 7px;'>{children_html}</div></details>"
            return html

        st.markdown("<div style='font-family: monospace; background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; max-height: 800px; overflow-y: auto;'>", unsafe_allow_html=True)
        st.markdown(generate_html_tree(tree), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
                    
    with c2:
        st.markdown("##### Ext. Distribution")
        ftypes = l1.get("file_types", {})
        st.dataframe(pd.DataFrame(list(ftypes.items()), columns=["Ext", "Count"]), hide_index=True, use_container_width=True)

def show_system_topology():
    st.title("System Topology")
    st.markdown("##### Relational Graph & Connectivity Analysis")
    
    with st.expander("💡 Reading the Topology", expanded=True):
        st.markdown("""
        This graph shows the **Functional Gravity** of your system. 
        - **Red (🚪)**: Entry / **Cyan (🎮)**: Controllers
        - **Green (🖼️)**: Views / **Yellow (⚙️)**: Configs
        - **Purple (⚡)**: Methods / **Orange (📦)**: Functions
        - **Blue (🧩)**: Classes / **Pink (🌎)**: Globals
        """)
    st.markdown("---")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("No active analysis run detected.")
        return

    # --- Filtering Logic ---
    st.markdown("#### Topology Filters")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_types = st.multiselect(
            "Visible Layers",
            options=["class", "method", "function", "global_var", "namespace", "file", "entry_point", "controller", "view", "config"],
            default=["class", "function", "global_var", "entry_point", "controller"]
        )
    
    with col2:
        max_nodes = st.slider("Node Limit", 50, 500, 250)

    try:
        graph_path = f"/data/graph_{run_id}.json"
        if os.path.exists(graph_path):
            with open(graph_path, "r") as f:
                graph_data = json.load(f)
            
            # 1. Build a lookup for node importance (degree)
            links = graph_data.get("links", [])
            node_degree = {}
            for l in links:
                node_degree[l["source"]] = node_degree.get(l["source"], 0) + 1
                node_degree[l["target"]] = node_degree.get(l["target"], 0) + 1
            
            # 2. Filter nodes by type AND degree
            all_nodes = graph_data.get("nodes", [])
            filtered_nodes = [n for n in all_nodes if n.get("type") in selected_types]
            
            sorted_nodes = sorted(filtered_nodes, key=lambda n: node_degree.get(n["id"], 0), reverse=True)
            top_nodes = sorted_nodes[:max_nodes]
            top_node_ids = {n["id"] for n in top_nodes}
            
            net = Network(height="750px", width="100%", bgcolor="#0b0e14", font_color="#e0e0e0", directed=True)
            
            # Use a robust configuration
            net.toggle_physics(True)
            net.set_options("""
            {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "springLength": 100,
                  "avoidOverlap": 0.5
                },
                "solver": "forceAtlas2Based",
                "stabilization": { "iterations": 100 }
              },
              "edges": { "smooth": { "type": "continuous" } }
            }
            """)
            
            # 3. Enhanced Color Mapping
            role_colors = {
                "entry_point": "#ff4b4b", "controller": "#00d4ff", "view": "#00cc96",
                "config": "#f9a825", "bootstrap": "#ab47bc", "vendor": "#757575",
                "file": "#90a4ae", "class": "#5c6bc0", 
                "method": "#7e57c2", "function": "#ffa726",
                "global_var": "#ec407a", "namespace": "#26a69a"
            }

            for n in top_nodes:
                ntype = n.get("type", "file")
                color = role_colors.get(ntype, "#90a4ae")
                degree = node_degree.get(n["id"], 1)
                size = 15 + (degree * 2) if degree > 5 else 15
                
                label = n.get("name")
                title = f"FQN: {n.get('fqn')}\nType: {ntype}\nConnections: {degree}"
                net.add_node(n["id"], label=label, title=title, color=color, size=min(size, 50))
            
            for link in links:
                if link["source"] in top_node_ids and link["target"] in top_node_ids:
                    net.add_edge(link["source"], link["target"], color="rgba(150, 150, 150, 0.3)", width=1.5)
            
            net.save_graph("/tmp/topology_graph.html")
            with open("/tmp/topology_graph.html", "r", encoding="utf-8") as f:
                html = f.read()
            components.html(html, height=760)
    except Exception as e:
        st.error(f"Could not render topology: {e}")

def show_bounded_contexts():
    st.title("Bounded Contexts")
    st.markdown("##### Semantic Domain Inference")
    
    with st.expander("💡 About Bounded Contexts", expanded=True):
        st.markdown("""
        We group your code into **Logical Domains** based on directory clustering and coupling density. 
        High **Coupling Ratios** indicate modules that are difficult to extract without refactoring.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected.")
        return

    res = requests.get(f"{FASTAPI_URL}/layer-analysis/{run_id}")
    if res.status_code == 200:
        l3 = res.json().get("layer_3", {})
        contexts = l3.get("bounded_contexts", [])
        if contexts:
            df_ctx = pd.DataFrame(contexts)
            df_ctx.columns = ["Domain Name", "Files", "Internal Calls", "External Calls", "Coupling Ratio", "DB?", "Auth?"]
            st.dataframe(df_ctx, use_container_width=True, hide_index=True)
        else:
            st.info("Insufficient signals to infer contexts.")

if __name__ == "__main__":
    show_layered_architecture()
