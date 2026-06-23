import streamlit as st
import requests
import os
import json

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def show_artifact_center():
    st.title("Artifact Center")
    st.markdown("##### Download Generated Machine & Human Artifacts")
    
    with st.expander("About the Artifact Center", expanded=True):
        st.markdown("""
        The Artifact Center is your single source of truth for all exports. 
        - **Human Artifacts** are intended for sharing with project managers, stakeholders, and presentation platforms.
        - **Machine Artifacts** are strictly schematized configurations meant for CI/CD pipelines, LLMs, and automated refactoring tools (like Rector and Deptrac).
        """)
        
    st.markdown("---")
    
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    # Check Run Status
    runs_res = requests.get(f"{FASTAPI_URL}/runs")
    run_status = "unknown"
    if runs_res.status_code == 200:
        runs = runs_res.json()
        current_run = next((r for r in runs if r["id"] == run_id), None)
        if current_run:
            run_status = current_run.get("status", "unknown")
            
    synthesis_statuses = ["synthesizing_findings", "synthesizing_summary", "synthesizing_rector"]
    
    if run_status in synthesis_statuses:
        import time
        with st.status("Synthesizing System Intelligence...", expanded=True) as status:
            if run_status == "synthesizing_findings":
                st.write("🤖 Synthesizing deep architectural findings...")
            elif run_status == "synthesizing_summary":
                st.write("📝 Writing executive roadmap and summary...")
            elif run_status == "synthesizing_rector":
                st.write("⚙️ Generating targeted Rector.php refactoring rules...")
                
            st.write("*(This process spaces out API calls to respect rate limits. Please wait...)*")
            time.sleep(3)
        st.rerun()
    elif run_status == "analysis_complete":
        st.markdown(
            "<div style='padding:1rem;background-color:rgba(16, 185, 129, 0.1);border-left:4px solid #10b981;border-radius:4px;color:var(--text-color);margin-bottom:1.5rem;'>"
            "<strong>Source Code Scan Complete!</strong> Auto-starting the AI engine for executive reports..."
            "</div>", 
            unsafe_allow_html=True
        )
        with st.spinner("Initializing AI Synthesis..."):
            requests.post(f"{FASTAPI_URL}/runs/{run_id}/retry_intelligence")
            st.rerun()
        st.stop()
    elif run_status == "analyzing":
        st.markdown(
            "<div style='padding:1rem;background-color:rgba(14, 165, 233, 0.1);border-left:4px solid #0ea5e9;border-radius:4px;color:var(--text-color);'>"
            "<strong>Core analysis is currently running. Please wait for completion.</strong>"
            "</div>", 
            unsafe_allow_html=True
        )
        st.write("")
        if st.button("Refresh Status"):
            st.rerun()
        st.stop()
    elif run_status == "intelligence_failed":
        err_msg = current_run.get("error_message") if current_run else None
        err_detail = f"<div style='margin-top:0.5rem;font-family:monospace;font-size:0.85rem;color:#f87171;word-break:break-all;'><strong>Error detail:</strong> {err_msg}</div>" if err_msg else ""
        st.markdown(
            f"<div style='padding:1rem;background-color:rgba(239, 68, 68, 0.1);border-left:4px solid #ef4444;border-radius:4px;color:var(--text-color);margin-bottom:1rem;'>"
            f"<strong>AI Intelligence Synthesis Failed.</strong> The AI engine encountered an issue. Base metrics are available, but deep synthesis failed.{err_detail}"
            f"</div>", 
            unsafe_allow_html=True
        )
        if st.button("Retry AI Synthesis", type="primary"):
            res = requests.post(f"{FASTAPI_URL}/runs/{run_id}/retry_intelligence")
            if res.status_code == 200:
                st.success("Retry queued! Processing in background...")
                st.rerun()
            else:
                st.error("Failed to queue retry.")


    st.markdown("### Workspace Export Bundle")
    st.caption("Download all selected artifacts packaged in a structured ZIP archive.")
    
    if st.button("Sync with Database", help="Clear cache and fetch latest artifacts if you used the CLI Override tool"):
        st.cache_data.clear()
        st.rerun()
    
    col_a, col_b = st.columns(2)
    with col_a:
        export_md = st.checkbox("Strategic Modernization Blueprint (.md)", value=True)
    with col_b:
        export_sarif = st.checkbox("SARIF Export", value=True)
    @st.cache_data(show_spinner=False)
    def fetch_bundle_cached(run_id_val, md_val, sarif_val):
        params = {"html": False, "md": md_val, "csv": False, "sarif": sarif_val, "rector": False, "deptrac": False, "pdf": False, "docx": False}
        res = requests.get(f"{FASTAPI_URL}/artifacts/bundle/{run_id_val}", params=params)
        return res.content if res.status_code == 200 else None

    with st.spinner("Compiling Workspace Bundle..."):
        bundle_content = fetch_bundle_cached(run_id, export_md, export_sarif)
        
    if bundle_content:
        st.download_button(
            label="📥 Download strata_workspace.zip",
            data=bundle_content,
            file_name=f"strata_workspace_{run_id}.zip",
            mime="application/zip"
        )
    else:
        st.error("Failed to generate Workspace Bundle.")
                
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Human Artifacts")
        st.markdown("For planning, review, and communication.")
        
        # 1. Strategic Modernization Assessment
        st.markdown("#### 1. Strategic Modernization Blueprint")
        st.caption("A comprehensive document covering system scope, KPIs, architectural risks, and dependency intelligence.")
        
        @st.cache_data(show_spinner=False)
        def fetch_human_cached(run_id_val):
            res = requests.get(f"{FASTAPI_URL}/artifacts/human/{run_id_val}?format=md")
            return res.content if res.status_code == 200 else None

        with st.spinner("Preparing MD Report..."):
            md_content = fetch_human_cached(run_id)
        
        if md_content:
            st.download_button(
                label="📥 Download Strategic_Modernization_Blueprint.md",
                data=md_content,
                file_name="Strategic_Modernization_Blueprint.md",
                mime="text/markdown"
            )
        else:
            st.error("Failed to load report.")

    with col2:
        st.markdown("### Machine Artifacts")
        st.markdown("For tooling, automation, and integrations.")
        
        # 1. SARIF
        st.markdown("#### 1. SARIF Export")
        st.caption("OASIS standard JSON format for static analysis findings. Ready for GitHub Code Scanning.")
        
        @st.cache_data(show_spinner=False)
        def fetch_sarif_cached(run_id_val):
            res = requests.get(f"{FASTAPI_URL}/artifacts/sarif/{run_id_val}")
            return json.dumps(res.json(), indent=2) if res.status_code == 200 else None

        with st.spinner("Preparing SARIF Export..."):
            sarif_content = fetch_sarif_cached(run_id)
            
        if sarif_content:
            st.download_button(
                label="📥 Download results.sarif",
                data=sarif_content,
                file_name="results.sarif",
                mime="application/json"
            )
        else:
            st.error("Failed to load SARIF.")



if __name__ == "__main__":
    show_artifact_center()
