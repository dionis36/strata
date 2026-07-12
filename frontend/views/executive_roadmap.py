import streamlit as st
import requests
import os

def show_executive_roadmap():
    st.title("Strategic Roadmap")
    st.markdown("##### Executive Modernization Brief & Artifacts")
    
    with st.expander("About the Strategic Roadmap", expanded=True):
        st.markdown("This module consolidates all intelligence gathered from the codebase into an actionable, step-by-step modernization plan. It also provides interactive architectural summaries, deep network reachability graphs, and raw structural artifacts ready for ingestion by external graph databases (Neo4j) or custom LLM pipelines.")
        
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis selected. Select a run from the **side panel** or start a new scan from the **Executive Dashboard**.")
        from views import page_registry
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    with st.spinner("Analyzing AST telemetry..."):
        try:
            res = requests.get(f"{FASTAPI_URL}/report/roadmap/{run_id}", timeout=10)
            if res.status_code == 200:
                data = res.json()
            else:
                st.error("Failed to fetch dynamic roadmap.")
                return
        except Exception as e:
            st.error(f"Connection error: {e}")
            return

    import pandas as pd

    st.markdown("---")
    
    # Phase 0
    phase_0 = data.get("phase_0")
    if phase_0:
        st.markdown("### Phase 0: Base Abstraction")
        st.warning("Architectural Blockers Detected: You cannot safely extract services until these shared memory and data constraints are decoupled.")
        col1, col2 = st.columns(2)
        with col1:
            if phase_0.get("has_global_state"):
                st.error("**Global State Detected**")
                st.caption("Implement a Dependency-Injected Session Manager/Context object to replace `$_SESSION` and `$GLOBALS`.")
            else:
                st.success("**Memory Isolated**")
        with col2:
            if phase_0.get("has_direct_sql"):
                st.error("**Direct Data Access Detected**")
                st.caption("Implement a Repository Pattern or DAO to abstract direct `mysqli_*` or raw SQL strings.")
            else:
                st.success("**Data Layer Abstracted**")
                
        stateful_files = phase_0.get("stateful_files", [])
        if stateful_files:
            st.markdown("##### Shared State Mutators")
            df = pd.DataFrame(stateful_files)
            st.dataframe(df, hide_index=True, use_container_width=True)
        st.markdown("---")
            
    # Phase 1
    phase_1 = data.get("phase_1")
    if phase_1:
        st.markdown("### Phase 1: Structural Decomposition")
        st.info("Break down the following massive monolithic classes (God Classes/Critical Risks) before defining new microservice boundaries.")
        god_classes = phase_1.get("god_classes", [])
        if god_classes:
            df = pd.DataFrame(god_classes)
            st.dataframe(df, hide_index=True, use_container_width=True)
        st.markdown("---")

    # Phase 2
    phase_2 = data.get("phase_2")
    if phase_2:
        st.markdown("### Phase 2: Extraction Sequence (Strangler Fig)")
        st.success("Mathematical extraction backlog based on Isolation Score (Lower score = Easier to extract).")
        domains = phase_2.get("domains", [])
        if domains:
            df = pd.DataFrame(domains)
            st.dataframe(df, hide_index=True, use_container_width=True)
        st.markdown("---")

if __name__ == "__main__":
    show_executive_roadmap()
