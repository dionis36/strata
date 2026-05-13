import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Layered Architecture", page_icon="🧬", layout="wide")

st.title("🧬 Layered Architecture Analysis")
st.markdown("Multi-dimensional analysis combining File System, Abstract Syntax Tree, and Semantic Domain grouping.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# --- Run Selector ---
try:
    runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=5)
    if runs_res.status_code == 200:
        available_runs = runs_res.json()
        run_options = {f"Run {r['id']} - {r['started_at'][:10]} ({r['total_files']} Files)": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
    else:
        run_options = {}
except Exception:
    run_options = {}

if not run_options:
    st.warning("⚠️ No completed runs found. Please run an Intelligence Scan from the Home page.")
    st.stop()

selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
run_id = run_options[selected_run_label]

@st.cache_data(ttl=60)
def fetch_layered_data(rid):
    res = requests.get(f"{FASTAPI_URL}/layer-analysis/{rid}")
    if res.status_code == 200:
        return res.json()
    return None

with st.spinner("Extracting layered intelligence..."):
    data = fetch_layered_data(run_id)

if not data:
    st.error("Failed to fetch layer analysis data. Ensure the backend is running.")
    st.stop()

# --- Display Logic ---
tab1, tab2, tab3 = st.tabs([
    "🗂️ Layer 1: File System", 
    "🧬 Layer 2: AST OOP Manifest", 
    "🧠 Layer 3: Semantic Domains"
])

with tab1:
    st.markdown("### Layer 1: File System Classification")
    l1 = data.get("layer_1", {})
    
    colA, colB = st.columns([2, 1])
    with colA:
        st.markdown("#### Folder Taxonomy (Tree View)")
        dirs = l1.get("directories", {})
        
        # Build nested tree
        tree = {}
        for path, info in sorted(dirs.items()):
            parts = [p for p in path.split('/') if p]
            if not parts:
                parts = ["/ (Root)"]
                
            current = tree
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_info": None, "_children": {}}
                if i == len(parts) - 1:
                    current[part]["_info"] = info
                current = current[part]["_children"]
                
        def generate_html_tree(node, depth=0):
            html = ""
            for name, data in sorted(node.items(), key=lambda x: x[0]):
                info = data["_info"]
                
                children_html = ""
                if data["_children"]:
                    children_html = generate_html_tree(data["_children"], depth + 1)
                
                open_attr = "open" if depth < 2 else ""
                
                if info:
                    icon = "📁"
                    if info["type"] == "vendor": icon = "📦"
                    elif info["type"] == "entry_point": icon = "🚪"
                    elif info["type"] == "asset": icon = "🎨"
                    elif info["type"] == "upload": icon = "⚠️"
                    
                    summary = f"{icon} <b>{name}/</b> <span style='color:#888; font-size:0.8em;'>[{info['type']} - {info['count']} files]</span>"
                    files_html = "".join([f"<div style='color:#aaa; padding-left: 20px;'>📄 {f}</div>" for f in info["files"][:10]])
                    if len(info["files"]) > 10:
                        files_html += f"<div style='color:#777; font-size: 0.8em; padding-left: 20px;'>...and {len(info['files']) - 10} more files</div>"
                        
                    html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 4px;'><summary style='cursor: pointer; padding: 2px;'>{summary}</summary><div style='margin-top: 4px; margin-bottom: 8px; border-left: 1px dashed #444; margin-left: 7px;'>{files_html}{children_html}</div></details>"
                else:
                    summary = f"📁 <b>{name}/</b>"
                    html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 4px;'><summary style='cursor: pointer; padding: 2px;'>{summary}</summary><div style='margin-top: 4px; margin-bottom: 8px; border-left: 1px dashed #444; margin-left: 7px;'>{children_html}</div></details>"
            return html

        # Render inside a card with monospace font
        st.markdown("<div style='font-family: monospace; background: #111; padding: 15px; border-radius: 5px; max-height: 600px; overflow-y: auto;'>", unsafe_allow_html=True)
        tree_html = generate_html_tree(tree)
        st.markdown(tree_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with colB:
        st.markdown("#### Physical Distribution")
        ftypes = l1.get("file_types", {})
        df_types = pd.DataFrame(list(ftypes.items()), columns=["Extension", "Count"])
        st.dataframe(df_types, hide_index=True, use_container_width=True)
                    
    st.markdown("#### Detected Entry Points")
    for ep in l1.get("entry_points", []):
        st.code(ep, language="text")

with tab2:
    st.markdown("### Layer 2: PHP AST OOP Manifest")
    st.write("Deterministic extractions generated strictly via PHP-Parser (no regex).")
    
    l2 = data.get("layer_2", {})
    entities = l2.get("oop_entities", [])
    if entities:
        df_oop = pd.DataFrame(entities)
        
        # Clean up side effects for display
        def format_effects(effects):
            if not isinstance(effects, list): return ""
            clean = [e.replace("sink::", "").replace("global::", "🌍 ") for e in effects]
            return ", ".join(clean)
            
        df_oop['side_effects'] = df_oop['side_effects'].apply(format_effects)
        
        st.dataframe(
            df_oop, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "name": "Entity Name",
                "namespace": "Namespace",
                "methods_count": st.column_config.NumberColumn("Methods", format="%d"),
                "is_interface": "Interface?",
                "is_trait": "Trait?",
                "parent_class": "Extends",
                "side_effects": "AST Side-Effects (Globals, DB, Auth)"
            }
        )
    else:
        st.info("No OOP entities found. This codebase might be 100% procedural.")

with tab3:
    st.markdown("### Layer 3: Semantic Architecture & Bounded Contexts")
    st.write("Inferred logical modules based on directory clustering and internal vs external dependency ratios.")
    
    l3 = data.get("layer_3", {})
    contexts = l3.get("bounded_contexts", [])
    
    if contexts:
        for ctx in sorted(contexts, key=lambda x: x["coupling_ratio"]):
            with st.container():
                st.markdown(f"<div style='border: 1px solid #444; border-radius: 5px; padding: 15px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                with c1:
                    st.markdown(f"#### 🧩 Context: `{ctx['name']}`")
                    st.caption(f"{ctx['file_count']} logic files mapped.")
                with c2:
                    st.metric("Internal Cohesion", ctx["internal_edges"])
                with c3:
                    st.metric("External Coupling", ctx["external_edges"])
                with c4:
                    if ctx["coupling_ratio"] > 1.5:
                        st.metric("Coupling Ratio", f"{ctx['coupling_ratio']} 🔴", help="High external coupling. Hard to extract.")
                    else:
                        st.metric("Coupling Ratio", f"{ctx['coupling_ratio']} 🟢", help="High cohesion. Prime candidate for extraction.")
                
                flags = []
                if ctx["is_transactional"]: flags.append("💾 Contains DB Writes")
                if ctx["handles_auth"]: flags.append("🔐 Interacts with Auth/Session")
                
                if flags:
                    st.markdown("**Semantic Capabilities:** " + " | ".join(flags))
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Could not automatically infer bounded contexts. Codebase may be a completely flat structure.")
