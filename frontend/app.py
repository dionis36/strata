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
    
    /* Global Tooltip Styles */
    .strata-tooltip-container {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: default;
        opacity: 0.6;
    }
    .strata-tooltip-container:hover {
        opacity: 1;
    }
    .strata-tooltip-text {
        visibility: hidden;
        background-color: var(--background-color, #ffffff) !important;
        color: var(--text-color, #31333F) !important;
        text-align: left;
        border-radius: 0.5rem;
        padding: 0.5rem 0.75rem;
        position: absolute;
        z-index: 999999;
        bottom: 140%;
        right: -10px;
        width: 320px;
        font-size: 14px;
        line-height: 1.4;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
        font-weight: 400 !important;
        pointer-events: none;
        border: 1px solid rgba(128,128,128,0.2);
    }
    .strata-tooltip-container:hover .strata-tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    
    /* --- Sidebar UX Refinements --- */
    /* 1. Fix gaps around dividers */
    [data-testid="stSidebar"] hr {
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* 2. Borderless accordions */
    [data-testid="stSidebar"] details {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    
    /* 3. Bold, slightly larger group titles */
    [data-testid="stSidebar"] summary p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }
    
    /* 4. Hide native expander toggle arrows in the sidebar */
    [data-testid="stSidebar"] div[data-testid="stExpander"] summary svg {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Navigation Architecture ---
from views.dashboard import show_dashboard
from views.executive_roadmap import show_executive_roadmap
from views.monolith_navigator import show_monolith_navigator
from views.layered_architecture import show_system_topology, show_bounded_contexts
from views.database_intelligence import show_database_intelligence
from views.global_state_intelligence import show_global_state_intelligence
from views.legacy_intelligence import show_legacy_intelligence
from views.risk_audit import show_risk_audit
from views.extraction_simulator import show_extraction_simulator
from views.decision_engine import show_modernization_decision_engine
from views.boundary_intelligence import show_boundary_intelligence
from views.report_viewer import show_report_viewer
from views.run_comparison import show_run_comparison
from views import page_registry

# Named Page objects for pages that are cross-referenced by in-page navigation
# buttons. Populated into page_registry so view files can import the exact same
# registered object - avoids the st.switch_page(st.Page(...)) anti-pattern.
_page_dashboard = st.Page(show_dashboard, title="Executive Dashboard", icon=":material/dashboard:")
_page_run_comparison = st.Page(show_run_comparison, title="Run Comparison", icon=":material/compare_arrows:")
_page_monolith_navigator = st.Page(show_monolith_navigator, title="System Structure", icon=":material/hub:")
_page_system_topology = st.Page(show_system_topology, title="System Topology", icon=":material/account_tree:")
_page_bounded_contexts = st.Page(show_bounded_contexts, title="Bounded Contexts", icon=":material/group_work:")

_page_database_intelligence = st.Page(show_database_intelligence, title="Database Intelligence", icon=":material/storage:")
_page_global_state_intelligence = st.Page(show_global_state_intelligence, title="Runtime & Global State", icon=":material/memory:")
_page_legacy_intelligence = st.Page(show_legacy_intelligence, title="Legacy PHP Intelligence", icon=":material/history:")
_page_risk_audit = st.Page(show_risk_audit, title="Modernization Risk", icon=":material/gpp_maybe:")
_page_boundary_intelligence = st.Page(show_boundary_intelligence, title="Boundary Intelligence", icon=":material/public:")

_page_decision_engine = st.Page(show_modernization_decision_engine, title="Modernization Decision Engine", icon=":material/psychology:")
_page_extraction_simulator = st.Page(show_extraction_simulator, title="Extraction Simulator", icon=":material/biotech:")
_page_executive_roadmap = st.Page(show_executive_roadmap, title="Strategic Roadmap", icon=":material/insights:")
_page_report_viewer = st.Page(show_report_viewer, title="Report Viewer", icon=":material/description:")

page_registry.PAGE_DASHBOARD = _page_dashboard
page_registry.PAGE_RISK_AUDIT = _page_risk_audit
page_registry.PAGE_BOUNDARY_INTELLIGENCE = _page_boundary_intelligence
page_registry.PAGE_REPORT_VIEWER = _page_report_viewer
page_registry.PAGE_RUN_COMPARISON = _page_run_comparison

# Modern Streamlit Navigation (v1.31+)
pages = {
    "Command Center": [
        _page_dashboard,
        _page_run_comparison,
    ],
    "Architectural Discovery": [
        _page_monolith_navigator,
        _page_system_topology,
        _page_bounded_contexts,
    ],
    "Intelligence Reports": [
        _page_database_intelligence,
        _page_global_state_intelligence,
        _page_legacy_intelligence,
        _page_risk_audit,
        _page_boundary_intelligence,
    ],
    "Strategic Advisory": [
        _page_decision_engine,
        _page_extraction_simulator,
        _page_executive_roadmap,
    ]
}

@st.dialog("User Guide", width="large")
def show_user_guide():
    st.session_state["show_user_guide"] = False
    st.subheader("Welcome to Strata")
    st.markdown(
        "Strata is an enterprise-grade modernization advisory platform designed to analyze legacy monoliths, identify architectural risk, and generate structured migration blueprints."
    )
    
    tab1, tab2, tab3 = st.tabs([
        "Overview & Workflow",
        "Sidebar Modules",
        "Architectural Concepts"
    ])
    
    with tab1:
        st.markdown("### The Modernization Workflow")
        st.caption(
            "Strata helps you navigate the transition from legacy monoliths to modern, modular architectures. "
            "Follow these key phases to modernize your codebase:"
        )
        
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            st.markdown("**Phase 1: Ingestion & Scan**")
            st.markdown(
                "1. **Provision Code**: Place your legacy files in the local `data/` folder\n\n"
                "2. **Trigger Scan**: Go to the **Executive Dashboard**, enter the container path, and run the intelligence scan."
            )
        with w_col2:
            st.markdown("**Phase 2: Discover & Analyze**")
            st.markdown(
                "3. **Audit Topology**: Use the **Monolith Navigator** and topology graphs to identify God Classes and cycles.\n\n"
                "4. **Analyze Coupling**: Inspect database dependencies and global state risks in **Intelligence Reports**."
            )
        with w_col3:
            st.markdown("**Phase 3: Simulate & Export**")
            st.markdown(
                "5. **Simulate Extraction**: Use the **Extraction Simulator** to model changes in Blast Radius and dependency flow.\n\n"
                "6. **Export Roadmaps**: Generate step-by-step modernization guides and Neo4j Cypher/AI JSON metadata."
            )
        st.info("Tip: You can switch between active workspace runs anytime using the drop-down menu in the sidebar.")

    with tab2:
        st.markdown("### Sidebar Navigation Categories")
        st.caption("The sidebar organizes Strata's analytical tools into four primary sections:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Command Center")
            st.markdown("Start here to initialize new code scans, switch between active projects/runs, and view high-level system readiness scores.")
            
            st.write("") # Spacer
            st.markdown("##### Architectural Discovery")
            st.markdown("Use interactive dependency graphs, heatmaps, and layered structures to visually trace class dependencies and identify God Objects.")
            
        with col2:
            st.markdown("##### Intelligence Reports")
            st.markdown("Deep-dive into technical debt reports, including database query coupling, runtime global state usage, and legacy version risks.")
            
            st.write("") # Spacer
            st.markdown("##### Strategic Advisory")
            st.markdown("Simulate the risk impact of class extraction, get advisory decisions, and export surgical modernization blueprints.")
            
    with tab3:
        st.markdown("### Key Architectural Metrics")
        st.caption("Strata uses deterministic graph theory and structural metrics to assess your system's design:")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown("**Blast Radius**")
            st.caption(
                "The percentage of the system that could be impacted by a change in this specific component. "
                "A lower blast radius indicates better decoupling."
            )
            
            st.markdown("**Systemic Gravity & Weight**")
            st.caption(
                "A metric based on in-degree and out-degree centrality. "
                "High gravity components pull the rest of the application into their orbit."
            )
            
        with m_col2:
            st.markdown("**Acyclic Guarantee**")
            st.caption(
                "Verification that dependencies flow in one direction without circular loops, ensuring clean encapsulation."
            )
            
            st.markdown("**Modernization ROI**")
            st.caption(
                "Estimated return on investment for decoupling a specific class, based on structural risk reduction "
                "divided by extraction complexity."
            )
            
        st.success("Strata is a read-only static analyzer. It never modifies your source files, making it safe to run on any codebase.")

# --- Global Context Sidebar ---
def trigger_user_guide():
    st.session_state["show_user_guide"] = True

with st.sidebar:
    st.markdown("<h1 style='font-size: 2.4rem; font-weight: 800; letter-spacing: -0.04em; margin-top: 0; padding-top: 0;'>Strata</h1>", unsafe_allow_html=True)
    
    st.button("User Guide", use_container_width=True, on_click=trigger_user_guide)
        
    st.write("") # Small spacer
    
    # ── Context Switcher ──
    st.divider()
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
                
                # --- Persistent State Sync ---
                import json
                state_file = ".strata_state.json"
                
                # 1. Restore from file if session is empty
                if current_run_id is None:
                    try:
                        if os.path.exists(state_file):
                            with open(state_file, "r") as f:
                                saved = json.load(f)
                                saved_run_id = saved.get("active_run_id")
                                if saved_run_id in run_options.values():
                                    current_run_id = saved_run_id
                                    st.session_state["active_run_id"] = saved_run_id
                                    st.session_state["active_project_id"] = saved.get("active_project_id")
                    except Exception:
                        pass
                
                # 2. Always ensure file reflects the active session (handles updates from anywhere)
                try:
                    current_saved = {}
                    if os.path.exists(state_file):
                        with open(state_file, "r") as f:
                            current_saved = json.load(f)
                            
                    if current_saved.get("active_run_id") != current_run_id:
                        with open(state_file, "w") as f:
                            json.dump({
                                "active_run_id": current_run_id, 
                                "active_project_id": st.session_state.get("active_project_id")
                            }, f)
                except Exception:
                    pass
                # ------------------------

                run_keys = list(run_options.keys())
                
                current_idx = None
                if current_run_id is not None:
                    try:
                        current_idx = next(i for i, k in enumerate(run_keys) if run_options[k] == current_run_id)
                    except StopIteration:
                        current_idx = None
                
                selected_run_label = st.selectbox(
                    "Select Workspace / Run", 
                    run_keys, 
                    index=current_idx,
                    placeholder="Select Workspace..."
                )
                
                if selected_run_label:
                    selected_run_id = run_options[selected_run_label]
                    
                    # Always ensure project_id stays in sync with run_id
                    current_r = next((r for r in available_runs if r['id'] == selected_run_id), None)
                    if current_r and 'project_id' in current_r:
                        st.session_state["active_project_id"] = current_r['project_id']
                    else:
                        st.session_state["active_project_id"] = None

                    if st.session_state.get("active_run_id") != selected_run_id:
                        st.session_state["active_run_id"] = selected_run_id
                        st.rerun()
                else:
                    # Clear session state if selection is empty
                    if st.session_state.get("active_run_id") is not None:
                        st.session_state["active_run_id"] = None
                        st.session_state["active_project_id"] = None
                        st.rerun()
            else:
                st.selectbox("Select Workspace / Run", ["No active runs"], disabled=True)
    except requests.exceptions.RequestException:
        st.error("API Unreachable. Please check backend connection.")
        if st.button("Retry Connection"):
            st.rerun()
    except Exception as e:
        if e.__class__.__name__ == "RerunException":
            raise e
        st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # ── Page Navigations ──
    for section, section_pages in pages.items():
        is_expanded = (section == "Command Center")
        with st.expander(f"**{section}**", expanded=is_expanded):
            for page in section_pages:
                st.page_link(page, icon=page.icon)

all_pages = [p for sublist in pages.values() for p in sublist]
all_pages.append(_page_report_viewer)

pg = st.navigation(all_pages, position="hidden")
pg.run()

if st.session_state.get("show_user_guide", False):
    show_user_guide()
