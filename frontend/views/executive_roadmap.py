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

    tabs = st.tabs([
        "Modernization Roadmap", 
        "Architectural Summary (Graph)",
        "Deep Topology (DOT)", 
        "Export & Integration"
    ])

    with tabs[0]:
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

    with tabs[1]:
        st.markdown("#### High-Level System Context")
        st.caption("Directory-level dependency clustering for executive overview.")
        with st.spinner("Generating summary graph..."):
            try:
                res = requests.get(f"{FASTAPI_URL}/report/summary-graphviz/{run_id}", timeout=10)
                if res.status_code == 200:
                    dot = res.json().get("dot", "")
                    if dot:
                        st.graphviz_chart(dot, use_container_width=True)
                    else:
                        st.info("Not enough context detected to generate summary.")
                else:
                    st.error("Failed to generate summary graph.")
            except Exception as e:
                st.error(f"Connection error: {e}")

    with tabs[2]:
        st.markdown("#### Reachability Network (Sampled)")
        st.info("Full system reachability is generated for download. Rendering large graphs may affect performance.")
        if st.button("Generate Visualization"):
            with st.spinner("Calculating layout..."):
                try:
                    res = requests.get(f"{FASTAPI_URL}/report/graphviz/{run_id}", timeout=30)
                    if res.status_code == 200:
                        dot = res.json().get("dot", "")
                        st.graphviz_chart(dot, use_container_width=True)
                    else:
                        st.error("Failed to generate topology.")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    with tabs[3]:
        st.markdown("#### Enterprise Integration Artifacts")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🕸️ Graph Database")
            st.caption("Neo4j Cypher scripts for structural reachability.")
            if st.button("Generate Cypher"):
                try:
                    res = requests.get(f"{FASTAPI_URL}/report/neo4j/{run_id}", timeout=10)
                    cypher = res.json().get("cypher", "")
                    st.code(cypher[:1000] + "...", language="cypher")
                    st.download_button("Download Cypher", cypher, file_name=f"neo4j_{run_id}.cypher")
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            st.markdown("##### 🧠 AI Metadata")
            st.caption("Vector-ready JSON chunks for LLM interpretation.")
            if st.button("Generate AI Chunks"):
                try:
                    res = requests.get(f"{FASTAPI_URL}/report/ai-chunks/{run_id}", timeout=10)
                    chunks = res.json().get("chunks", [])
                    st.code(str(chunks)[:1000] + "...", language="json")
                    st.download_button("Download Chunks", str(chunks), file_name=f"ai_{run_id}.json")
                except Exception as e:
                    st.error(f"Error: {e}")

if __name__ == "__main__":
    show_executive_roadmap()
