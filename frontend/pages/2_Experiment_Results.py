import streamlit as st
import os

st.set_page_config(page_title="Strata - Experiment Results", layout="wide")
st.title("Validation & Experiment Harness")
st.markdown("This interface will be populated in Phase 3 or later to display experimental sensitivity results.")

st.warning("⚠️ Experiment Engine offline. Awaiting downstream metric sensitivity features.")

st.markdown("### Anticipated Experiment Summaries")

col1, col2 = st.columns(2)

with col1:
    st.info("**Weight Sensitivity**")
    st.metric("Spearman Correlation", "N/A", delta=None)

with col2:
    st.info("**Edge Perturbation (5%)**")
    st.metric("Avg Rank Shift", "N/A", delta=None)
    st.metric("Max Rank Shift", "N/A", delta=None)

st.markdown("---")
st.info("**Node Removal Impact**")
st.code("""
Largest SCC Before: N/A
Largest SCC After: N/A
Impact Delta: N/A
""")
