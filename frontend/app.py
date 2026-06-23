import streamlit as st
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Strata | Modernization Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global Style Overrides ---
st.markdown("""
    <style>
    /* Typography and layout tweaks (No hardcoded colors) */
    .main { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.02em !important; }
    .stMetric { border-radius: 8px; padding: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px 4px 0 0; padding: 8px 16px; }
    
    .stButton>button { border-radius: 6px !important; font-weight: 500 !important; transition: all 0.2s ease; }
    
    /* Streamlit Top Bar and Menu are enabled for Theme Switching */
    </style>
""", unsafe_allow_html=True)

# --- Navigation Architecture ---
from views.dashboard import show_dashboard
from views.executive_roadmap import show_executive_roadmap
from views.monolith_navigator import show_monolith_navigator
from views.layered_architecture import show_layered_architecture, show_system_topology, show_bounded_contexts
from views.database_intelligence import show_database_intelligence
from views.global_state_intelligence import show_global_state_intelligence
from views.legacy_intelligence import show_legacy_intelligence
from views.risk_audit import show_risk_audit
from views.extraction_simulator import show_extraction_simulator
from views.decision_engine import show_modernization_decision_engine
from views.legacy_bootstrapper import show_legacy_bootstrapper

from views.boundary_intelligence import show_boundary_intelligence
from views.artifact_center import show_artifact_center

# Modern Streamlit Navigation (v1.31+)
pages = {
    "A. Command Center": [
        st.Page(show_dashboard, title="Executive Dashboard", icon=":material/dashboard:"),
    ],
    "B. Architectural Discovery": [
        st.Page(show_monolith_navigator, title="Monolith Navigator", icon=":material/hub:"),
        st.Page(show_layered_architecture, title="Layered Structure", icon=":material/layers:"),
        st.Page(show_system_topology, title="System Topology", icon=":material/account_tree:"),
        st.Page(show_bounded_contexts, title="Bounded Contexts", icon=":material/group_work:"),
    ],
    "C. Intelligence Reports": [
        st.Page(show_database_intelligence, title="Database Intelligence", icon=":material/storage:"),
        st.Page(show_global_state_intelligence, title="Runtime & Global State", icon=":material/memory:"),
        st.Page(show_legacy_intelligence, title="Legacy PHP Intelligence", icon=":material/history:"),
        st.Page(show_risk_audit, title="Modernization Risk", icon=":material/gpp_maybe:"),
        st.Page(show_boundary_intelligence, title="Boundary Intelligence", icon=":material/public:"),
    ],
    "D. Strategic Advisory": [
        st.Page(show_modernization_decision_engine, title="Modernization Decision Engine", icon=":material/psychology:"),
        st.Page(show_extraction_simulator, title="Extraction Simulator", icon=":material/biotech:"),
        st.Page(show_executive_roadmap, title="Strategic Roadmap", icon=":material/insights:"),
        st.Page(show_legacy_bootstrapper, title="Legacy Bootstrapper", icon=":material/build:"),
    ],
    "E. Artifact Center": [
        st.Page(show_artifact_center, title="Artifact Center", icon=":material/download:"),
    ]
}

@st.dialog("User Guide", width="large")
def show_user_guide():
    st.markdown("""
    ### Welcome to Strata
    Strata is an enterprise-grade static analysis platform built to untangle legacy monoliths and guide your modernization strategy.

    #### Navigation Workflow
    1. **A. Command Center:** Start here to initialize new code scans, switch between active projects, and view high-level system readiness scores.
    2. **B. Architectural Discovery:** Use the interactive *System Topology* and *Bounded Contexts* graphs to visually identify "God Classes" and tangled dependencies.
    3. **C. Intelligence Reports:** Deep-dive into specific architectural debts. The *Database Intelligence* and *Global State* tabs are critical for finding hidden couplings before extracting microservices.
    4. **D. Strategic Advisory:** Use the *Extraction Simulator* to mathematically preview the risk impact of moving a class into its own service before you write any code.
    5. **E. Artifact Center:** Export your findings into Executive PDFs, SARIF security logs, or automated `rector.php` refactoring rules.
    """)

# --- Global Context Sidebar ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 2.4rem; font-weight: 800; letter-spacing: -0.04em; margin-top: 0; padding-top: 0;'>Strata</h1>", unsafe_allow_html=True)
    
    if st.button("User Guide", use_container_width=True):
        show_user_guide()
        
    st.write("") # Small spacer
    
    # ── Context Switcher ──
    st.markdown("**Global Context**")
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    import requests
    try:
        runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=2)
        if runs_res.status_code == 200:
            available_runs = runs_res.json()
            valid_statuses = ['COMPLETED', 'ANALYSIS_COMPLETE', 'INTELLIGENCE_READY', 'INTELLIGENCE_FAILED', 'SYNTHESIZING_FINDINGS', 'SYNTHESIZING_SUMMARY', 'SYNTHESIZING_RECTOR']
            run_options = {f"Run {r['id']} ({r['started_at'][:10]})": r['id'] for r in available_runs if r.get('status', '').upper() in valid_statuses}
            if run_options:
                current_run_id = st.session_state.get("active_run_id")
                run_keys = list(run_options.keys())
                try:
                    current_idx = next(i for i, k in enumerate(run_keys) if run_options[k] == current_run_id)
                except StopIteration:
                    current_idx = 0
                
                selected_run_label = st.selectbox("Active Analysis Run", run_keys, index=current_idx, label_visibility="collapsed")
                selected_run_id = run_options[selected_run_label]
                
                # Always ensure project_id stays in sync with run_id
                current_r = next((r for r in available_runs if r['id'] == selected_run_id), None)
                if current_r and 'project_id' in current_r:
                    st.session_state["active_project_id"] = current_r['project_id']

                if st.session_state.get("active_run_id") != selected_run_id:
                    st.session_state["active_run_id"] = selected_run_id
                    st.rerun()
    except requests.exceptions.RequestException:
        st.caption("Unable to connect to API.")
    except Exception as e:
        if e.__class__.__name__ == "RerunException":
            raise e
        st.error(f"Error: {str(e)}")
    
    st.write("") # Small spacer
    
    # ── Page Navigations ──
    for section, section_pages in pages.items():
        st.markdown(f"**{section}**")
        for page in section_pages:
            st.page_link(page, icon=page.icon)

pg = st.navigation(pages, position="hidden")
pg.run()
