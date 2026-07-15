import streamlit as st
import requests
import pandas as pd
import os
from views import page_registry
from views.severity import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW

def show_monolith_navigator():
    st.title("System Structure")
    st.markdown("##### The System Inventory & Component Map")
    
    with st.expander("Why use the Navigator?", expanded=True):
        st.markdown("""
        The Navigator provides **Technical Determinism**. It classifies every file into a strategic role, 
        helping you separate the 'Display' layer from the 'Business' logic. 
        
        **Your Goal**: Identify high-density 'SRC' directories that should be classified into 
        Controllers or Services to reduce architectural debt.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis selected. Select a run from the **side panel** or start a new scan from the **Executive Dashboard**.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    @st.cache_data(ttl=60)
    def fetch_inventory(rid):
        res = requests.get(f"{FASTAPI_URL}/layer-analysis/{rid}")
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_inventory(run_id)
    if not data:
        st.error("Unable to load component inventory.")
        return

    # --- Summary Metrics ---
    l1 = data.get("layer_1", {})
    dirs = l1.get("directories", {})
    
    role_counts = {}
    for dname, dinfo in dirs.items():
        role = dinfo["type"].upper()
        role_counts[role] = role_counts.get(role, 0) + dinfo["count"]

    st.markdown("### System Composition")
    ROLE_HELP = {
        "STANDARD":    "General-purpose application directories containing core backend logic, services, or mixed-role files.",
        "VENDOR":      "External third-party dependency directories. These are excluded from structural risk analysis they cannot be refactored by your team.",
        "ENTRY_POINT": "Directories containing web-accessible scripts. These are the public surface area of the application that receives incoming HTTP requests.",
        "ASSET":       "Public static files (CSS, JS, images). No business logic excluded from modernization scope.",
        "BOOTSTRAP":   "Framework initialization files. Changing these has cascading effects across the entire application startup sequence.",
        "CONFIG":      "Configuration files. These often contain hardcoded environment assumptions that block containerization.",
    }
    cols = st.columns(len(role_counts))
    for i, (role, count) in enumerate(role_counts.items()):
        cols[i].metric(role, count, help=ROLE_HELP.get(role, f"Files classified as {role} by the architectural scanner."))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- File Structure Tree ---
    st.markdown("#### System File Structure")
    
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
        
    col1, col2 = st.columns([1, 2])
    with col1:
        search_term = st.text_input("Search", placeholder="Filter codebase...", label_visibility="collapsed").lower()
    
    def generate_html_tree(node, depth=0):
        html = ""
        for name, data in sorted(node.items(), key=lambda x: x[0]):
            info = data["_info"]
            children_html = generate_html_tree(data["_children"], depth + 1)
            
            # Auto-expand up to the system root, or if a folder only contains one sub-directory (passthrough)
            is_passthrough = len(node) == 1 and not (info and info.get("files", []))
            open_attr = "open" if (depth < 2 or is_passthrough) else ""
            
            if info:
                summary = f"<b>{name}/</b>"
                files_html = ""
                for f_obj in info.get("files", []):
                    fname = f_obj["name"] if isinstance(f_obj, dict) else f_obj
                    
                    if search_term and search_term not in fname.lower() and search_term not in name.lower():
                        continue
                    
                    files_html += f"<div style='padding-left: 20px; font-size: 0.9rem; opacity: 0.8;'>{fname}</div>"

                if search_term and not files_html and not children_html and search_term not in name.lower():
                    continue

                html += f"<details {open_attr} style='margin-left: 15px; margin-bottom: 2px;'><summary style='cursor: pointer;'>{summary}</summary><div style='border-left: 1px solid rgba(128,128,128,0.2); margin-left: 6px; padding-top: 2px; padding-bottom: 2px;'>{files_html}{children_html}</div></details>"
            else:
                if search_term and not children_html and search_term not in name.lower():
                    continue
                html += f"<details {open_attr} style='margin-left: 15px;'><summary style='cursor: pointer;'><b>{name}/</b></summary><div style='border-left: 1px solid rgba(128,128,128,0.2); margin-left: 6px; padding-top: 2px; padding-bottom: 2px;'>{children_html}</div></details>"
        return html

    tree_html = generate_html_tree(tree)
    if not tree_html:
        tree_html = "<div style='opacity: 0.5; font-style: italic;'>No files match your search.</div>"

    # Wrap the CSS and HTML in a SINGLE markdown call to prevent Streamlit from auto-closing the div wrapper
    st.markdown(f"""
        <style>
        details > summary {{
            list-style-type: none; 
        }}
        details > summary::-webkit-details-marker {{
            display: none;
        }}
        details > summary::before {{
            content: '▶';
            font-size: 0.7em;
            margin-right: 6px;
            display: inline-block;
            transition: transform 0.2s;
            opacity: 0.6;
        }}
        details[open] > summary::before {{
            transform: rotate(90deg);
        }}
        </style>
        <div style="font-family: 'Inter', sans-serif; padding: 15px; border-radius: 8px; border: 1px solid rgba(128,128,128,0.2); max-height: 600px; overflow-y: auto;">
            {tree_html}
        </div>
    """, unsafe_allow_html=True)

    # --- OOP Manifest (Symbols) ---
    st.markdown("---")
    st.subheader("Extracted Assessment Manifest")
    st.info("This manifest lists the physical entities extracted from your code. It identifies potential 'God Objects' and behavioral risks.")
    
    l2 = data.get("layer_2", {})
    entities = l2.get("oop_entities", [])
    
    if entities:
        df_oop = pd.DataFrame(entities)
        
        # UI Prettification
        df_oop["Interactions"] = df_oop["side_effects"].apply(lambda x: ", ".join([s.split("::")[-1] for s in x]) if x else "none")
        df_oop["Complexity"] = df_oop["methods_count"].apply(lambda x: SEVERITY_CRITICAL if x > 20 else (SEVERITY_HIGH if x > 15 else (SEVERITY_MEDIUM if x > 10 else SEVERITY_LOW)))
        
        # Rename for clarity and replace empty boolean columns with concrete metrics
        df_oop["parent_class"] = df_oop["parent_class"].fillna("None")
        display_df = df_oop[["name", "namespace", "parent_class", "methods_count", "Complexity", "Interactions"]].copy()
        display_df.columns = ["Name", "Namespace", "Parent Class", "Method Count", "Structural Complexity", "System Interactions"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### Component Density Assessment")
        
        total_entities = len(df_oop)
        high_complexity = len(df_oop[df_oop["Complexity"] == "High"])
        gravity_well = df_oop.sort_values(by="methods_count", ascending=False).iloc[0] if total_entities > 0 else None
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Object Encapsulation Insight</h4>
                <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">High-Complexity Object Concentration measures whether logic is evenly distributed across many single-responsibility classes or concentrated in a few bloated objects. A high number of complex classes (> 20 methods) indicates a heavy, tightly-coupled OOP architecture that resists extraction.</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**METRIC**: High-Complexity Object Concentration")
            st.markdown("**INTERPRETATION**: This metric assesses whether logic is evenly distributed across many single-responsibility classes or concentrated in a few bloated objects. A high number of complex classes indicates a heavy, tightly-coupled OOP architecture.")
            st.markdown(f"**EVIDENCE**: \n1. Total recognized entities: {total_entities}.\n2. Entities flagged with 'High' complexity (> 20 methods): {high_complexity}.")
            st.markdown("**RECOMMENDATION**: Focus refactoring efforts on the 'High' complexity entities. If the system is mostly procedural (few entities), proceed to look at standalone scripts instead of classes.")

        with col2:
            st.markdown("""
            <div style="background-color: rgba(33,195,84,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Gravity Wells (God Objects)</h4>
                <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Method Weight & Interaction Gravity 'Gravity Wells' are massive God Objects containing so much logic they attract dependencies from across the entire system. They are the primary anti-corruption targets: breaking them apart is mandatory before attempting to split the system into microservices.</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**METRIC**: Method Weight & Interaction Gravity")
            st.markdown("**INTERPRETATION**: 'Gravity Wells' are massive God Objects that contain so much logic they attract dependencies from across the entire system. Breaking these apart is mandatory before attempting to split the system into microservices.")
            
            if gravity_well is not None and gravity_well["methods_count"] > 10:
                ev1_gw = f"The heaviest entity is `{gravity_well['name']}` with {gravity_well['methods_count']} methods."
                ev2_gw = f"Detected side-effects: {gravity_well['Interactions'] if gravity_well['Interactions'] else 'None mapped'}."
            else:
                ev1_gw = "No massive God Objects detected."
                ev2_gw = "Logic weight appears evenly distributed."
                
            st.markdown(f"**EVIDENCE**: \n1. {ev1_gw}\n2. {ev2_gw}")
            st.markdown("**RECOMMENDATION**: Treat 'Gravity Wells' as your primary anti-corruption targets. Begin by extracting small, self-contained traits or helper classes from the heaviest entity.")
    else:
        st.info("No deep symbols identified in this run.")

if __name__ == "__main__":
    show_monolith_navigator()


