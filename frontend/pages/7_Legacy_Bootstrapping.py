import streamlit as st
import requests
import os

st.set_page_config(page_title="Legacy Bootstrapping", page_icon="🌳", layout="wide")

st.title("🌳 Legacy Bootstrapping (Req 3B)")
st.markdown("### Implicit Dependency Graph & Include Trees")
st.write("Visualizes procedural bootstrap chains, circular dependencies, and orphaned code paths detected by the AST.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

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
    st.warning("⚠️ No completed runs found. Please return to the Home page and run an Intelligence Scan.")
    st.stop()

selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
run_id = run_options[selected_run_label]

@st.cache_data(ttl=60)
def fetch_tree_data(rid):
    res = requests.get(f"{FASTAPI_URL}/graph/{rid}/includes")
    if res.status_code == 200:
        return res.json()
    return None

with st.spinner("Compiling structural trees..."):
    tree_data = fetch_tree_data(run_id)

if not tree_data:
    st.error("Failed to fetch legacy bootstrapping data. Ensure the backend is running.")
    st.stop()

# --- Top Row: Warnings & Dead Ends ---
col1, col2 = st.columns(2)
with col1:
    cycles = tree_data.get("circular_includes", [])
    st.markdown("#### 🚨 Circular Include Detection")
    if cycles:
        st.error(f"**{len(cycles)} Dependency Loops Detected**")
        with st.expander("View Circular Paths", expanded=True):
            for c in cycles:
                st.code(c, language="text")
    else:
        st.success("✅ No circular includes detected. Safe tree structure.")

with col2:
    orphans = tree_data.get("dead_includes", [])
    st.markdown("#### ⚠️ Dead Include Detection")
    if orphans:
        st.warning(f"**{len(orphans)} Orphaned Files Detected**")
        st.caption("These files are never included by any other file and are not standard entry points.")
        with st.expander("View Dead Files", expanded=True):
            st.code("\n".join(orphans), language="text")
    else:
        st.success("✅ No orphaned files detected. All code is reachable.")

st.markdown("---")

# --- Bottom Row: The Bootstrap Chain ---
st.markdown("#### 🔗 Full Bootstrap Chains")
st.write("Hierarchical representation of file dependencies (who includes who).")

adjacency = tree_data.get("bootstrap_chain", {})
if not adjacency:
    st.info("No explicit `include` or `require` statements found in this codebase.")
else:
    # Build a simple recursive viewer
    def render_tree(node, graph, depth=0, visited=None):
        if visited is None: visited = set()
        indent = "&nbsp;" * 8 * depth
        prefix = "└── " if depth > 0 else "📄 "
        st.markdown(f"{indent}{prefix}**{node}**", unsafe_allow_html=True)
        
        if node in visited:
            st.markdown(f"{indent}&nbsp;&nbsp;&nbsp;&nbsp;*(Circular Loop Break)*", unsafe_allow_html=True)
            return
            
        visited.add(node)
        for child in graph.get(node, []):
            render_tree(child, graph, depth + 1, visited.copy())
            
    # Find root nodes (nodes that are never included by anything else)
    in_degrees = {k: 0 for k in adjacency.keys()}
    for children in adjacency.values():
        for c in children:
            if c not in in_degrees: in_degrees[c] = 0
            in_degrees[c] += 1
            
    roots = [n for n, deg in in_degrees.items() if deg == 0]
    if not roots: roots = list(adjacency.keys())[:5] # Fallback if everything is a cycle
    
    with st.container():
        st.markdown("<div class='card' style='font-family: monospace; background: #111; padding: 20px; border-radius: 5px;'>", unsafe_allow_html=True)
        for root in roots:
            render_tree(root, adjacency)
            st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
