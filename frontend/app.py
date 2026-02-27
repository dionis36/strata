import streamlit as st
import requests
import os

st.set_page_config(page_title="Strata - Phase 0", layout="wide")
st.title("Strata: System Status")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000/health")

try:
    res = requests.get(FASTAPI_URL, timeout=5)
    if res.status_code == 200:
        data = res.json()
        st.success(f"System Status: {data.get('status')}")
        st.info(f"Database: {data.get('database')}")
        st.markdown(f"**Version**: {data.get('version')}")
        st.markdown(f"**Timestamp**: {data.get('timestamp')}")
    else:
        st.error(f"API returned status {res.status_code}")
except requests.exceptions.RequestException as e:
    st.error(f"Failed to connect to API at {FASTAPI_URL}")
    st.error(str(e))
