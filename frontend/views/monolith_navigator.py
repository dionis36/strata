import streamlit as st
import requests
import pandas as pd
import os

def show_monolith_navigator():
    st.title("Monolith Navigator")
    st.markdown("##### The System Inventory & Component Map")
    
    with st.expander("💡 Why use the Navigator?", expanded=True):
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
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
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
    all_files = []
    for dname, dinfo in dirs.items():
        role = dinfo["type"].upper()
        role_counts[role] = role_counts.get(role, 0) + dinfo["count"]
        for f in dinfo["files"]:
            if isinstance(f, dict):
                fname = f["name"]
                frole = f["role"].upper()
            else:
                fname = f
                frole = role
                
            all_files.append({
                "File": fname,
                "Directory": dname,
                "Role": frole
            })

    st.markdown("### 🏷️ System Composition")
    cols = st.columns(len(role_counts))
    for i, (role, count) in enumerate(role_counts.items()):
        cols[i].metric(role, count)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Search & Filter ---
    st.markdown("#### Component Search")
    c1, c2 = st.columns([2, 1])
    search = c1.text_input("🔍 Search Files", placeholder="e.g. UserController")
    selected_role = c2.selectbox("Filter by Architectural Role", ["ALL"] + sorted(list(role_counts.keys())))

    # --- Inventory Table ---
    df = pd.DataFrame(all_files)
    if search:
        df = df[df["File"].str.contains(search, case=False)]
    if selected_role != "ALL":
        df = df[df["Role"] == selected_role]

    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- OOP Manifest (Symbols) ---
    st.markdown("---")
    st.subheader("🧩 Extracted Intelligence Manifest")
    st.info("This manifest lists the physical entities extracted from your code. It identifies potential 'God Objects' and behavioral risks.")
    
    l2 = data.get("layer_2", {})
    entities = l2.get("oop_entities", [])
    
    if entities:
        df_oop = pd.DataFrame(entities)
        
        # UI Prettification
        df_oop["Interactions"] = df_oop["side_effects"].apply(lambda x: ", ".join([s.split("::")[-1] for s in x]))
        df_oop["Complexity"] = df_oop["methods_count"].apply(lambda x: "High" if x > 20 else ("Medium" if x > 10 else "Low"))
        
        # Rename for clarity and replace empty boolean columns with concrete metrics
        df_oop["parent_class"] = df_oop["parent_class"].fillna("None")
        display_df = df_oop[["name", "namespace", "parent_class", "methods_count", "Complexity", "Interactions"]].copy()
        display_df.columns = ["Name", "Namespace", "Parent Class", "Method Count", "Structural Complexity", "System Interactions"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No deep symbols identified in this run.")

if __name__ == "__main__":
    show_monolith_navigator()

if __name__ == "__main__":
    show_monolith_navigator()
