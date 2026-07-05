import streamlit as st
import requests
import os
import math

def show_dashboard():
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    
    st.title("Executive Dashboard")
    st.markdown("##### Strategic Modernization Command Center")
    st.markdown("---")

    # ── Context is managed globally in app.py ──
    project_id = st.session_state.get("active_project_id")
    dashboard_data = None
    if project_id:
        try:
            dash_res = requests.get(f"{FASTAPI_URL}/dashboard/{project_id}", timeout=5)
            if dash_res.status_code == 200:
                dashboard_data = dash_res.json()
        except Exception:
            pass

    if dashboard_data and dashboard_data.get("latest_run"):
        proj = dashboard_data["project"]
        run = dashboard_data["latest_run"]
        
        # ── Dashboard Top Row: Readiness & Strategy ───────────────────────────────
        col_gauge, col_strat = st.columns([1, 2])
        
        with col_gauge:
            score = run.get("risk_score", 0)
            st.markdown(f"""
                <div style="text-align: center; background: var(--secondary-background-color); padding: 20px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2);">
                    <h2 style="margin:0; color: var(--primary-color);">{round(score, 1)}%</h2>
                    <p style="color: var(--text-color); opacity: 0.8; font-size: 0.9rem;">Modernization Readiness</p>
                    <div style="background: rgba(128, 128, 128, 0.2); height: 8px; border-radius: 4px; margin-top: 10px;">
                        <div style="background: var(--primary-color); width: {score}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_strat:
            st.markdown(f"""
                <div style="background: var(--secondary-background-color); padding: 20px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); height: 100%;">
                    <h4 style="margin:0; color: var(--text-color);">{proj['name']}</h4>
                    <p style="color: var(--text-color); opacity: 0.7; font-size: 0.85rem; margin-bottom: 12px;">{proj['root_path']}</p>
                    <div style="display: flex; gap: 10px;">
                        <span style="background: #238636; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">ERA: {run['php_era']}</span>
                        <span style="background: #1f6feb; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">FW: {run['framework']}</span>
                        <span style="background: rgba(128, 128, 128, 0.2); color: var(--text-color); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">Last Scan: {run['completed_at'][:16]}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── KPI Bento Grid ───────────────────────────────────────────────────────
        # --- Primary KPI Row ---
        st.markdown("### System Vitality")
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        kpi1.metric("Total Files", f"{run.get('total_files', 0):,}")
        kpi2.metric("Lines of Code", f"{run.get('total_loc', 0):,}")
        kpi3.metric("Avg Complexity", round(run.get('avg_complexity', 0), 2))
        kpi4.metric("Total Classes", f"{run.get('total_classes', 0):,}")
        kpi5.metric("Connectivity", f"{run.get('total_edges', 0):,}")
        
        # cov = run.get('test_coverage')
        # cov_str = f"{round(cov * 100, 1)}%" if cov is not None else "N/A"
        # kpi6.metric("Test Coverage", cov_str, help="Overall Code Coverage from Clover/PHPUnit reports.")

        st.markdown("---")

    else:
        st.info("Select a project or start a new analysis to populate the dashboard.")

    # st.markdown("---")

    # ── Action Center ─────────────────────────────────────────────────────────────
    st.subheader("Action Center")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### New Project Analysis")
        
        tab_local, tab_zip, tab_git = st.tabs(["Local Directory", "Zip Upload", "Git Repository"])
        
        with tab_local:
            # ── Directory Discovery ──
            data_dir = os.environ.get("DATA_DIR", "/data")
            try:
                available_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
                available_dirs = sorted(available_dirs)
            except Exception:
                available_dirs = []
                
            if not available_dirs:
                st.warning("No directories found in /data. Please verify your volume mounts.")
                p_path = data_dir
                p_name = st.text_input("Project Name", value="Monolith_X", key="local_p_name")
            else:
                selected_dir = st.selectbox("Select Directory in /data", options=available_dirs)
                p_path = os.path.join(data_dir, selected_dir)
                p_name = st.text_input("Project Name", value=selected_dir.replace("-", "_").replace(".", "_"), key="local_p_name")
            
            if st.button("Initialize Deep Scan", use_container_width=True, key="btn_local_scan"):
                with st.spinner("Processing AST..."):
                    res = requests.post(f"{FASTAPI_URL}/analyze", json={"project_name": p_name, "project_path": p_path})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["active_run_id"] = data.get("run_id")
                        st.success("Analysis Complete!", icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.text}", icon=":material/error:")

        with tab_zip:
            st.markdown("Upload a compressed archive of your codebase.")
            p_name_zip = st.text_input("Project Name", value="Uploaded_Monolith", key="zip_p_name")
            uploaded_file = st.file_uploader("Upload Codebase", type=["zip"])
            
            if uploaded_file is not None:
                if st.button("Upload & Analyze", use_container_width=True, key="btn_zip_analyze"):
                    import time
                    status_placeholder = st.empty()
                    status_placeholder.info("Uploading file to engine...")
                    
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                    data_payload = {"project_name": p_name_zip}
                    
                    try:
                        res = requests.post(f"{FASTAPI_URL}/ingest/zip", files=files, data=data_payload)
                        if res.status_code == 200:
                            job_data = res.json()
                            job_id = job_data.get("job_id")
                            
                            # Polling loop
                            while True:
                                status_res = requests.get(f"{FASTAPI_URL}/ingest/status/{job_id}")
                                if status_res.status_code == 200:
                                    s_data = status_res.json()
                                    state = s_data.get("status")
                                    
                                    if state == "COMPLETE":
                                        status_placeholder.success("Analysis Complete! Loading dashboard...", icon=":material/check_circle:")
                                        runs_res = requests.get(f"{FASTAPI_URL}/runs")
                                        if runs_res.status_code == 200:
                                            runs = runs_res.json()
                                            if len(runs) > 0:
                                                st.session_state["active_run_id"] = runs[0]["id"]
                                        time.sleep(1)
                                        st.rerun()
                                    elif state == "FAILED":
                                        status_placeholder.error(f"Analysis Failed: {s_data.get('error_message')}", icon=":material/error:")
                                        break
                                    else:
                                        # Add some visual spin to the state
                                        status_placeholder.info(f"Status: {state} ... please wait", icon="⏳")
                                else:
                                    status_placeholder.error("Lost connection to status endpoint.")
                                    break
                                time.sleep(2)
                        else:
                            status_placeholder.error(f"Failed to start upload: {res.text}")
                    except Exception as e:
                        status_placeholder.error(f"Upload error: {e}")

        with tab_git:
            st.markdown("Clone a Git repository directly into the analysis engine.")
            repo_url = st.text_input("Repository URL", placeholder="https://github.com/dionis36/strata.git", key="git_url")
            c_branch, c_pname = st.columns(2)
            with c_branch:
                branch = st.text_input("Branch", value="main", key="git_branch")
            with c_pname:
                git_p_name = st.text_input("Project Name (Optional)", key="git_p_name")
                
            if st.button("Clone & Analyze", use_container_width=True, key="btn_git_analyze"):
                if not repo_url:
                    st.error("Please provide a Repository URL.")
                else:
                    import time
                    status_placeholder = st.empty()
                    status_placeholder.info("Initializing Git clone...")
                    
                    payload = {
                        "repo_url": repo_url,
                        "branch": branch,
                        "project_name": git_p_name if git_p_name else repo_url.rstrip("/").split("/")[-1].replace(".git", "")
                    }
                    
                    try:
                        res = requests.post(f"{FASTAPI_URL}/ingest/git", json=payload)
                        if res.status_code == 200:
                            job_data = res.json()
                            job_id = job_data.get("job_id")
                            
                            while True:
                                status_res = requests.get(f"{FASTAPI_URL}/ingest/status/{job_id}")
                                if status_res.status_code == 200:
                                    s_data = status_res.json()
                                    state = s_data.get("status")
                                    
                                    if state == "COMPLETE":
                                        status_placeholder.success("Analysis Complete! Loading dashboard...", icon=":material/check_circle:")
                                        runs_res = requests.get(f"{FASTAPI_URL}/runs")
                                        if runs_res.status_code == 200:
                                            runs = runs_res.json()
                                            if len(runs) > 0:
                                                st.session_state["active_run_id"] = runs[0]["id"]
                                        time.sleep(1)
                                        st.rerun()
                                    elif state == "FAILED":
                                        status_placeholder.error(f"Analysis Failed: {s_data.get('error_message')}", icon=":material/error:")
                                        break
                                    else:
                                        status_placeholder.info(f"Status: {state} ... please wait", icon="⏳")
                                else:
                                    status_placeholder.error("Lost connection to status endpoint.")
                                    break
                                time.sleep(2)
                        else:
                            status_placeholder.error(f"Failed to start clone: {res.text}")
                    except Exception as e:
                        status_placeholder.error(f"Git Ingestion error: {e}")

    with c2:
        if dashboard_data and dashboard_data.get("project"):
            st.markdown("#### Project Management")
            st.write(f"Active Root: `{dashboard_data['project']['root_path']}`")
            if st.button("Re-Scan", use_container_width=True):
                with st.spinner("Analyzing changes..."):
                    res = requests.post(f"{FASTAPI_URL}/analyze", json={
                        "project_name": dashboard_data['project']['name'], 
                        "project_path": dashboard_data['project']['root_path']
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["active_run_id"] = data.get("run_id")
                        st.success("Re-scan Successful!", icon=":material/check_circle:")
                        st.rerun()

if __name__ == "__main__":
    show_dashboard()
