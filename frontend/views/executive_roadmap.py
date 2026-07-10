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

    tabs = st.tabs([
        "Modernization Roadmap (Actionable)", 
        "Architectural Summary (Interactive)",
        "Deep Topology (DOT)", 
        "Export & Integration (2 Artifacts)"
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
        st.caption("Directory-level dependency clustering for executive overview. Interactive graph (zoom, pan, drag).")
        if st.button("Generate Visual Summary"):
            with st.spinner("Generating interactive network..."):
                try:
                    res = requests.get(f"{FASTAPI_URL}/report/summary-network/{run_id}", timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        nodes = data.get("nodes", [])
                        edges = data.get("edges", [])
                        
                        if nodes:
                            from pyvis.network import Network
                            import streamlit.components.v1 as components
                            
                            net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0", directed=True)
                            for node in nodes:
                                net.add_node(node, label=node, color="#38bdf8", size=20)
                            for edge in edges:
                                net.add_edge(edge["source"], edge["target"], color="#9ca3af")
                                
                            net.save_graph(f"/tmp/summary_net_{run_id}.html")
                            with open(f"/tmp/summary_net_{run_id}.html", "r", encoding="utf-8") as f:
                                html = f.read()
                            components.html(html, height=650)
                        else:
                            st.info("Not enough context detected to generate summary. The system may lack inter-module dependencies.")
                    else:
                        st.error("Failed to generate summary network.")
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
            st.markdown("##### Graph Database")
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
            st.markdown("##### AI Metadata")
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
