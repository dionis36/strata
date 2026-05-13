import streamlit as st
import requests
import pandas as pd
import os

def show_layered_architecture():
    st.title("Layered Architecture Analysis")
    st.markdown("### Structural & Semantic Decomposition")
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

    tabs = st.tabs([
        "File System Inventory", 
        "AST OOP Manifest", 
        "Semantic Domain Models"
    ])

    with tabs[0]:
        st.markdown("#### Physical Layout & Classification")
        l1 = data.get("layer_1", {})
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("##### Directory Hierarchy")
            dirs = l1.get("directories", {})
            
            # Build nested tree structure
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
                for name, data in sorted(node.items(), key=lambda x: x[0]):
                    info = data["_info"]
                    children_html = generate_html_tree(data["_children"], depth + 1)
                    open_attr = "open" if depth < 1 else ""
                    
                    if info:
                        # Icon Mapping
                        icon = "📁"
                        if info["type"] == "vendor": icon = "📦"
                        elif info["type"] == "entry_point": icon = "🚪"
                        elif info["type"] == "asset": icon = "🎨"
                        elif info["type"] == "upload": icon = "⚠️"
                        
                        summary = f"{icon} <b>{name}/</b> <span style='color:#888; font-size:0.8em;'>[{info['type']} - {info['count']} files]</span>"
                        files_html = "".join([f"<div style='color:#aaa; padding-left: 20px; font-size: 0.85rem;'>📄 {f}</div>" for f in info["files"][:10]])
                        if len(info["files"]) > 10:
                            files_html += f"<div style='color:#777; font-size: 0.8em; padding-left: 20px;'>...and {len(info['files']) - 10} more files</div>"
                        
                        html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 4px;'><summary style='cursor: pointer; padding: 2px;'>{summary}</summary><div style='margin-top: 4px; margin-bottom: 8px; border-left: 1px dashed #444; margin-left: 7px;'>{files_html}{children_html}</div></details>"
                    else:
                        summary = f"📁 <b>{name}/</b>"
                        html += f"<details {open_attr} style='margin-left: 10px; margin-bottom: 4px;'><summary style='cursor: pointer; padding: 2px;'>{summary}</summary><div style='margin-top: 4px; margin-bottom: 8px; border-left: 1px dashed #444; margin-left: 7px;'>{children_html}</div></details>"
                return html

            st.markdown("<div style='font-family: monospace; background: #111; padding: 15px; border-radius: 8px; max-height: 600px; overflow-y: auto; border: 1px solid #333;'>", unsafe_allow_html=True)
            st.markdown(generate_html_tree(tree), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
                        
        with c2:
            st.markdown("##### Distribution")
            ftypes = l1.get("file_types", {})
            st.dataframe(pd.DataFrame(list(ftypes.items()), columns=["Ext", "Count"]), hide_index=True, use_container_width=True)

    with tabs[1]:
        st.markdown("#### Deterministic OOP Extraction")
        l2 = data.get("layer_2", {})
        entities = l2.get("oop_entities", [])
        if entities:
            df_oop = pd.DataFrame(entities)
            st.dataframe(df_oop, use_container_width=True, hide_index=True)
        else:
            st.info("No OOP entities identified in the analyzed codebase.")

    with tabs[2]:
        st.markdown("#### Inferred Bounded Contexts")
        l3 = data.get("layer_3", {})
        contexts = l3.get("bounded_contexts", [])
        
        if contexts:
            for ctx in sorted(contexts, key=lambda x: x["coupling_ratio"]):
                with st.container(border=True):
                    cols = st.columns([2, 1, 1, 1])
                    cols[0].markdown(f"**Context**: `{ctx['name']}`")
                    cols[1].metric("Internal Edges", ctx["internal_edges"])
                    cols[2].metric("External Edges", ctx["external_edges"])
                    cols[3].metric("Coupling Ratio", ctx["coupling_ratio"])
                    
                    if ctx["is_transactional"] or ctx["handles_auth"]:
                        caps = []
                        if ctx["is_transactional"]: caps.append("Persistence")
                        if ctx["handles_auth"]: caps.append("Identity")
                        st.caption(f"Semantic Capabilities: {', '.join(caps)}")
        else:
            st.info("Insufficient architectural signals to infer bounded contexts.")

if __name__ == "__main__":
    show_layered_architecture()
