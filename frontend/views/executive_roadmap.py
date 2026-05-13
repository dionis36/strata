import streamlit as st
import requests
import os

def show_executive_roadmap():
    st.title("Strategic Roadmap")
    st.markdown("### Executive Modernization Brief & Artifacts")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=60)
    def fetch_reports(rid):
        return {
            "roadmap": requests.get(f"{FASTAPI_URL}/report/roadmap/{rid}").json().get("markdown", ""),
            "dot": requests.get(f"{FASTAPI_URL}/report/graphviz/{rid}").json().get("dot", ""),
            "cypher": requests.get(f"{FASTAPI_URL}/report/neo4j/{rid}").json().get("cypher", ""),
            "ai": str(requests.get(f"{FASTAPI_URL}/report/ai-chunks/{rid}").json().get("chunks", []))
        }

    reports = fetch_reports(run_id)
    if not reports.get("roadmap"):
        st.error("Technical error generating strategic artifacts.")
        return

    tabs = st.tabs([
        "Modernization Roadmap", 
        "Network Topology (DOT)", 
        "Graph Database (Cypher)", 
        "AI Metadata (JSON)"
    ])

    with tabs[0]:
        st.markdown("#### Strategic Execution Roadmap")
        st.markdown(reports["roadmap"])
        st.download_button("Export Roadmap (MD)", reports["roadmap"], file_name=f"roadmap_{run_id}.md")

    with tabs[1]:
        st.markdown("#### Structural Topology Graph")
        if reports["dot"]:
            st.graphviz_chart(reports["dot"], use_container_width=True)
            st.download_button("Export Topology (DOT)", reports["dot"], file_name=f"graph_{run_id}.dot")

    with tabs[2]:
        st.markdown("#### Neo4j Integration Query")
        st.code(reports["cypher"][:2000] + "\n...", language="cypher")
        st.download_button("Export Cypher", reports["cypher"], file_name=f"neo4j_{run_id}.cypher")

    with tabs[3]:
        st.markdown("#### LLM Knowledge Chunks")
        st.code(reports["ai"][:2000] + "\n...", language="json")
        st.download_button("Export AI Metadata", reports["ai"], file_name=f"ai_chunks_{run_id}.json")

if __name__ == "__main__":
    show_executive_roadmap()
