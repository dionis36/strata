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
        strategy_icons = {
            "REWRITE": "🔴", "STRANGLER FIG": "🟡", "EXTRACT (MICROSERVICE)": "🟢", "REPLATFORM": "🔵", "RETAIN / REHOST": "⚪"
        }
        strategy_raw = kpis.get("Most Common Strategy", "Unknown")
        icon = strategy_icons.get(strategy_raw, "")
        st.metric(
            "Primary Modernization Path", 
            f"{icon} {strategy_raw}",
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
        st.markdown("#### 🎯 Modernization ROI Matrix")
        # Extract numeric effort for plotting and humanizing
        df['EffortScore'] = df['Migration Effort'].apply(lambda x: int(x.split()[0]))
        
        def humanize_score(points):
            if points < 20: return "Small (Days)"
            elif points < 100: return "Medium (Weeks)"
            else: return "Large (Months)"
            
        df['Estimated Effort'] = df['EffortScore'].apply(humanize_score)
        
        # Add badges to strategies
        strategy_icons_full = {
            "REWRITE": "🔴 REWRITE", "STRANGLER FIG": "🟡 STRANGLER FIG", 
            "EXTRACT (MICROSERVICE)": "🟢 EXTRACT", "REPLATFORM": "🔵 REPLATFORM", 
            "RETAIN / REHOST": "⚪ RETAIN"
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

        st.markdown("#### 📋 Strategic Roadmap Details")
        st.dataframe(
            df[["Context", "Strategy", "Modernization ROI", "Estimated Effort", "Primary Blocker"]],
            hide_index=True,
            use_container_width=True
        )
        
        # Deep Dive rationale
        st.markdown("#### 🔍 Top 10 Strategic Justifications")
        st.caption("Detailed rationale for the most critical modules to prevent UI overload.")
        top_recommendations = recommendations[:10]
        for rec in top_recommendations:
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
