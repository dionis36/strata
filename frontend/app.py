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
    /* Minimalist Dark Theme */
    .main { background-color: #0e1117; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; letter-spacing: -0.02em !important; }
    .stMetric { background-color: #161b22; border-radius: 8px; padding: 15px; border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #161b22; 
        border-radius: 4px 4px 0 0; 
        padding: 8px 16px; 
        border: 1px solid #30363d;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] { background-color: #1f2937 !important; color: #ffffff !important; border-bottom: 2px solid #58a6ff !important; }
    
    /* Clean Buttons */
    .stButton>button { 
        border-radius: 6px !important; 
        border: 1px solid #30363d !important; 
        background-color: #21262d !important; 
        color: #c9d1d9 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { border-color: #8b949e !important; background-color: #30363d !important; }
    
    /* Hide Streamlit Top Bar but preserve Sidebar Headers */
    [data-testid="stHeader"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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

pg = st.navigation(pages)

# --- Global Context Sidebar ---
with st.sidebar:
    st.markdown("### Strata")
    st.markdown("<span style='color: #8b949e; font-size: 0.8rem;'>v1.0.0 Enterprise</span>", unsafe_allow_html=True)
    st.markdown("---")
    
    # ── Context Switcher ──
    st.markdown("##### Global Context")
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    import requests
    try:
        runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=2)
        if runs_res.status_code == 200:
            available_runs = runs_res.json()
            run_options = {f"Run {r['id']} ({r['started_at'][:10]})": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
            if run_options:
                current_run_id = st.session_state.get("active_run_id")
                # Find current index or default to 0
                run_keys = list(run_options.keys())
                try:
                    current_idx = next(i for i, k in enumerate(run_keys) if run_options[k] == current_run_id)
                except StopIteration:
                    current_idx = 0
                
                selected_run_label = st.selectbox("Active Analysis Run", run_keys, index=current_idx)
                if st.session_state.get("active_run_id") != run_options[selected_run_label]:
                    st.session_state["active_run_id"] = run_options[selected_run_label]
                    st.rerun()
    except Exception:
        st.caption("Unable to fetch run history.")
    
    st.markdown("---")
    
    # ── Process Flow Guide ──
    st.markdown("##### Modernization Journey")
    st.markdown("""
    - **A. Dashboard**: Project Overview
    - **B. Discovery**: Map the structure & Topology
    - **C. Intelligence**: Audit deep risks
    - **D. Roadmap**: Strategic Advisory
    - **E. Artifacts**: Downloads & Exports
    """)
    st.markdown("---")

pg.run()
