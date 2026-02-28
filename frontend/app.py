import streamlit as st
import requests
import os

st.set_page_config(page_title="Strata - Phase 2", layout="wide")
st.title("Strata: Analysis Trigger")
st.markdown("Use this interface to natively trigger the Graph Extract & Metrics Engine.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# Health Check Sidebar
with st.sidebar:
    st.header("System Status")
    try:
        # Fallback to appending /health if FASTAPI_URL points to root
        health_url = FASTAPI_URL if FASTAPI_URL.endswith("/health") else f"{FASTAPI_URL}/health"
        res = requests.get(health_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"Status: {data.get('status')}")
            st.info(f"Database: {data.get('database')}")
            st.caption(f"Version: {data.get('version')}")
        else:
            st.error(f"API returned status {res.status_code}")
    except requests.exceptions.RequestException:
        st.error(f"Failed to connect to API")

# Main Content
st.header("Analyze Workspace")
project_path = st.text_input("Project Path (inside container)", value="/data")

if st.button("Run Minimal Analysis"):
    with st.spinner("Parsing PHP and building minimal graph..."):
        try:
            payload = {"project_path": project_path, "project_name": "demo_project"}
            
            # Ensure proper routing depending on FASTAPI_URL setup
            analyze_url = FASTAPI_URL.replace("/health", "") + "/analyze"
            
            response = requests.post(analyze_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                st.success("Analysis Complete!")
                st.info("Navigate to `Metrics Inspection` in the sidebar to view the structural calculations.")
                
                st.subheader("Structural Summary Card")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Run ID", result.get("run_id"))
                col2.metric("Files Evaluated", result.get("files"))
                col3.metric("Classes Identified (Nodes)", result.get("classes"))
                col4.metric("Method Calls (Edges)", result.get("edges"))
            else:
                st.error(f"Analysis failed: {response.json().get('detail')}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
