import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Strata - Modernization Intelligence",
    page_icon="🚀",
    layout="wide"
)

# Premium Dark Mode Branding
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    h1 { color: #ffffff !important; font-size: 3rem !important; margin-bottom: 0px !important; }
    .stButton>button { background-color: #4ade80 !important; color: #000 !important; font-weight: bold !important; border: none !important; }
    .card { background-color: #1a1c24; border: 1px solid #333; padding: 25px; border-radius: 10px; margin-bottom: 20px; }
    .highlight { color: #4ade80; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Strata")
st.markdown("<h3 style='color: #888;'>Enterprise Monolith Modernization Intelligence</h3>", unsafe_allow_html=True)
st.markdown("---")

# ── Quick Start Hub ───────────────────────────────────────────────────────────
col_info, col_start = st.columns([2, 1])

with col_info:
    st.markdown("""
    ### 🏗️ Strata: Architectural Intelligence Platform
    Strata is a specialized **Modernization Advisory Platform** that provides technical determinism 
    and risk quantization for the complex journey of decoupling legacy systems.
    
    #### 🚀 Three Steps to Modernization:
    1.  **Analyze**: Run the **Intelligence Engine** to map the systemic topology and risk DNA.
    2.  **Explore**: Use the **Monolith Navigator** to visually identify architectural chokepoints.
    3.  **Plan**: Generate **Surgical Blueprints** and ROI reports in the **Modernization Cockpit**.
    """)
    
    st.markdown("---")
    st.subheader("🛠️ Current Project Configuration")
    
    # --- Auto-Discovery for /data folder ---
    data_dir = "/data"
    try:
        available_projects = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        available_projects = sorted(available_projects)
    except Exception:
        available_projects = []

    if not available_projects:
        st.warning("⚠️ No projects found in /data. Please add your monolith to the 'data/' folder on your host.")
        project_name_slug = st.text_input("Project Name (Slug)", value="Strata_Monolith")
        project_path = "/data" # Fallback
    else:
        selected_project = st.selectbox("Select Monolith from In-Box (/data)", available_projects)
        project_path = os.path.join(data_dir, selected_project)
        project_name_slug = st.text_input("Project Name (Slug)", value=selected_project.replace("-", "_").capitalize())
    
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    if st.button("🚀 Run Deep Intelligence Scan", use_container_width=True):
        with st.spinner("Executing Deep Intelligence Pipeline..."):
            try:
                res = requests.post(f"{FASTAPI_URL}/analyze", json={
                    "project_name": project_name_slug,
                    "project_path": project_path
                }, timeout=300)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"✅ Intelligence Scan Complete! (Run ID: {data['run_id']})")
                    
                    # --- 📊 Instant Summary Card ---
                    st.markdown("### 📊 Scan Summary")
                    col_f, col_c, col_e = st.columns(3)
                    col_f.metric("Files Processed", data.get("files", 0))
                    col_c.metric("Classes Identified", data.get("classes", 0))
                    col_e.metric("Dependencies Mapped", data.get("edges", 0))
                    
                    st.session_state["active_run_id"] = data["run_id"]
                    st.info("💡 Use the sidebar to explore the specific metrics and risk profiles for this run.")
                else:
                    st.error(f"Scan Failed: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

with col_start:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ System Status")
    st.markdown("- **Engine**: <span class='highlight'>Active (Parallel)</span><br><small>Multi-core AST parsing enabled.</small>", unsafe_allow_html=True)
    st.markdown("- **Caching**: <span class='highlight'>Delta-Scan Enabled</span><br><small>Hash-based incremental analysis.</small>", unsafe_allow_html=True)
    st.markdown("- **CLI**: <span class='highlight'>Ready</span><br><small>Headless mode available for CI/CD.</small>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### 🎯 Quick Navigation")
    if st.button("🕸️ Open Monolith Navigator", use_container_width=True):
        st.info("Select 'Monolith Navigator' from the sidebar to begin exploration.")
    if st.button("🕹️ Open Modernization Cockpit", use_container_width=True):
        st.info("Select 'Modernization Cockpit' from the sidebar to plan extractions.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Strata v1.0.0-Competition | Advanced Modernization Advisor")
