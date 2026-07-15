import streamlit as st
import requests
import os
import pandas as pd

PHASE_CONTEXTS = {
    0: "Before dismantling a monolithic architecture, a reliable safety net is non-negotiable. This phase focuses on identifying the most complex, highly coupled components that completely lack test coverage. Modifying these 'ticking time bombs' without tests guarantees regression failures. The metric Weighted Method Count (WMC) identifies files where test instrumentation must begin immediately.",
    1: "Monoliths often entangle database queries directly within UI templates or route handlers (known as 'Fat Views'). This violates the single responsibility principle and makes API-driven microservices impossible. This phase prioritizes extracting data-access logic from presentation layers to create clean, decoupled boundary interfaces.",
    2: "Microservices require strict state isolation. If multiple services write to the same database tables or share global memory (`$GLOBALS`, `$_SESSION`), they are still architecturally coupled. This phase targets components with high shared table pressure and global mutators to prepare the data layer for decomposition.",
    3: "God classes are massive, uncohesive files that control too much of the system's behavior. Their blast radius is enormous, meaning a change in one domain often breaks another. We must decompose these structural bottlenecks into smaller, single-purpose services before attempting to physically extract domains.",
    4: "With the safety net in place and chokepoints dismantled, we can begin the Strangler Fig pattern. This phase uses our mathematical 'Isolation Score' (a ratio of external dependencies to internal cohesion) to rank Bounded Contexts. Modules with the lowest isolation scores are the easiest and safest to extract first."
}

def style_dataframe(df: pd.DataFrame, phase_id: int):
    """Applies custom formatting to dataframes based on phase."""
    if df.empty:
         return df
         
    styled = df.style
    
    if phase_id == 1 and "entanglement" in df.columns:
         try:
             # Convert the string percentage (e.g. '15.5%') into a float directly in the column
             df["entanglement"] = df["entanglement"].astype(str).str.rstrip('%').astype(float)
             # Format it back to look like a percentage
             styled = styled.format({"entanglement": "{:.1f}%"})
         except:
             pass
         
    return styled

def show_executive_roadmap():
    st.title("Strategic Roadmap")
    st.markdown("##### The 5-Phase Deterministic Modernization Engine")
    
    with st.expander("About the Strategic Roadmap", expanded=True):
         st.markdown("""
         **Deterministic Modernization Pipeline**
         This roadmap is not a generic checklist. It is a mathematically derived pipeline that calculates exactly which files to rewrite first based on their blast radius, cyclomatic complexity, and structural coupling. 
         
         The AI executive rationale enriches this raw data to provide board-level context without dictating the engineering steps.
         """)

    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis selected. Select a run from the side panel or dashboard.")
        return

    with st.spinner("Compiling deterministic roadmap sequence..."):
        try:
            res = requests.get(f"{FASTAPI_URL}/report/roadmap/{run_id}", timeout=10)
            if res.status_code == 200:
                data = res.json()
            else:
                st.error("Failed to fetch roadmap.")
                return
        except Exception as e:
            st.error(f"Connection error: {e}")
            return

    phases = data.get("phases", [])
    if not phases:
        st.info("No roadmap data available for this run.")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    for phase in phases:
        pid = phase.get('phase_id', 0)
        
        # Header and Rationale
        st.markdown(f"### {phase.get('title')}")
        st.markdown(f"<div style='font-size:0.95em; color:var(--text-color); opacity:0.8; margin-bottom:15px; border-left: 4px solid var(--primary-color); padding-left: 10px;'>{PHASE_CONTEXTS.get(pid, '')}</div>", unsafe_allow_html=True)
        
        summary = phase.get('executive_summary', '')
        if summary:
             st.info(f"**Executive Rationale:** {summary}")
            
        status = phase.get('status', 'ACTION_REQUIRED')
        if status == 'PASSED':
            st.success("**PHASE CLEARED:** No modernization blockers detected.")
        else:
            st.warning("**ACTION REQUIRED:** Architectural blockers detected. See prioritized backlog below.")
            
            tables = phase.get('evidence_tables', {})
            for table_name, table_data in tables.items():
                if isinstance(table_data, list) and table_data:
                    title = table_name.replace('_', ' ').title()
                    st.markdown(f"##### {title} Backlog")
                    df = pd.DataFrame(table_data)
                    
                    st.dataframe(
                         style_dataframe(df, pid),
                         hide_index=True, 
                         use_container_width=True
                    )
                elif isinstance(table_data, (int, float, str)):
                     st.metric(label=table_name.replace('_', ' ').title(), value=table_data)
        
        st.markdown("<hr style='margin: 40px 0;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    show_executive_roadmap()
