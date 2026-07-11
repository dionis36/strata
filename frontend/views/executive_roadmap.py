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
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        from views import page_registry
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    st.markdown("#### Strategic Execution Roadmap")
    with st.spinner("Generating roadmap..."):
        try:
            res = requests.get(f"{FASTAPI_URL}/report/roadmap/{run_id}", timeout=10)
            if res.status_code == 200:
                roadmap_md = res.json().get("markdown", "")
                st.markdown(roadmap_md)
                st.download_button("Export Roadmap (MD)", roadmap_md, file_name=f"roadmap_{run_id}.md")
            else:
                st.error("Failed to generate roadmap.")
        except Exception as e:
            st.error(f"Connection error: {e}")

if __name__ == "__main__":
    show_executive_roadmap()
