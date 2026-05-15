import streamlit as st
import os
import requests
import pandas as pd
import plotly.express as px

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def fetch_strategic_roadmap(run_id: int):
    try:
        res = requests.get(f"{FASTAPI_URL}/strategic-roadmap/{run_id}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to fetch roadmap: {e}")
    return None

def show_modernization_decision_engine():
    st.markdown("## 🧠 Modernization Decision Engine")
    st.caption("Strategic advisory based on structural risk, domain coupling, and modernization ROI.")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("Please select a valid analysis run in the sidebar.")
        return

    data = fetch_strategic_roadmap(run_id)
    if not data:
        st.warning("No strategic data available for this run.")
        return

    kpis = data.get("kpis", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Migration Effort", kpis.get("Overall Migration Effort", "0 Points"))
    with col2:
        st.metric("Recommended Path", kpis.get("Most Common Strategy", "Unknown"))
    with col3:
        st.metric("High-ROI Targets", kpis.get("High Value Targets", 0))

    st.markdown("---")

    recommendations = data.get("recommendations", [])
    if recommendations:
        df = pd.DataFrame(recommendations)
        
        # Visualize ROI vs Effort
        st.markdown("#### 🎯 Modernization ROI Matrix")
        # Extract numeric effort for plotting
        df['EffortScore'] = df['Migration Effort'].apply(lambda x: int(x.split()[0]))
        
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

        st.markdown("#### 📋 Strategic Roadmap Details")
        st.dataframe(
            df[["Context", "Recommended Strategy", "Modernization ROI", "Migration Effort", "Primary Blocker"]],
            hide_index=True,
            use_container_width=True
        )
        
        # Deep Dive rationale
        st.markdown("#### 🔍 Strategic Justification")
        for rec in recommendations:
            with st.expander(f"Strategy for: {rec['Context']}"):
                st.markdown(f"**RECOMMENDED**: `{rec['Recommended Strategy']}`")
                st.markdown(f"**RATIONALE**: {rec['Rationale']}")
                st.markdown(f"**PRIMARY BLOCKER**: {rec['Primary Blocker']}")
                
                # Behavioral Insight Protocol (D1 Strategy)
                st.info("##### 🧐 Advisory Interpretation")
                st.markdown(
                    f"The {rec['Context']} module has been assigned a **{rec['Recommended Strategy']}** strategy because its "
                    f"structural profile shows {rec['Primary Blocker']} as the dominant constraint. "
                    "This is a data-driven assignment based on industry benchmarks for legacy PHP decomposition."
                )
    else:
        st.info("The engine is still processing strategy profiles. Please check back shortly.")

if __name__ == "__main__":
    show_modernization_decision_engine()
