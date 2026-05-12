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
    ### 🏛️ The Oracle for Your Monolith
    Strata is a specialized **Modernization Advisory Platform** that provides mathematical certainty 
    to the complex journey of decoupling legacy systems.
    
    #### 🚀 Three Steps to Modernization:
    1.  **Analyze**: Run the **Intelligence Engine** to map the systemic topology and risk DNA.
    2.  **Explore**: Use the **Monolith Navigator** to visually identify architectural chokepoints.
    3.  **Plan**: Generate **Surgical Blueprints** and ROI reports in the **Modernization Cockpit**.
    """)
    
    st.markdown("---")
    st.subheader("🛠️ Current Project Configuration")
    
    project_path = st.text_input("Source Path", value="/data/test_project_1")
    project_name = st.text_input("Project Name", value="Strata_Monolith_Alpha")
    
    if st.button("🚀 Run Deep Intelligence Scan", type="primary"):
        FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
        try:
            payload = {"project_path": project_path, "project_name": project_name}
            res = requests.post(f"{FASTAPI_URL}/analyze", json=payload)
            if res.status_code == 200:
                st.success(f"Intelligence Scan Started! (Run ID: {res.json()['run_id']})")
                st.balloons()
            else:
                st.error(f"Analysis failed: {res.text}")
        except Exception as e:
            st.error(f"Could not connect to Intelligence Engine: {e}")

with col_start:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ System Status")
    st.markdown("- **Engine**: <span class='highlight'>Active (Parallel)</span>", unsafe_allow_html=True)
    st.markdown("- **Caching**: <span class='highlight'>Delta-Scan Enabled</span>", unsafe_allow_html=True)
    st.markdown("- **CLI**: <span class='highlight'>Ready</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### 🎯 Quick Navigation")
    if st.button("🕸️ Open Monolith Navigator", use_container_width=True):
        st.info("Select 'Monolith Navigator' from the sidebar to begin exploration.")
    if st.button("🕹️ Open Modernization Cockpit", use_container_width=True):
        st.info("Select 'Modernization Cockpit' from the sidebar to plan extractions.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Strata v1.0.0-Competition | Managed by Antigravity AI")
