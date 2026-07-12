import streamlit as st
import requests
import os

def show_run_comparison():
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    
    st.title("Run Comparison")
    st.markdown("##### Modernization Trajectory & Diff Analysis")
    st.markdown("---")
    
    project_id = st.session_state.get("active_project_id")
    if not project_id:
        st.info("Select a project or start a new analysis to view comparisons.")
        return
        
    # Fetch runs for the active project
    try:
        runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=5)
        if runs_res.status_code != 200:
            st.error("Failed to fetch runs.")
            return
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return
        
    all_runs = runs_res.json()
    # Filter runs for this project that are completed or similar
    valid_statuses = ['COMPLETED', 'ANALYSIS_COMPLETE', 'INTELLIGENCE_READY', 'INTELLIGENCE_FAILED', 'SYNTHESIZING_FINDINGS', 'SYNTHESIZING_SUMMARY', 'SYNTHESIZING_RECTOR']
    proj_runs = [r for r in all_runs if r.get("project_id") == project_id and r.get("status", "").upper() in valid_statuses]
    
    if len(proj_runs) < 2:
        st.info("At least 2 completed runs are required for comparison. Please run another scan on this project.")
        return
        
    # Sort runs chronologically (oldest first)
    proj_runs = sorted(proj_runs, key=lambda x: x.get("started_at", ""), reverse=False)
    
    # ── Section A: The Control Panel ──
    st.markdown("#### Select Runs for Comparison")
    col1, col2 = st.columns(2)
    
    run_options = {f"Run {r['id']} ({r.get('started_at', '')[:16]})": r for r in proj_runs}
    run_keys = list(run_options.keys())
    
    with col1:
        # Default Baseline to the second to last run if available, or first
        default_base_idx = max(0, len(run_keys) - 2)
        baseline_key = st.selectbox("Baseline Run", run_keys, index=default_base_idx)
        baseline_run = run_options[baseline_key]
        
    with col2:
        # Default Target to the latest run
        default_target_idx = len(run_keys) - 1
        target_key = st.selectbox("Target Run", run_keys, index=default_target_idx)
        target_run = run_options[target_key]
        
    st.markdown("---")
    
    if baseline_run['id'] == target_run['id']:
        st.warning("Please select two different runs to compare.")
        return
        
    # ── Section B: The Delta Grid ──
    st.markdown("### System Vitality Deltas")
    
    def get_run_metrics(run_data):
        return {
            "total_files": run_data.get("total_files") or 0,
            "total_loc": run_data.get("total_loc") or 0,
            "avg_complexity": run_data.get("avg_complexity") or 0.0,
            "total_classes": run_data.get("total_classes") or 0,
            "total_edges": run_data.get("total_edges") or 0,
            "risk_score": run_data.get("risk_score") or 0.0
        }
        
    base_metrics = get_run_metrics(baseline_run)
    target_metrics = get_run_metrics(target_run)
    
    def render_trajectory_metric(label, base_val, target_val, invert_color=False, is_pct=False):
        b_val = round(base_val, 2) if isinstance(base_val, float) else base_val
        t_val = round(target_val, 2) if isinstance(target_val, float) else target_val
        delta = t_val - b_val
        
        if delta == 0:
            color = "gray"
            sign = ""
        else:
            if invert_color:
                color = "#ff4b4b" if delta > 0 else "#21c354"
            else:
                color = "#21c354" if delta > 0 else "#ff4b4b"
            sign = "+" if delta > 0 else ""
            
        b_str = f"{b_val:,}" if isinstance(b_val, int) else str(b_val)
        t_str = f"{t_val:,}" if isinstance(t_val, int) else str(t_val)
        d_str = f"{delta:,}" if isinstance(delta, int) else f"{delta:.2f}"
        
        if is_pct:
            b_str += "%"
            t_str += "%"
            d_str += "%"
            
        st.markdown(f"""
        <div style="padding: 15px; border-radius: 8px; background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); margin-bottom: 10px;">
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 5px;">{label}</div>
            <div style="font-size: 1.2rem; font-weight: 600;">
                {b_str} <span style="opacity: 0.5;">➔</span> {t_str} 
                <span style="color: {color}; font-size: 1rem; margin-left: 8px;">[{sign}{d_str}]</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        render_trajectory_metric("Total Files", base_metrics["total_files"], target_metrics["total_files"])
        render_trajectory_metric("OOP Entities (Classes)", base_metrics["total_classes"], target_metrics["total_classes"])
    with kpi2:
        render_trajectory_metric("Lines of Code", base_metrics["total_loc"], target_metrics["total_loc"])
        render_trajectory_metric("Connectivity (Edges)", base_metrics["total_edges"], target_metrics["total_edges"], invert_color=True)
    with kpi3:
        render_trajectory_metric("Avg Complexity", base_metrics["avg_complexity"], target_metrics["avg_complexity"], invert_color=True)
        render_trajectory_metric("Modernization Readiness Score", base_metrics["risk_score"], target_metrics["risk_score"], is_pct=True)

    st.markdown("---")
    
    # ── Section C: Tabbed Deep Dive ──
    st.markdown("### Architectural Drift")
    
    @st.cache_data(ttl=60)
    def fetch_risk_data(rid):
        try:
            res = requests.get(f"{FASTAPI_URL}/security-risk/{rid}", timeout=10)
            return res.json() if res.status_code == 200 else {}
        except Exception:
            return {}

    with st.spinner("Fetching deep structural metrics for both runs..."):
        base_risk = fetch_risk_data(baseline_run['id'])
        target_risk = fetch_risk_data(target_run['id'])
        
    tab1, tab2 = st.tabs(["Structural Changes", "Risk Remediation"])
    
    with tab1:
        st.markdown("#### File-Level Complexity Shifts")
        st.caption("Files where Cyclomatic Complexity or Fan-Out increased or decreased between runs.")
        
        base_files = {f["File Name"]: f for f in base_risk.get("file_matrix", [])}
        target_files = {f["File Name"]: f for f in target_risk.get("file_matrix", [])}
        
        drift_data = []
        for fname, t_file in target_files.items():
            if fname in base_files:
                b_file = base_files[fname]
                cc_diff = t_file.get("Cyclomatic Complexity", 0) - b_file.get("Cyclomatic Complexity", 0)
                fo_diff = t_file.get("Fan-Out", 0) - b_file.get("Fan-Out", 0)
                
                if cc_diff != 0 or fo_diff != 0:
                    drift_data.append({
                        "File Name": fname,
                        "Base CC": b_file.get("Cyclomatic Complexity", 0),
                        "Target CC": t_file.get("Cyclomatic Complexity", 0),
                        "CC Delta": cc_diff,
                        "Base Fan-Out": b_file.get("Fan-Out", 0),
                        "Target Fan-Out": t_file.get("Fan-Out", 0),
                        "Fan-Out Delta": fo_diff
                    })
                    
        import pandas as pd
        if drift_data:
            df_drift = pd.DataFrame(drift_data)
            # Style the deltas
            def style_delta(val):
                if val > 0: return 'color: #ff4b4b' # Red for increased complexity
                if val < 0: return 'color: #21c354' # Green for decreased
                return ''
                
            st.dataframe(
                df_drift.style.applymap(style_delta, subset=['CC Delta', 'Fan-Out Delta']),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("No file-level complexity changes detected between these runs.", icon=":material/check_circle:")
            
    with tab2:
        st.markdown("#### Vulnerability & Rot Remediation")
        st.caption("New risks introduced or existing risks resolved.")
        
        # Compare Architectual Rot
        base_rot = {f"{r.get('File')}-{r.get('Defect Type')}" for r in base_risk.get("architectural_rot", [])}
        target_rot = {f"{r.get('File')}-{r.get('Defect Type')}" for r in target_risk.get("architectural_rot", [])}
        
        resolved_rot = base_rot - target_rot
        new_rot = target_rot - base_rot
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Resolved Blockers")
            if resolved_rot:
                for r in resolved_rot:
                    parts = r.split("-", 1)
                    st.markdown(f"- **{parts[1]}** fixed in `{parts[0]}`")
            else:
                st.info("No blockers resolved.")
                
        with c2:
            st.markdown("##### New Blockers Introduced")
            if new_rot:
                for r in new_rot:
                    parts = r.split("-", 1)
                    st.markdown(f"- **{parts[1]}** detected in `{parts[0]}`")
            else:
                st.success("No new blockers introduced.")
