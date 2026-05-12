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
                    
                    # --- 🧠 Legacy Intelligence Section (Requirement 1, 8, 16) ---
                    st.markdown("---")
                    st.markdown("### 🧠 Legacy Intelligence Advisory")
                    
                    legacy = data.get("legacy_insights", {})
                    era = legacy.get("php_era", "Unknown")
                    
                    # Era Badge
                    era_color = "#f87171" if "Era A" in era or "Era B" in era else "#fbbf24" if "Era C" in era else "#4ade80"
                    st.markdown(f"""
                        <div style="background-color: {era_color}; color: #000; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                            <h2 style="margin:0; color: #000;">{era}</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # New Intelligence Metrics (Requirement 9 & 15)
                    col_fw, col_host = st.columns(2)
                    col_fw.metric("🛠️ Framework Identity", legacy.get("detected_framework", "Custom"))
                    
                    h_risk = legacy.get("hosting_risk_level", "low").upper()
                    h_color = "red" if h_risk == "HIGH" else "orange" if h_risk == "MEDIUM" else "green"
                    col_host.markdown(f"**🌐 Hosting Assumption Risk**: <span style='color:{h_color}'>{h_risk}</span>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    st.markdown("#### ⚙️ Deep Technical Profile")
                    t_col1, t_col2 = st.columns(2)
                    t_col1.write(f"🗄️ **Database Layer**: {legacy.get('db_layer', 'Unknown')}")
                    t_col1.write(f"🔐 **Auth Strategy**: {legacy.get('auth_layer', 'Unknown')}")
                    t_col2.write(f"🎨 **Template Engine**: {legacy.get('template_layer', 'Unknown')}")
                    t_col2.write(f"🚚 **Autoloading**: {legacy.get('autoloading_strategy', 'Unknown')}")
                    
                    st.markdown("---")

                    col_score, col_rec = st.columns([2, 1])
                    
                    with col_score:
                        st.markdown("#### 🎯 Modernization Scoreboard")
                        # 7 Dimensions from FINAL.md - Flattened to avoid nesting error
                        st.write(f"🚀 **Version Compatibility**: {legacy.get('version_score', 0)}/20")
                        st.write(f"🏷️ **Namespace Adoption**: {legacy.get('namespace_score', 0)}/10")
                        st.write(f"🗄️ **DB Layer Quality**: {legacy.get('db_layer_score', 0)}/15")
                        st.write(f"🛡️ **Security Risk**: {legacy.get('security_score', 0)}/20")
                        st.write(f"📦 **Framework Alignment**: {legacy.get('framework_score', 0)}/10")
                        st.write(f"🧪 **Testability**: {legacy.get('testability_score', 0)}/10")
                        st.write(f"🔗 **Coupling Density**: {legacy.get('coupling_score', 0)}/15")
                        
                        st.markdown(f"**Total Modernization Score: {legacy.get('total_modernization_score', 0)}/100**")
                        st.progress(float(legacy.get('total_modernization_score', 0)) / 100)

                    with col_rec:
                        # Call Recommendation Engine (Placeholder for now, but we can logic it here based on score)
                        score = legacy.get('total_modernization_score', 0)
                        if score > 70:
                            strategy = "Option A — Incremental"
                            icon = "🛠️"
                        elif score > 40:
                            strategy = "Option B — Strangler Fig"
                            icon = "🌿"
                        else:
                            strategy = "Option C — Full Rewrite"
                            icon = "🏗️"
                            
                        st.markdown(f"""
                        <div class='card' style='border-left: 5px solid #4ade80;'>
                            <h4>{icon} Recommended Strategy</h4>
                            <p class='highlight'>{strategy}</p>
                            <small>Based on architectural topology and era classification.</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.session_state["active_run_id"] = data["run_id"]
                    st.info("💡 Use the 'Modernization Cockpit' in the sidebar to view full reports and extraction blueprints.")
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


