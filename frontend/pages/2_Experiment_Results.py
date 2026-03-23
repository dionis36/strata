import os
import streamlit as st

st.set_page_config(page_title="Evaluation Laboratory — Strata", layout="wide")
st.title("🔬 Architecture Evaluation Laboratory")
st.markdown("Automated experimentation suite executing Phase 6 ablation and sensitivity validation protocols natively over the intelligence engine.")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("▶ Run Experiment Suite", use_container_width=True):
        st.session_state["running_experiments"] = True
        
if st.session_state.get("running_experiments", False):
    with st.spinner("Isolating in-memory database & calculating structural ablations. Generating metrics..."):
        from evaluation.reports.report_generator import generate_full_evaluation_report
        try:
            # We hardcode Run #1 for standard demonstration
            report_data = generate_full_evaluation_report(1)
            st.session_state["eval_report"] = report_data
        except Exception as e:
            st.error(f"Experimental Pipeline Failure: {e}")
        finally:
            st.session_state["running_experiments"] = False

if "eval_report" in st.session_state:
    st.divider()
    report = st.session_state["eval_report"]
    
    st.markdown("### 1️⃣ Mathematical Classification Validation (Ablation)")
    st.caption("Validates how much predictive intelligence accuracy drops when internal heuristics (Behavior, Density) are disabled from the engine.")
    
    ablation = report.get("ablation_metrics", {})
    cols = st.columns(len(ablation))
    idx = 0
    for var, metrics in ablation.items():
        cols[idx].metric(
            f"{var.upper()}: F1 Score", 
            metrics.get("f1", 0), 
            delta=f"P: {metrics.get('precision')} | R: {metrics.get('recall')}",
            delta_color="off"
        )
        idx += 1
        
    if os.path.exists("evaluation/results/charts/ablation_f1.png"):
        st.image("evaluation/results/charts/ablation_f1.png", caption="F1 Score degradation under model ablation. Proves internal heuristics directly add intelligence value.")
    
    st.divider()
    
    st.markdown("### 2️⃣ Sensitivity & Consistency (Perturbation Bounds)")
    st.caption("Verifies that sweeping edge-case variable shifts in the mathematical core do not randomly shuffle extraction recommendations.")
    if os.path.exists("evaluation/results/charts/sensitivity_overlap.png"):
        st.image("evaluation/results/charts/sensitivity_overlap.png", caption="Top-5 Ranking Configuration Overlap. Shows rigid stability across different instantiation bounds.")
