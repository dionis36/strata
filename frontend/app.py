import streamlit as st
import requests
import os

st.set_page_config(page_title="Strata - Phase 2", layout="wide")
st.title("Strata: Analysis Trigger")
st.markdown("Use this interface to trigger the Graph Extract & Metrics Engine.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
DATA_ROOT = "/data"

# ── Health Check Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Status")
    try:
        health_url = FASTAPI_URL if FASTAPI_URL.endswith("/health") else f"{FASTAPI_URL}/health"
        res = requests.get(health_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"Status: {data.get('status')}")
            st.info(f"Database: {data.get('database')}")
            st.caption(f"Version: {data.get('version')}")
        else:
            st.error(f"API returned status {res.status_code}")
    except requests.exceptions.RequestException:
        st.error("Failed to connect to API")


# ── Project Folder Discovery ─────────────────────────────────────────────────
def _list_project_folders(root: str) -> list[str]:
    """Return sorted list of directory names inside `root`.
    Excludes hidden entries (dotfiles) and anything that isn't a directory.
    """
    try:
        return sorted(
            entry for entry in os.listdir(root)
            if not entry.startswith(".")
            and os.path.isdir(os.path.join(root, entry))
        )
    except OSError:
        return []


# ── Main Content ─────────────────────────────────────────────────────────────
st.header("Analyze Workspace")

folders = _list_project_folders(DATA_ROOT)

if not folders:
    st.warning(
        "No project folders found in `/data`. "
        "Add a PHP project directory there and restart the analysis."
    )
    project_path = None
else:
    selected_folder = st.selectbox(
        "Select project folder",
        options=folders,
        format_func=lambda name: f"📁  {name}",
        help="Only directories inside /data are listed. "
             "PHP files, app.db, and graph JSONs are excluded."
    )
    project_path = os.path.join(DATA_ROOT, selected_folder)
    st.caption(f"Will scan: `{project_path}`")

    # Guard: never allow scanning the raw /data root
    if project_path == DATA_ROOT:
        st.error("Cannot run analysis on the root `/data` directory. Select a project sub-folder.")
        project_path = None

# ── Analysis Trigger ─────────────────────────────────────────────────────────
run_btn = st.button("Run Analysis", disabled=(project_path is None))

if run_btn and project_path:
    with st.spinner(f"Parsing PHP and building dependency graph for `{project_path}`…"):
        try:
            payload = {"project_path": project_path, "project_name": selected_folder}
            analyze_url = FASTAPI_URL.replace("/health", "") + "/analyze"
            response = requests.post(analyze_url, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                st.success("Analysis Complete!")
                st.info("Navigate to **Metrics Inspection** in the sidebar to view the structural matrix.")

                st.subheader("Structural Summary Card")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Run ID", result.get("run_id"))
                col2.metric("Files Evaluated", result.get("files"))
                col3.metric("Classes (Nodes)", result.get("classes"))
                col4.metric("Structural Edges", result.get("edges"))
            else:
                detail = response.json().get("detail", "Unknown error")
                st.error(f"Analysis failed: {detail}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
