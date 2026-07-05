import streamlit as st
import requests
import pandas as pd
import os
import json
import streamlit.components.v1 as components
from pyvis.network import Network
from views import page_registry

def show_layered_architecture():
    st.title("Layered Structure")
    st.markdown("##### Physical Layout & Architectural Classification")
    
    with st.expander("Layered Structure Blueprint Key", expanded=True):
        colA, colB = st.columns(2)
        with colA:
            st.markdown("""
            **Directories**
            - <span style='color:#f9a825;'>▼</span> **Standard Directory**: Normal application folders.
            - <span style='color:#757575;'>■</span> **Vendor**: External third-party dependencies.
            - <span style='color:#ff4b4b;'>◆</span> **Entry Point**: Web-accessible script directories.
            - <span style='color:#00cc96;'>●</span> **Assets**: Public web files (CSS/JS).
            """, unsafe_allow_html=True)
        with colB:
            st.markdown("""
            **Files & Roles**
            - <span style='color:#ff4b4b;'>◆</span> **Entry Point**: Direct access scripts.
            - <span style='color:#00d4ff;'>◆</span> **Controller**: Request handlers.
            - <span style='color:#00cc96;'>●</span> **View / Asset**: HTML output or UI files.
            - <span style='color:#ab47bc;'>■</span> **Bootstrap**: Framework initialization.
            - <span style='color:#ffb300;'>★</span> **Job / God Class**: Heavy logic processing.
            """, unsafe_allow_html=True)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
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
    st.info("Expand directories below to see classified files. Look for Controllers, Views, and Entry Points.")
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
            
        search_term = st.text_input("🔍 Search files or directories...", "").lower()
        
        def generate_html_tree(node, depth=0):
            html = ""
            # Role Icon Mapping
            role_icons = {
                "entry_point": "<span style='color:#ff4b4b;'>◆</span>", 
                "bootstrap": "<span style='color:#ab47bc;'>■</span>", 
                "controller": "<span style='color:#00d4ff;'>◆</span>", 
                "view": "<span style='color:#00cc96;'>●</span>", 
                "config": "<span style='color:#f9a825;'>■</span>", 
                "asset": "<span style='color:#00cc96;'>●</span>", 
                "job": "⚙️", 
                "vendor": "<span style='color:#757575;'>■</span>", 
                "model": "📦",
                "schema": "💾",
                "file": "<span style='color:#90a4ae;'>●</span>"
            }

            for name, data in sorted(node.items(), key=lambda x: x[0]):
                info = data["_info"]
                children_html = generate_html_tree(data["_children"], depth + 1)
                open_attr = "open" if depth < 1 else ""
                
                if info:
                    icon = "<span style='color:#f9a825;'>▼</span>"
                    if info["type"] == "vendor": icon = "<span style='color:#757575;'>■</span>"
                    elif info["type"] == "entry_point": icon = "<span style='color:#ff4b4b;'>◆</span>"
                    elif info["type"] == "asset": icon = "<span style='color:#00cc96;'>●</span>"
                    
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
                        
                        if search_term and search_term not in fname.lower() and search_term not in name.lower():
                            continue
                        
                        ficon = role_icons.get(frole, "")
                        files_html += f"<div style='color:#aaa; padding-left: 20px; font-size: 0.85rem;'>{ficon} {fname} <span style='color:#555; font-size:0.75em;'>({frole})</span></div>"

                    if search_term and not files_html and not children_html and search_term not in name.lower():
                        continue

                    html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 5px;'><summary style='cursor: pointer;'>{summary}</summary><div style='border-left: 1px dashed #444; margin-left: 7px; padding-top: 4px;'>{files_html}{children_html}</div></details>"
                else:
                    if search_term and not children_html and search_term not in name.lower():
                        continue
                    html += f"<details {open_attr} style='margin-left: 10px;'><summary style='cursor: pointer;'><b>{name}/</b></summary><div style='border-left: 1px dashed #444; margin-left: 7px;'>{children_html}</div></details>"
            return html

        st.markdown("<div style='font-family: monospace; background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; max-height: 800px; overflow-y: auto;'>", unsafe_allow_html=True)
        st.markdown(generate_html_tree(tree), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
                    
    with c2:
        st.markdown("##### Ext. Distribution")
        ftypes = l1.get("file_types", {})
        st.dataframe(pd.DataFrame(list(ftypes.items()), columns=["Ext", "Count"]), hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("### Architectural Layer Insight")
        
        # Calculate layer distribution dynamically
        role_counts = {}
        total_files = 0
        for info in dirs.values():
            for f in info.get("files", []):
                total_files += 1
                role = f.get("role", "file") if isinstance(f, dict) else "file"
                role_counts[role] = role_counts.get(role, 0) + 1
        
        presentation_roles = ["view", "controller", "asset"]
        presentation_count = sum(role_counts.get(r, 0) for r in presentation_roles)
        presentation_ratio = (presentation_count / total_files * 100) if total_files > 0 else 0
        top_layer = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[0] if role_counts else ("none", 0)

        st.info("#### Presentation vs. Logic")
        st.markdown("**METRIC**: MVC / Role Distribution Ratio")
        st.markdown("**INTERPRETATION**: This metric assesses whether the codebase maintains a healthy separation of concerns. A high presentation ratio indicates a UI-heavy monolith, whereas a high 'file' ratio indicates unstructured procedural logic.")
        
        ev1 = f"{presentation_ratio:.1f}% of classified files handle Presentation/Routing."
        ev2 = f"The most populated architectural layer is `{top_layer[0]}` with {top_layer[1]} files."
        st.markdown(f"**EVIDENCE**: \n1. {ev1}\n2. {ev2}")
        
        if top_layer[0] == "file":
            st.markdown("**RECOMMENDATION**: The majority of your codebase consists of unstructured `file` components. Focus on extracting business logic from these generic files into dedicated service classes.")
        elif presentation_ratio > 60:
            st.markdown("**RECOMMENDATION**: The system is highly UI-coupled. Extracting microservices will be difficult until the presentation layer (Views/Templates) is completely decoupled from the backend routing logic.")
        else:
            st.markdown("**RECOMMENDATION**: The application demonstrates a structured layer distribution. Proceed to the System Topology view to analyze the depth of entanglement between these physical layers.")

def show_system_topology():
    st.title("System Topology")
    st.markdown("##### Relational Graph & Connectivity Analysis")
    
    with st.expander("Architectural Blueprint Key", expanded=True):
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown("""
            **Node Archetypes (Shapes)**
            - <span style="color:#ff1744; font-size:1.2em;">★</span> **God Class**: Monolithic bottlenecks with high coupling.
            - <span style="color:#00d4ff; font-size:1.2em;">◆</span> **Controller**: Routing / Presentation boundaries.
            - <span style="color:#90a4ae; font-size:1.2em;">■</span> **Utility**: Stateless infrastructure helpers.
            - <span style="color:#5c6bc0; font-size:1.2em;">●</span> **Entity / Standard**: Standard domain structures.
            """, unsafe_allow_html=True)
        with colB:
            st.markdown("""
            **Edge Intelligence (Coupling)**
            - <hr style="border: 2px solid #ff4b4b; width: 20px; display: inline-block; margin: 0; vertical-align: middle;"> Static Call: Toxic tight coupling. Hard to mock.
            - <hr style="border: 2px solid #f9a825; width: 20px; display: inline-block; margin: 0; vertical-align: middle;"> Instantiates: Direct `new` usage. Violates DI.
            - <hr style="border: 2px dashed #00cc96; width: 20px; display: inline-block; margin: 0; vertical-align: middle;"> Injects: Clean Dependency Injection.
            - <hr style="border: 1px solid rgba(150,150,150,0.5); width: 20px; display: inline-block; margin: 0; vertical-align: middle;"> Calls: Standard procedural linkage.
            """, unsafe_allow_html=True)
        with colC:
            st.markdown("""
            **Hover Metrics Explained**
            - **WMC (Weighted Method Count)**: Total structural complexity. Higher = Harder to maintain.
            - **LCOM (Lack of Cohesion)**: `> 0.8` means the class has unrelated responsibilities.
            - **Coverage**: Risk baseline. `< 20%` means unsafe to extract.
            """, unsafe_allow_html=True)
    st.markdown("---")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
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
        data_dir = os.getenv("DATA_DIR", "/data")
        graph_path = os.path.join(data_dir, f"graph_{run_id}.json")
        if os.path.exists(graph_path):
            with st.spinner("Re-calculating Force-Directed Physics & Semantic Edges..."):
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
            net = Network(height="750px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
            
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
                "stabilization": false
              },
              "edges": { "smooth": { "type": "continuous" } }
            }
            """)
            
            # 3. Enhanced Color Mapping & Shape Mapping
            role_colors = {
                "entry_point": "#ff4b4b", "controller": "#00d4ff", "view": "#00cc96",
                "config": "#f9a825", "bootstrap": "#ab47bc", "vendor": "#757575",
                "file": "#90a4ae", "class": "#5c6bc0", 
                "method": "#7e57c2", "function": "#ffa726",
                "global_var": "#ec407a", "namespace": "#26a69a"
            }
            
            archetype_shapes = {
                "ENTITY": "dot",
                "CONTROLLER": "diamond",
                "UTILITY": "square",
                "GOD_CLASS": "star",
                "UNKNOWN": "dot"
            }

            for n in top_nodes:
                ntype = n.get("type", "file")
                color = role_colors.get(ntype, "#90a4ae")
                degree = node_degree.get(n["id"], 1)
                size = 15 + (degree * 2) if degree > 5 else 15
                
                archetype = n.get("domain_archetype", "UNKNOWN")
                shape = archetype_shapes.get(archetype, "dot")
                if archetype == "GOD_CLASS":
                    color = "#ff1744" # Pulsing Red Equivalent
                    size += 10
                
                label = n.get("name")
                cov_str = f"{(n.get('test_coverage') * 100):.1f}%" if n.get("test_coverage") is not None else "N/A"
                title = (
                    f"FQN: {n.get('fqn')}\nType: {ntype}\n"
                    f"Archetype: {archetype}\nConnections: {degree}\n"
                    f"WMC: {n.get('wmc', 0)}\nLCOM: {n.get('lcom', 0):.2f}\n"
                    f"Coverage: {cov_str}"
                )
                net.add_node(n["id"], label=label, title=title, color=color, shape=shape, size=min(size, 50))
            
            # Map edge types
            for link in links:
                if link["source"] in top_node_ids and link["target"] in top_node_ids:
                    edge_type = link.get("type", "calls")
                    e_color = "rgba(150, 150, 150, 0.3)"
                    e_width = 1.5
                    e_dashes = False
                    
                    if edge_type == "injects":
                        e_color = "rgba(0, 204, 150, 0.7)" # Green
                        e_dashes = True
                    elif edge_type == "static_call":
                        e_color = "rgba(255, 75, 75, 0.8)" # Solid Red
                        e_width = 2.5
                    elif edge_type == "instantiates":
                        e_color = "rgba(249, 168, 37, 0.8)" # Solid Orange
                        e_width = 2.0
                        
                    net.add_edge(link["source"], link["target"], color=e_color, width=e_width, dashes=e_dashes)
            
            net.save_graph(f"/tmp/topology_graph_{run_id}.html")
            with open(f"/tmp/topology_graph_{run_id}.html", "r", encoding="utf-8") as f:
                html = f.read()
                
            # Inject custom CSS to remove PyVis default white borders and margins
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
            
            components.html(html, height=770)
            
            st.markdown("---")
            st.markdown("### System Topology Intelligence")
            
            # Find the most connected node
            max_degree_node = None
            max_degree = 0
            for n in top_nodes:
                d = node_degree.get(n["id"], 0)
                if d > max_degree:
                    max_degree = d
                    max_degree_node = n
                    
            # Calculate density
            total_edges = len(links)
            total_visible = len(top_nodes)
            density = total_edges / (total_visible * max(1, total_visible - 1)) if total_visible > 1 else 0
            
            # Fast Circular Dependency Detection (Mutual Edges)
            edge_set = set()
            mutual_edges = set()
            for l in links:
                if l["source"] in top_node_ids and l["target"] in top_node_ids:
                    edge = (l["source"], l["target"])
                    reverse_edge = (l["target"], l["source"])
                    if reverse_edge in edge_set:
                        mutual_edges.add(edge)
                        mutual_edges.add(reverse_edge)
                    edge_set.add(edge)
            
            circular_count = len(mutual_edges) // 2
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("#### Network Density & Coupling")
                st.markdown("**METRIC**: Graph Edge Density")
                st.markdown("**INTERPRETATION**: Density indicates how intertwined the components are. A 'Spaghetti Code' monolith will have an extremely dense, highly connected graph, whereas a modular system will appear as distinct, lightly-connected clusters.")
                
                ev1 = f"Total rendered connections: {total_edges}."
                ev2 = "The graph visually forms distinct clusters." if density < 0.05 else "The graph forms a dense, highly entangled web."
                st.markdown(f"**EVIDENCE**: \n1. {ev1}\n2. {ev2}")
                st.markdown("**RECOMMENDATION**: If the graph is a dense web, do not attempt to split it immediately. Look for natural fault lines between the colored clusters to identify potential service boundaries.")

            with col2:
                st.success("#### Structural Bottlenecks")
                st.markdown("**METRIC**: Component Centrality & Degree")
                st.markdown("**INTERPRETATION**: The node with the highest number of connections acts as a primary structural bottleneck. These are often core utilities, base controllers, or global configuration files that every other file depends on.")
                
                if max_degree_node:
                    ev1_bn = f"The most central node is `{max_degree_node.get('name')}` (Type: {max_degree_node.get('type')})."
                    ev2_bn = f"It single-handedly manages {max_degree} direct connections."
                else:
                    ev1_bn = "No central bottleneck identified."
                    ev2_bn = "Connections are distributed."
                    
                st.markdown(f"**EVIDENCE**: \n1. {ev1_bn}\n2. {ev2_bn}")
                st.markdown(
                    "**RECOMMENDATION**: The most central node in a legacy system is almost never a coincidence — it accumulated connections because it was the most convenient place to put shared logic. "
                    "Consider what *role* this node was originally intended to play. Is it a technical utility (a logger, a config loader) that crept into business logic? "
                    "Or is it a core business object that became a catch-all? That distinction determines whether it belongs in a shared library, a dedicated service, or needs to be decomposed entirely."
                )

            with col3:
                st.warning("#### Circular Dependencies")
                st.markdown("**METRIC**: Mutual Back-Edges")
                st.markdown("**INTERPRETATION**: Circular dependencies (A calls B, and B calls A) create tightly coupled loops that are impossible to extract independently. They are the most severe blockers for microservice modernization.")
                
                ev1_circ = f"Detected {circular_count} direct circular loop(s) within the visible topology."
                ev2_circ = "The graph contains mutual dependencies." if circular_count > 0 else "No direct mutual loops found in this view."
                st.markdown(f"**EVIDENCE**: \n1. {ev1_circ}\n2. {ev2_circ}")
                
                if circular_count > 0:
                    st.markdown(
                        "**RECOMMENDATION**: Circular dependencies are the architectural equivalent of a structural loop — neither component can be moved without moving the other. "
                        "Before deciding how to break them, understand *why* they formed: did two modules genuinely need to share behaviour, or was one module just reaching across a boundary out of convenience? "
                        "The answer will tell you whether to introduce an interface, extract the shared logic into a third component, or merge the two modules into a single bounded context."
                    )
                else:
                    st.markdown(
                        "**RECOMMENDATION**: The absence of circular dependencies in this slice indicates that the original call flow was directional — logic moved in one consistent direction through these components. "
                        "Note whether this continues to hold as you explore the full topology, or whether circular dependencies appear only in specific subsystems."
                    )
    except Exception as e:
        st.error(f"Could not render topology: {e}")

def show_bounded_contexts():
    st.title("Bounded Contexts")
    st.markdown("##### Semantic Domain Inference")
    
    with st.expander("About Bounded Contexts", expanded=True):
        st.markdown("""
        We group your code into **Logical Domains** based on directory clustering and coupling density. 
        High **Coupling Ratios** indicate modules that are difficult to extract without refactoring.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    res = requests.get(f"{FASTAPI_URL}/layer-analysis/{run_id}")
    if res.status_code == 200:
        l3 = res.json().get("layer_3", {})
        contexts = l3.get("bounded_contexts", [])
        if contexts:
            df_ctx = pd.DataFrame(contexts)
            df_ctx.columns = ["Domain Name", "Files", "Internal Calls", "External Calls", "Coupling Ratio", "DB?", "Auth?"]
            st.dataframe(df_ctx, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### Domain Extractability Intelligence")
            
            # Find insights
            high_coupling = sorted(contexts, key=lambda x: x["coupling_ratio"], reverse=True)
            most_coupled = high_coupling[0] if high_coupling else None
            
            isolated_domains = [c for c in contexts if c["coupling_ratio"] <= 0.3 and c["file_count"] > 1]
            best_candidate = sorted(isolated_domains, key=lambda x: x["file_count"], reverse=True)[0] if isolated_domains else None

            col1, col2 = st.columns(2)
            with col1:
                st.info("#### Domain Cohesion Insight")
                st.markdown("**METRIC**: Global Coupling Ratios & Outliers")
                st.markdown("**INTERPRETATION**: This metric provides an understanding of how well the legacy system's logic is encapsulated. A system with predominantly high-coupling domains typically represents a 'Big Ball of Mud' architecture, whereas lower coupling ratios suggest that the original developers successfully implemented separation of concerns.")
                
                highly_coupled = [f"`{c['name']}` ({c['coupling_ratio']})" for c in high_coupling[:3] if c["coupling_ratio"] >= 1.0]
                ev1 = f"Domains with high inter-dependencies: {', '.join(highly_coupled)}." if highly_coupled else "No domains exceed a 1.0 coupling ratio."
                ev2 = f"There are {len([c for c in contexts if c['coupling_ratio'] < 0.5])} domains with strong internal cohesion (< 0.5 ratio)."
                st.markdown(f"**EVIDENCE**: \n1. {ev1}\n2. {ev2}")
                st.markdown("**RECOMMENDATION**: Use these cohesion insights to map out which areas of the codebase share state. High-coupling areas indicate cross-cutting concerns that should be mapped carefully during the architectural discovery phase.")

            with col2:
                st.success("#### State & Boundary Distribution")
                st.markdown("**METRIC**: Transactional (DB) and Authentication (Auth) Sinks")
                st.markdown("**INTERPRETATION**: Identifying which domains independently touch database layers or session management reveals the functional layout of the system. Domains that manage their own state are naturally closer to operating as independent bounded contexts, whereas centralized state points to a highly monolithic data tier.")
                
                db_domains = [f"`{c['name']}`" for c in contexts if c.get("db_access")]
                auth_domains = [f"`{c['name']}`" for c in contexts if c.get("auth_access")]
                ev1_db = ", ".join(db_domains[:4]) + ("..." if len(db_domains) > 4 else "") if db_domains else "No direct DB access sinks detected."
                ev2_auth = ", ".join(auth_domains[:4]) + ("..." if len(auth_domains) > 4 else "") if auth_domains else "No isolated Auth sinks detected."
                
                st.markdown(f"**EVIDENCE**: \n1. Domains bypassing abstractions to hit DB sinks: {ev1_db}\n2. Domains interacting directly with auth/session state: {ev2_auth}")
                st.markdown("**RECOMMENDATION**: Observe whether data persistence is heavily centralized in a single 'Core' domain or distributed across multiple feature domains. This insight will guide your future data-tier modernization strategies.")
                    
        else:
            st.info("Insufficient signals to infer contexts.")

if __name__ == "__main__":
    show_layered_architecture()
