import streamlit as st
import requests
import pandas as pd
import os
import json
import streamlit.components.v1 as components
from pyvis.network import Network
from views import page_registry



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

    # --- Step 1: Fetch Bounded Context data for Domain Focus filter ---
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    fqn_to_domain = {}
    _bounded_contexts = []
    try:
        _layer_res = requests.get(f"{FASTAPI_URL}/layer-analysis/{run_id}", timeout=15)
        if _layer_res.status_code == 200:
            _l3 = _layer_res.json().get("layer_3", {})
            _bounded_contexts = _l3.get("bounded_contexts", [])
            for _ctx in _bounded_contexts:
                _dname = _ctx.get("name", "")
                for _fqn in _ctx.get("files", []):
                    fqn_to_domain[str(_fqn)] = _dname
    except Exception:
        pass  # Domain Focus unavailable selectbox falls back to "All Domains" only

    # --- Step 2: Render Topology Filters ---
    st.markdown("#### Topology Filters")
    col1, col2, col3 = st.columns([3, 1, 2])

    # Render type filter first domain node counts depend on this selection
    with col1:
        selected_types = st.multiselect(
            "Visible Layers",
            options=["class", "method", "function", "global_var", "namespace", "file", "entry_point", "controller", "view", "config"],
            default=["class", "function", "global_var", "entry_point", "controller"]
        )

    # --- Step 3: Count nodes per domain matching the current type filter ---
    _domain_node_counts = {}
    try:
        _data_dir = os.getenv("DATA_DIR", "/data")
        _graph_path_scan = os.path.join(_data_dir, f"graph_{run_id}.json")
        if os.path.exists(_graph_path_scan):
            with open(_graph_path_scan, "r") as _gsf:
                _gsdata = json.load(_gsf)
            for _n in _gsdata.get("nodes", []):
                if _n.get("type") in selected_types:
                    _nd = fqn_to_domain.get(str(_n.get("fqn", "")))
                    if _nd:
                        _domain_node_counts[_nd] = _domain_node_counts.get(_nd, 0) + 1
    except Exception:
        # Fallback: use file_count from API as proxy
        for _ctx in _bounded_contexts:
            _nm = _ctx.get("name", "")
            if _nm:
                _domain_node_counts[_nm] = _ctx.get("file_count", 0)

    # Build enriched options only domains with at least 1 matching node
    domain_label_to_name = {"All Domains": "All Domains"}
    enriched_domain_options = ["All Domains"]
    for _ctx in sorted(_bounded_contexts, key=lambda x: -_domain_node_counts.get(x.get("name", ""), 0)):
        _nm  = _ctx.get("name", "")
        _cnt = _domain_node_counts.get(_nm, 0)
        if _nm and _cnt > 0:
            _label = f"{_nm}  ({_cnt} nodes)"
            enriched_domain_options.append(_label)
            domain_label_to_name[_label] = _nm

    # --- Step 4: Render remaining controls ---
    with col2:
        max_nodes = st.slider("Node Limit", 50, 500, 250)

    with col3:
        selected_domain_label = st.selectbox(
            "Domain Focus",
            options=enriched_domain_options,
            help="Only domains with nodes matching the current Visible Layers filter are shown. Sorted by node count."
        )
        selected_domain = domain_label_to_name.get(selected_domain_label, "All Domains")

    try:
        data_dir = os.getenv("DATA_DIR", "/data")
        graph_path = os.path.join(data_dir, f"graph_{run_id}.json")
        if os.path.exists(graph_path):
            with st.spinner("Re-calculating Force-Directed Physics & Semantic Edges..."):
                with open(graph_path, "r") as f:
                    graph_data = json.load(f)
                
                # 1. Build degree lookup (total connections per node)
                links = graph_data.get("links", [])
                node_degree = {}
            for l in links:
                node_degree[l["source"]] = node_degree.get(l["source"], 0) + 1
                node_degree[l["target"]] = node_degree.get(l["target"], 0) + 1

            # 2. Filter nodes by selected types
            all_nodes = graph_data.get("nodes", [])
            filtered_nodes = [n for n in all_nodes if n.get("type") in selected_types]

            # 3. Apply Domain Focus filter (if a specific domain is selected)
            if selected_domain != "All Domains":
                filtered_nodes = [
                    n for n in filtered_nodes
                    if fqn_to_domain.get(str(n.get("fqn", ""))) == selected_domain
                ]
            total_after_filter = len(filtered_nodes)

            # 4. Role-weighted ranking: architectural importance first, degree within tier
            #    Tier 0 (GOD_CLASS) → Tier 1 (CONTROLLER / entry_point) → Tier 2 (ENTITY / class)
            #    → Tier 3 (function / global_var) → Tier 4 (everything else)
            def _node_sort_key(n):
                archetype = n.get("domain_archetype", "UNKNOWN")
                ntype = n.get("type", "")
                if archetype == "GOD_CLASS":
                    tier = 0
                elif archetype == "CONTROLLER" or ntype in ("entry_point", "controller"):
                    tier = 1
                elif archetype == "ENTITY" or ntype == "class":
                    tier = 2
                elif ntype in ("function", "global_var"):
                    tier = 3
                else:
                    tier = 4
                return (tier, -node_degree.get(n["id"], 0))

            sorted_nodes = sorted(filtered_nodes, key=_node_sort_key)
            top_nodes    = sorted_nodes[:max_nodes]
            top_node_ids = {n["id"] for n in top_nodes}

            # 5. Transparency notice always tell the user what's hidden
            hidden_count = total_after_filter - len(top_nodes)
            if hidden_count > 0:
                st.warning(
                    f"Displaying **{len(top_nodes)} of {total_after_filter}** nodes "
                    f" **{hidden_count} hidden** by the node limit. "
                    f"Increase the slider or narrow the Domain Focus / Layer filter to see more.",
                    icon=":material/visibility_off:"
                )
            else:
                st.success(
                    f"Displaying all **{len(top_nodes)}** nodes matching the current filters.",
                    icon=":material/check_circle:"
                )
            HEIGHT_PX = 750
            net = Network(height=f"{HEIGHT_PX}px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
            
            # Physics: stabilize fully then fit all nodes within the canvas bounds
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
                "stabilization": {
                  "enabled": true,
                  "iterations": 200,
                  "fit": true
                }
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
                
            # Inject CSS: zero out body/html margins, border lives on #mynetwork inside the iframe
            # Inject CSS: zero out body margins, let PyVis manage the explicit pixel height
            custom_css = """
            <style>
                html, body {
                    margin: 0 !important;
                    padding: 0 !important;
                    background-color: #0e1117 !important;
                    overflow: hidden !important;
                }
                center, h1 {
                    display: none !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .card {
                    border: none !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    background-color: transparent !important;
                }
                .card-body {
                    padding: 0 !important;
                }
                #mynetwork {
                    background-color: #0e1117 !important;
                    border: 1px solid #2d3748 !important;
                    border-radius: 8px !important;
                    box-sizing: border-box !important;
                }
                #loadingBar { display: none !important; }
            </style>
            """
            # Inject Material Icons & custom CSS
            icon_css = '<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">'
            html = html.replace("</head>", icon_css + custom_css + "</head>")
            html = html.replace('border: 1px solid lightgray;', 'border: none;')

            # Inject floating controls (Theme + Fullscreen) and their Javascript logic
            ui_controls = """
            <div style="position: absolute; top: 15px; right: 15px; z-index: 9999; display: flex; gap: 8px;">
                <button id="theme-btn" style="background: rgba(30, 36, 48, 0.8); border: 1px solid #4a5568; color: #e2e8f0; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: 500; transition: all 0.2s; display: flex; align-items: center; gap: 6px;">
                    <span class="material-icons" style="font-size: 16px;">light_mode</span> Light Mode
                </button>
                <button id="fs-btn" style="background: rgba(30, 36, 48, 0.8); border: 1px solid #4a5568; color: #e2e8f0; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: 500; transition: all 0.2s; display: flex; align-items: center; gap: 6px;">
                    <span class="material-icons" style="font-size: 16px;">fullscreen</span> Fullscreen
                </button>
            </div>
            <script>
                // Theme toggle logic
                let isDark = true;
                const themeBtn = document.getElementById('theme-btn');
                const fsBtn = document.getElementById('fs-btn');
                const networkDiv = document.getElementById('mynetwork');
                
                const updateNodeFonts = (colorHex) => {
                    if (typeof nodes !== 'undefined') {
                        const updates = nodes.get().map(n => ({id: n.id, font: {color: colorHex}}));
                        nodes.update(updates);
                    } else if (typeof network !== 'undefined') {
                        network.setOptions({ nodes: { font: { color: colorHex } } });
                    }
                };
                
                themeBtn.onclick = () => {
                    isDark = !isDark;
                    if (isDark) {
                        document.documentElement.style.setProperty('background-color', '#0e1117', 'important');
                        document.body.style.setProperty('background-color', '#0e1117', 'important');
                        networkDiv.style.setProperty('background-color', '#0e1117', 'important');
                        networkDiv.style.setProperty('border-color', '#2d3748', 'important');
                        
                        themeBtn.innerHTML = '<span class="material-icons" style="font-size: 16px;">light_mode</span> Light Mode';
                        themeBtn.style.background = 'rgba(30, 36, 48, 0.8)';
                        themeBtn.style.color = '#e2e8f0';
                        themeBtn.style.borderColor = '#4a5568';
                        
                        fsBtn.style.background = 'rgba(30, 36, 48, 0.8)';
                        fsBtn.style.color = '#e2e8f0';
                        fsBtn.style.borderColor = '#4a5568';
                        
                        updateNodeFonts('#e0e0e0');
                    } else {
                        document.documentElement.style.setProperty('background-color', '#ffffff', 'important');
                        document.body.style.setProperty('background-color', '#ffffff', 'important');
                        networkDiv.style.setProperty('background-color', '#ffffff', 'important');
                        networkDiv.style.setProperty('border-color', '#cbd5e1', 'important');
                        
                        themeBtn.innerHTML = '<span class="material-icons" style="font-size: 16px;">dark_mode</span> Dark Mode';
                        themeBtn.style.background = 'rgba(255, 255, 255, 0.9)';
                        themeBtn.style.color = '#1e293b';
                        themeBtn.style.borderColor = '#cbd5e1';
                        
                        fsBtn.style.background = 'rgba(255, 255, 255, 0.9)';
                        fsBtn.style.color = '#1e293b';
                        fsBtn.style.borderColor = '#cbd5e1';
                        
                        updateNodeFonts('#1e293b');
                    }
                };

                // Fullscreen logic
                fsBtn.onclick = () => {
                    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                        const root = document.documentElement;
                        if (root.requestFullscreen) {
                            root.requestFullscreen().catch(err => console.warn(err));
                        } else if (root.webkitRequestFullscreen) {
                            root.webkitRequestFullscreen();
                        }
                        fsBtn.innerHTML = '<span class="material-icons" style="font-size: 16px;">fullscreen_exit</span> Exit Fullscreen';
                    } else {
                        if (document.exitFullscreen) {
                            document.exitFullscreen();
                        } else if (document.webkitExitFullscreen) {
                            document.webkitExitFullscreen();
                        }
                        fsBtn.innerHTML = '<span class="material-icons" style="font-size: 16px;">fullscreen</span> Fullscreen';
                    }
                };
                
                const handleFsChange = () => {
                    if (document.fullscreenElement || document.webkitFullscreenElement) {
                        networkDiv.style.setProperty('height', '100vh', 'important');
                    } else {
                        networkDiv.style.setProperty('height', '750px', 'important');
                        fsBtn.innerHTML = '<span class="material-icons" style="font-size: 16px;">fullscreen</span> Fullscreen';
                    }
                };
                document.addEventListener('fullscreenchange', handleFsChange);
                document.addEventListener('webkitfullscreenchange', handleFsChange);
            </script>
            """
            html = html.replace("</body>", ui_controls + "</body>")

            components.html(html, height=HEIGHT_PX)
            
            st.markdown("---")
            st.markdown("### System Topology Assessment")
            
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
                st.markdown("""
                <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Network Density & Coupling</h4>
                    <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Graph Edge Density measures how interconnected the components are. A density near 0 = modular clusters. A density near 1 = 'Spaghetti Code' every file talks to every other file, making safe extraction mathematically improbable.</span></div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**METRIC**: Graph Edge Density")
                st.markdown("**INTERPRETATION**: Density indicates how intertwined the components are. A 'Spaghetti Code' monolith will have an extremely dense, highly connected graph, whereas a modular system will appear as distinct, lightly-connected clusters.")
                
                ev1 = f"Total rendered connections: {total_edges}."
                ev2 = "The graph visually forms distinct clusters." if density < 0.05 else "The graph forms a dense, highly entangled web."
                st.markdown(f"**EVIDENCE**: \n1. {ev1}\n2. {ev2}")
                st.markdown("**RECOMMENDATION**: If the graph is a dense web, do not attempt to split it immediately. Look for natural fault lines between the colored clusters to identify potential service boundaries.")

            with col2:
                st.markdown("""
                <div style="background-color: rgba(33,195,84,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Structural Bottlenecks</h4>
                    <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Component Centrality & Degree the node with the highest connection count is the structural center of gravity. In legacy systems this is usually a shared utility, base controller, or God Class that every other file depends on. It cannot be safely moved until its dependents are decoupled.</span></div>
                </div>
                """, unsafe_allow_html=True)
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
                    "**RECOMMENDATION**: The most central node in a legacy system is almost never a coincidence - it accumulated connections because it was the most convenient place to put shared logic. "
                    "Consider what *role* this node was originally intended to play. Is it a technical utility (a logger, a config loader) that crept into business logic? "
                    "Or is it a core business object that became a catch-all? That distinction determines whether it belongs in a shared library, a dedicated service, or needs to be decomposed entirely."
                )

            with col3:
                st.markdown("""
                <div style="background-color: rgba(255,193,7,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Circular Dependencies</h4>
                    <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Mutual Back-Edges A depends on B, and B depends on A. These loops are the most severe extraction blockers: neither component can be independently deployed without the other. Breaking them requires introducing an interface, a shared library, or merging both modules into one bounded context.</span></div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**METRIC**: Mutual Back-Edges")
                st.markdown("**INTERPRETATION**: Circular dependencies (A calls B, and B calls A) create tightly coupled loops that are impossible to extract independently. They are the most severe blockers for microservice modernization.")
                
                ev1_circ = f"Detected {circular_count} direct circular loop(s) within the visible topology."
                ev2_circ = "The graph contains mutual dependencies." if circular_count > 0 else "No direct mutual loops found in this view."
                st.markdown(f"**EVIDENCE**: \n1. {ev1_circ}\n2. {ev2_circ}")
                
                if circular_count > 0:
                    st.markdown(
                        "**RECOMMENDATION**: Circular dependencies are the architectural equivalent of a structural loop - neither component can be moved without moving the other. "
                        "Before deciding how to break them, understand *why* they formed: did two modules genuinely need to share behaviour, or was one module just reaching across a boundary out of convenience? "
                        "The answer will tell you whether to introduce an interface, extract the shared logic into a third component, or merge the two modules into a single bounded context."
                    )
                else:
                    st.markdown(
                        "**RECOMMENDATION**: The absence of circular dependencies in this slice indicates that the original call flow was directional - logic moved in one consistent direction through these components. "
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
            # Build display table (exclude raw files list kept in contexts for drill-down)
            display_rows = []
            for c in contexts:
                display_rows.append({
                    "Domain Name":   c.get("name", ""),
                    "Files":         c.get("file_count", 0),
                    "Internal Calls": c.get("internal_edges", 0),
                    "External Calls": c.get("external_edges", 0),
                    "Coupling Ratio": c.get("coupling_ratio", 0.0),
                    "DB?":           c.get("is_transactional", False),
                    "Auth?":         c.get("handles_auth", False),
                })
            df_ctx = pd.DataFrame(display_rows)

            st.caption("Click any row to drill into its file inventory.")
            selection = st.dataframe(
                df_ctx,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Coupling Ratio": st.column_config.NumberColumn(format="%.2f"),
                    "DB?":   st.column_config.CheckboxColumn("DB?"),
                    "Auth?": st.column_config.CheckboxColumn("Auth?"),
                }
            )

            # ── File Drill-Down Panel ─────────────────────────────────────────
            selected_rows = selection.selection.get("rows", [])
            if selected_rows:
                idx = selected_rows[0]
                domain = contexts[idx]
                domain_name  = domain.get("name", "")
                domain_files = domain.get("files", [])

                st.markdown("---")
                st.markdown(f"### `{domain_name}` File Inventory")

                col_meta1, col_meta2, col_meta3 = st.columns(3)
                col_meta1.metric("Files in Domain",   domain.get("file_count", 0))
                col_meta2.metric("Coupling Ratio",    domain.get("coupling_ratio", 0.0))
                col_meta3.metric("DB Sink",           "Yes" if domain.get("is_transactional") else "No")

                if domain_files:
                    # Search filter
                    search = st.text_input(
                        "Filter files",
                        placeholder="Type to search by filename or path...",
                        key=f"file_search_{domain_name}",
                        label_visibility="collapsed"
                    )
                    filtered = [f for f in domain_files if search.lower() in f.lower()] if search else domain_files

                    st.markdown(
                        f"**{len(filtered)}** file(s) shown"
                        + (f" · *filtered from {len(domain_files)}*" if search and len(filtered) != len(domain_files) else "")
                    )

                    # Render as scrollable code block for easy copy
                    file_list_text = "\n".join(filtered)
                    st.code(file_list_text, language=None)
                else:
                    st.info("No file paths recorded for this domain in the current scan.", icon=":material/info:")
            
            st.markdown("---")
            st.markdown("### Domain Extractability Assessment")
            
            # Find insights
            high_coupling = sorted(contexts, key=lambda x: x["coupling_ratio"], reverse=True)
            most_coupled = high_coupling[0] if high_coupling else None
            
            isolated_domains = [c for c in contexts if c["coupling_ratio"] <= 0.3 and c["file_count"] > 1]
            best_candidate = sorted(isolated_domains, key=lambda x: x["file_count"], reverse=True)[0] if isolated_domains else None

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Domain Cohesion Insight</h4>
                    <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Coupling Ratio = External Calls ÷ Internal Calls. A ratio > 1.0 means a domain makes more calls outside itself than within it is not a true bounded context and cannot be extracted as-is without breaking cross-domain dependencies.</span></div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**METRIC**: Global Coupling Ratios & Outliers")
                st.markdown("**INTERPRETATION**: This metric provides an understanding of how well the legacy system's logic is encapsulated. A system with predominantly high-coupling domains typically represents a 'Big Ball of Mud' architecture, whereas lower coupling ratios suggest that the original developers successfully implemented separation of concerns.")
                
                highly_coupled = [f"`{c['name']}` ({c['coupling_ratio']})" for c in high_coupling[:3] if c["coupling_ratio"] >= 1.0]
                ev1 = f"Domains with high inter-dependencies: {', '.join(highly_coupled)}." if highly_coupled else "No domains exceed a 1.0 coupling ratio."
                ev2 = f"There are {len([c for c in contexts if c['coupling_ratio'] < 0.5])} domains with strong internal cohesion (< 0.5 ratio)."
                st.markdown(f"**EVIDENCE**: \n1. {ev1}\n2. {ev2}")
                st.markdown("**RECOMMENDATION**: Use these cohesion insights to map out which areas of the codebase share state. High-coupling areas indicate cross-cutting concerns that should be mapped carefully during the architectural discovery phase.")

            with col2:
                st.markdown("""
                <div style="background-color: rgba(33,195,84,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">State & Boundary Distribution</h4>
                    <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Transactional (DB) and Authentication (Auth) Sinks domains with direct DB access or auth/session management cannot easily operate as independent microservices without owning their own data tier. These domains require a Database-per-Service migration pattern before extraction.</span></div>
                </div>
                """, unsafe_allow_html=True)
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
