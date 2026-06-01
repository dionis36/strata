import streamlit as st
import requests
import os
import math

def show_dashboard():
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    
    st.title("Executive Dashboard")
    st.markdown("##### Strategic Modernization Command Center")
    st.markdown("---")

    # ── Context & Project Management ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("##### Project Registry")
        try:
            # We should probably have a /projects endpoint, but for now we list runs and group by project_id
            # Actually, let's just get all runs and find unique projects
            runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=5)
            if runs_res.status_code == 200:
                all_runs = runs_res.json()
                unique_projects = {}
                for r in all_runs:
                    pid = r['project_id']
                    if pid not in unique_projects:
                        unique_projects[pid] = f"Project {pid}"
                
                if unique_projects:
                    selected_pid = st.selectbox("Select Active Project", options=list(unique_projects.keys()), 
                                             format_func=lambda x: unique_projects[x])
                    st.session_state["active_project_id"] = selected_pid
                else:
                    st.info("No projects found. Run a scan below.")
        except Exception:
            st.error("API Offline")

    # ── Data Fetching ─────────────────────────────────────────────────────────────
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
                <div style="text-align: center; background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d;">
                    <h2 style="margin:0; color: #58a6ff;">{round(score, 1)}%</h2>
                    <p style="color: #8b949e; font-size: 0.9rem;">Modernization Readiness</p>
                    <div style="background: #30363d; height: 8px; border-radius: 4px; margin-top: 10px;">
                        <div style="background: #58a6ff; width: {score}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_strat:
            st.markdown(f"""
                <div style="background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; height: 100%;">
                    <h4 style="margin:0;">{proj['name']}</h4>
                    <p style="color: #8b949e; font-size: 0.85rem; margin-bottom: 12px;">{proj['root_path']}</p>
                    <div style="display: flex; gap: 10px;">
                        <span style="background: #238636; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">ERA: {run['php_era']}</span>
                        <span style="background: #1f6feb; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">FW: {run['framework']}</span>
                        <span style="background: #30363d; color: #c9d1d9; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">Last Scan: {run['completed_at'][:16]}</span>
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
        
        cov = run.get('test_coverage')
        cov_str = f"{round(cov * 100, 1)}%" if cov is not None else "N/A"
        kpi6.metric("Test Coverage", cov_str, help="Overall Code Coverage from Clover/PHPUnit reports.")

        st.markdown("---")
        st.markdown("### Architectural Footprint")
        try:
            layer_res = requests.get(f"{FASTAPI_URL}/layer-analysis/{run['id']}", timeout=5)
            if layer_res.status_code == 200:
                l_data = layer_res.json()
                dirs = l_data.get("layer_1", {}).get("directories", {})
                
                models = 0
                controllers = 0
                jobs = 0
                schemas = 0
                views = 0
                vendors = 0
                
                for info in dirs.values():
                    for f in info.get("files", []):
                        role = f.get("role", "file") if isinstance(f, dict) else "file"
                        if role == "model": models += 1
                        elif role == "controller": controllers += 1
                        elif role == "job": jobs += 1
                        elif role == "schema": schemas += 1
                        elif role == "view": views += 1
                        elif role == "vendor": vendors += 1
                        
                contexts = l_data.get("layer_3", {}).get("bounded_contexts", [])
                site_variants = len([c for c in contexts if c["name"].startswith("Site:")])
                
                af1, af2, af3, af4, af5, af6, af7 = st.columns(7)
                af1.metric("📦 Models", models)
                af2.metric("🎛️ Controllers", controllers)
                af3.metric("🖥️ Views", views)
                af4.metric("⚙️ CLI Scripts", jobs)
                af5.metric("💾 Schemas", schemas)
                af6.metric("🧩 Libraries", vendors)
                af7.metric("🌍 Site Variants", site_variants)
        except Exception as e:
            st.warning(f"Could not load architectural footprint: {e}")

    else:
        st.info("Select a project or start a new analysis to populate the dashboard.")

    st.markdown("---")

    # ── Action Center ─────────────────────────────────────────────────────────────
    st.subheader("Action Center")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### New Project Analysis")
        
        # ── Directory Discovery ──
        data_dir = "/data"
        try:
            available_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
            available_dirs = sorted(available_dirs)
        except Exception:
            available_dirs = []
            
        if not available_dirs:
            st.warning("No directories found in /data. Please verify your volume mounts.")
            p_path = data_dir
            p_name = st.text_input("Project Name", value="Monolith_X")
        else:
            selected_dir = st.selectbox("Select Directory in /data", options=available_dirs)
            p_path = os.path.join(data_dir, selected_dir)
            # Default name to directory name, but allow override
            p_name = st.text_input("Project Name", value=selected_dir.replace("-", "_").replace(".", "_"))
        
        if st.button("Initialize Deep Scan", use_container_width=True):
            with st.spinner("Processing AST..."):
                res = requests.post(f"{FASTAPI_URL}/analyze", json={"project_name": p_name, "project_path": p_path})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["active_run_id"] = data.get("run_id")
                    st.success("Analysis Complete!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error(f"Failed: {res.text}", icon=":material/error:")

    with c2:
        if dashboard_data and dashboard_data.get("project"):
            st.markdown("#### Project Management")
            st.write(f"Active Root: `{dashboard_data['project']['root_path']}`")
            if st.button("Trigger Delta Re-Scan", use_container_width=True):
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
