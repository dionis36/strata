import streamlit as st
import requests
import os

st.set_page_config(page_title="Executive Roadmap", page_icon="🗺️", layout="wide")

st.title("🗺️ Executive Roadmap & Phase 5 Artifacts")
st.markdown("### Strategic Modernization Outputs")
st.write("Automatically generated industry-standard documentation, system context maps, and AI-ready metadata.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

try:
    runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=5)
    if runs_res.status_code == 200:
        available_runs = runs_res.json()
        run_options = {f"Run {r['id']} - {r['started_at'][:10]} ({r['total_files']} Files)": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
    else:
        run_options = {}
except Exception:
    run_options = {}

if not run_options:
    st.warning("⚠️ No completed runs found. Please return to the Home page and run an Intelligence Scan.")
    st.stop()

selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
run_id = run_options[selected_run_label]

@st.cache_data(ttl=60)
def fetch_reports(rid):
    return {
        "roadmap": requests.get(f"{FASTAPI_URL}/report/roadmap/{rid}").json().get("markdown", ""),
        "dot": requests.get(f"{FASTAPI_URL}/report/graphviz/{rid}").json().get("dot", ""),
        "cypher": requests.get(f"{FASTAPI_URL}/report/neo4j/{rid}").json().get("cypher", ""),
        "ai": str(requests.get(f"{FASTAPI_URL}/report/ai-chunks/{rid}").json().get("chunks", []))
    }

with st.spinner("Generating Enterprise Artifacts..."):
    reports = fetch_reports(run_id)

if not reports.get("roadmap"):
    st.error("Failed to generate artifacts. Ensure the backend is running and the scan succeeded.")
    st.stop()

# --- Tabbed Navigation ---
tab_roadmap, tab_graphviz, tab_neo4j, tab_ai = st.tabs([
    "🗺️ Executive Roadmap", 
    "🕸️ Graphviz (.dot)", 
    "🗄️ Neo4j Cypher", 
    "🤖 AI-Ready JSON"
])

with tab_roadmap:
    st.download_button("📥 Download Roadmap (Markdown)", reports["roadmap"], file_name=f"roadmap_{run_id}.md", type="primary")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(reports["roadmap"])

with tab_graphviz:
    st.markdown("### Graphviz Network Topology")
    st.write("Use this DOT file to render the exact reachability and context maps of the legacy monolith.")
    st.download_button("📥 Download .dot File", reports["dot"], file_name=f"graph_{run_id}.dot", type="primary")
    with st.expander("Preview Raw Graphviz Code", expanded=True):
        st.code(reports["dot"][:2000] + "\n... (truncated)", language="dot")

with tab_neo4j:
    st.markdown("### Neo4j Cypher Injection")
    st.write("Execute this Cypher query in your Neo4j instance to populate the Knowledge Graph engine.")
    st.download_button("📥 Download Cypher Query", reports["cypher"], file_name=f"neo4j_{run_id}.cypher", type="primary")
    with st.expander("Preview Cypher Logic", expanded=True):
        st.code(reports["cypher"][:2000] + "\n... (truncated)", language="cypher")

with tab_ai:
    st.markdown("### LLM Embeddings Payload")
    st.write("Embeddings-ready metadata for vector search and AI-orchestrated automated refactoring.")
    st.download_button("📥 Download AI Chunks (JSON)", reports["ai"], file_name=f"ai_chunks_{run_id}.json", type="primary")
    with st.expander("Preview Knowledge Chunks", expanded=True):
        st.code(reports["ai"][:2000] + "\n... (truncated)", language="json")
