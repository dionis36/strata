import streamlit as st
import requests
import os

def show_dashboard():
    st.title("Project Dashboard")
    st.markdown("### Modernization Command Center")
    st.markdown("---")

    # ── Quick Start Hub ───────────────────────────────────────────────────────────
    col_info, col_start = st.columns([2, 1])

    with col_info:
        st.markdown("""
        ### Architectural Intelligence Platform
        Strata provides technical determinism and risk quantization for decoupling legacy systems.
        
        **Methodology:**
        1.  **Analyze**: Execute the Intelligence Engine to map systemic topology.
        2.  **Explore**: Navigate the monolith to identify architectural chokepoints.
        3.  **Plan**: Generate surgical blueprints and ROI reports.
        """)
        
        st.markdown("---")
        st.subheader("Project Configuration")
        
        data_dir = "/data"
        try:
            available_projects = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
            available_projects = sorted(available_projects)
        except Exception:
            available_projects = []

        if not available_projects:
            st.warning("No projects found in /data. Please verify the volume mount.")
            project_name_slug = st.text_input("Project Name (Slug)", value="Strata_Monolith")
            project_path = "/data"
        else:
            selected_project = st.selectbox("In-Box Projects", available_projects)
            project_path = os.path.join(data_dir, selected_project)
            project_name_slug = st.text_input("Project Slug", value=selected_project.replace("-", "_").lower())
        
        FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
        if st.button("Execute Deep Intelligence Scan", use_container_width=True):
            with st.spinner("Analyzing codebase..."):
                try:
                    res = requests.post(f"{FASTAPI_URL}/analyze", json={
                        "project_name": project_name_slug,
                        "project_path": project_path
                    }, timeout=300)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Analysis complete. Run ID: {data['run_id']}", icon=":material/check_circle:")
                        st.session_state["active_run_id"] = data["run_id"]
                        st.session_state["project_slug"] = project_name_slug
                        
                        # --- Metrics Grid ---
                        st.markdown("---")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("📄 Files Processed", data.get("files", 0))
                        m2.metric("🧩 Entities Identified", data.get("classes", 0))
                        m3.metric("🔗 Dependencies Mapped", data.get("edges", 0))
                        
                        # --- Intelligence Advisory ---
                        legacy = data.get("legacy_insights", {})
                        era = legacy.get("php_era", "Unknown")
                        
                        st.markdown(f"#### Era Classification: **{era}**")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.info(f"**Framework**: {legacy.get('detected_framework', 'Custom')}")
                            st.info(f"**Database**: {legacy.get('db_layer', 'Unknown')}")
                        with c2:
                            h_risk = legacy.get("hosting_risk_level", "low").upper()
                            st.info(f"**Hosting Risk**: {h_risk}")
                            st.info(f"**Auth Layer**: {legacy.get('auth_layer', 'Unknown')}")
                    else:
                        st.error(f"Analysis failed: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    with col_start:
        st.markdown("<div style='background-color: #1a1c24; padding: 20px; border-radius: 10px; border: 1px solid #333;'>", unsafe_allow_html=True)
        st.markdown("#### ⚙️ System Integrity")
        st.markdown("- **Engine**: Active (Parallel AST)")
        st.markdown("- **Cache**: Delta-Scan Enabled")
        st.markdown("- **Mode**: Enterprise Advisory")
        
        st.markdown("---")
        st.markdown("#### 🏷️ Active Context")
        run_id = st.session_state.get("active_run_id", "None")
        st.markdown(f"**Run ID**: `{run_id}`")
        st.markdown(f"**Project**: `{st.session_state.get('project_slug', 'None')}`")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("active_run_id"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Next Steps")
            st.markdown("""
            1.  **Map Topology**: Visit **Monolith Navigator**.
            2.  **Audit Data**: Check **Database Intelligence**.
            3.  **Inspect Risk**: View **Modernization Risk**.
            4.  **Simulate**: Use **Extraction Simulator**.
            """)

if __name__ == "__main__":
    show_dashboard()
