import streamlit as st
import os
import requests
import pandas as pd
import plotly.express as px

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
from views import page_registry
from views.severity import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW

def fetch_strategic_roadmap(run_id: int):
    try:
        res = requests.get(f"{FASTAPI_URL}/strategic-roadmap/{run_id}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to fetch roadmap: {e}")
    return None

@st.cache_data(ttl=60)
def fetch_ai_advisory(run_id: int):
    try:
        res = requests.get(f"{FASTAPI_URL}/advisory/ai/{run_id}", timeout=30)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def show_modernization_decision_engine():
    st.title("Modernization Decision Engine")
    st.markdown("##### Strategic advisory based on structural risk, domain coupling, and modernization ROI.")

    with st.expander("Decision Engine Blueprint Key", expanded=True):
        st.markdown("""
        ### Understanding the Modernization ROI Graph
        The scatter plot visualizes the cost-benefit analysis of modernizing each architectural module.
        * **X-Axis (Migration Effort)**: How difficult the module is to modernize (measured in Logic Points). Modules further to the right are highly complex, deeply coupled, and will take months to untangle.
        * **Y-Axis (Modernization ROI)**: The Return on Investment (0-100 score). A high ROI means the module carries high structural risk or high business value, meaning modernizing it provides immense immediate benefit.
        * **Bubble Size & Color**: Represents the size of the module and its assigned modernization strategy.
        * **The Goal**: Target the **top-left quadrant** first. These are "Quick Wins"-high ROI but relatively low effort. Avoid the bottom-right quadrant (low ROI, massive effort).
        
        ### The 5 Modernization Strategies
        The engine assigns one of five industry-standard strategies based on the module's structural signature:
        * **EXTRACT (Microservice)**: The module is highly cohesive and decoupled. It is safe to rip out of the monolith and deploy as an independent microservice immediately.
        * **STRANGLER FIG**: The module is valuable but heavily entangled. Do not rewrite it all at once. Instead, wrap it in an API facade and slowly strangle the legacy code piece-by-piece over time.
        * **REWRITE**: The module suffers from critical logical rot. It is so structurally compromised (low maintainability, extreme complexity) that untangling it is mathematically more expensive than throwing it away and rewriting from scratch.
        * **REPLATFORM**: The module works but relies heavily on deprecated or dangerous infrastructure (e.g., legacy database calls, raw execution sinks). Move it to a modern framework without fundamentally changing its business logic.
        * **RETAIN / REHOST**: The module is stable, works fine, and has low risk. Leave it in the monolith for now so engineering resources can focus on the high-risk targets.
        """)
    st.markdown("---")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    data = fetch_strategic_roadmap(run_id)
    if not data:
        st.warning("No strategic data available for this run.")
        return

    kpis = data.get("kpis", {})
    
    # Humanize Effort Points
    raw_effort = kpis.get("Overall Migration Effort", "0 Points")
    try:
        effort_points = int(raw_effort.split()[0])
        if effort_points < 100: human_effort = "Small (Days)"
        elif effort_points < 500: human_effort = "Medium (Weeks)"
        else: human_effort = "Large (Months)"
    except:
        human_effort = raw_effort
        effort_points = 0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Estimated Migration Effort", 
            human_effort,
            delta=f"{effort_points} Raw Logic Points",
            delta_color="off",
            help="An estimate of time required based on code complexity and size."
        )
    with col2:
        strategy_raw = kpis.get("Most Common Strategy", "Unknown")
        st.metric(
            "Primary Modernization Path", 
            strategy_raw,
            help="The most frequent recommendation. e.g., 'Extract' means moving clean isolated code to a microservice."
        )
    with col3:
        st.metric(
            "Quick Wins (High ROI)", 
            kpis.get("High Value Targets", 0),
            help="Modules where the benefit of modernization heavily outweighs the effort. Score > 70."
        )

    st.markdown("---")

    recommendations = data.get("recommendations", [])
    if recommendations:
        df = pd.DataFrame(recommendations)
        
        # Visualize ROI vs Effort
        st.markdown("#### Modernization ROI Matrix")
        # Extract numeric effort for plotting and humanizing
        df['EffortScore'] = df['Migration Effort'].apply(lambda x: int(x.split()[0]))
        
        def humanize_score(points):
            if points < 20: return "Small (Days)"
            elif points < 100: return "Medium (Weeks)"
            else: return "Large (Months)"
            
        df['Estimated Effort'] = df['EffortScore'].apply(humanize_score)
        
        # Add badges to strategies
        strategy_icons_full = {
            "REWRITE": "REWRITE", "STRANGLER FIG": "STRANGLER FIG", 
            "EXTRACT (MICROSERVICE)": "EXTRACT", "REPLATFORM": "REPLATFORM", 
            "RETAIN / REHOST": "RETAIN"
        }
        df['Strategy'] = df['Recommended Strategy'].apply(lambda x: strategy_icons_full.get(x, x))
        
        fig = px.scatter(
            df, 
            x="EffortScore", 
            y="Modernization ROI",
            text="Context",
            color="Recommended Strategy",
            size="EffortScore",
            hover_data=["Rationale", "Primary Blocker"],
            labels={"EffortScore": "Migration Effort (Points)", "Modernization ROI": "ROI Score (0-100)"},
            template="plotly_dark",
            color_discrete_map={
                "REWRITE": "#f85149",
                "STRANGLER FIG": "#d29922",
                "EXTRACT (MICROSERVICE)": "#3fb950",
                "REPLATFORM": "#58a6ff",
                "RETAIN / REHOST": "#8b949e"
            }
        )
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Strategic Roadmap Details")
        st.dataframe(
            df[["Context", "Strategy", "Modernization ROI", "Estimated Effort", "Primary Blocker"]],
            hide_index=True,
            use_container_width=True
        )
        
        # Deep Dive rationale
        st.markdown("#### Top 10 Strategic Justifications")
        st.caption("Detailed rationale for the most critical modules to prevent UI overload.")
        top_recommendations = recommendations[:10]
        for rec in top_recommendations:
            with st.expander(f"Strategy for: {rec['Context']}"):
                st.markdown(f"**RECOMMENDED**: `{rec['Recommended Strategy']}`")
                st.markdown(f"**RATIONALE**: {rec['Rationale']}")
                st.markdown(f"**PRIMARY BLOCKER**: {rec['Primary Blocker']}")
                
                # Behavioral Insight Protocol (D1 Strategy)
                st.info("##### Advisory Interpretation", icon=":material/info:")
                st.markdown(
                    f"The {rec['Context']} module has been assigned a **{rec['Recommended Strategy']}** strategy because its "
                    f"structural profile shows {rec['Primary Blocker']} as the dominant constraint. "
                    "This is a data-driven assignment based on industry benchmarks for legacy PHP decomposition."
                )
    else:
        st.info("The engine is still processing strategy profiles. Please check back shortly.")

    # --- Phase 10: AI Narratives & Mermaid Diagrams ---
    st.markdown("---")
    st.markdown("### Deep AI Architectural Intelligence")
    st.caption("AI-synthesized modernization paths directly targeting God Classes and structural tight coupling.")
    
    ai_data = fetch_ai_advisory(run_id)
    if ai_data and ai_data.get("findings"):
        findings = ai_data["findings"]
        for f in findings:
            p = str(f.get("priority", "")).upper()
            priority_color = SEVERITY_CRITICAL if p == SEVERITY_CRITICAL else SEVERITY_HIGH if p == SEVERITY_HIGH else SEVERITY_MEDIUM
            
            with st.expander(f"[{priority_color}] {f.get('observation', 'Architecture Finding')}"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("##### The Assessment")
                    st.markdown(f.get('impact', ''))
                    
                    st.markdown("##### Executive Recommendation")
                    st.success(f.get('recommended_action', ''), icon=":material/check_circle:")
                    
                    if "Playbook Standard" in f.get('category', ''):
                        st.info("**Playbook Standard Enforced**: This recommendation follows strict, deterministic modernization rules.", icon=":material/menu_book:")
                    else:
                        st.caption(f"**Confidence**: {f.get('confidence', 'N/A')} | **Category**: {f.get('category', 'General')}")
                
                with c2:
                    diagram = f.get('mermaid_diagram')
                    if diagram:
                        st.markdown("##### Extraction Blueprint")
                        # We use standard code block which Streamlit automatically renders as Mermaid if Streamlit >= 1.35
                        st.markdown(f"```mermaid\n{diagram}\n```")
                    else:
                        st.markdown("*No diagram available for this finding.*")
    else:
        st.info("Waiting for AI analysis to complete...")

if __name__ == "__main__":
    show_modernization_decision_engine()
