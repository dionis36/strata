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
            
    synthesis_statuses = ["analysis_complete", "synthesizing_findings", "synthesizing_summary", "synthesizing_rector"]
    
    if run_status in synthesis_statuses:
        import time
        with st.status("Synthesizing System Intelligence...", expanded=True) as status:
            if run_status == "analysis_complete" or run_status == "synthesizing_findings":
                st.write("🤖 Synthesizing deep architectural findings...")
            elif run_status == "synthesizing_summary":
                st.write("✅ Architectural findings synthesized.")
                st.write("📝 Writing executive roadmap and summary...")
            elif run_status == "synthesizing_rector":
                st.write("✅ Executive summary complete.")
                st.write("⚙️ Generating targeted Rector.php refactoring rules...")
                
            st.write("*(This process spaces out API calls to respect rate limits. Please wait...)*")
            time.sleep(3)
        st.rerun()
    elif run_status == "analyzing":
        st.markdown(
            "<div style='padding:1rem;background-color:rgba(14, 165, 233, 0.1);border-left:4px solid #0ea5e9;border-radius:4px;color:#e2e8f0;'>"
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
            f"<div style='padding:1rem;background-color:rgba(239, 68, 68, 0.1);border-left:4px solid #ef4444;border-radius:4px;color:#e2e8f0;margin-bottom:1rem;'>"
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
    
    with st.form("export_bundle_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            export_pdf = st.checkbox("Master Intelligence Report (PDF)", value=True)
            export_docx = st.checkbox("Master Intelligence Report (DOCX)", value=True)
            export_html = st.checkbox("Master Navigatable HTML App", value=True)
            export_md = st.checkbox("Master Intelligence Report (.md)", value=False)
            export_csv = st.checkbox("Complete Risk Inventory (CSV)", value=True)
        with col_b:
            export_sarif = st.checkbox("SARIF Export", value=True)
            export_rector = st.checkbox("Rector Config", value=True)
            export_deptrac = st.checkbox("Deptrac Config", value=True)
            
        submit_bundle = st.form_submit_button("Generate Full Bundle (.zip)")
        
    if submit_bundle or st.session_state.get("zip_bundle_data") is not None:
        if submit_bundle:
            with st.spinner("Compiling Workspace Bundle..."):
                params = {
                    "html": export_html,
                    "md": export_md,
                    "csv": export_csv,
                    "sarif": export_sarif,
                    "rector": export_rector,
                    "deptrac": export_deptrac,
                    "pdf": export_pdf,
                    "docx": export_docx
                }
                res = requests.get(f"{FASTAPI_URL}/artifacts/bundle/{run_id}", params=params)
                if res.status_code == 200:
                    st.session_state["zip_bundle_data"] = res.content
                else:
                    st.error("Failed to generate Workspace Bundle.")
                    
        if st.session_state.get("zip_bundle_data") is not None:
            st.download_button(
                label="📥 Download strata_workspace.zip",
                data=st.session_state["zip_bundle_data"],
                file_name=f"strata_workspace_{run_id}.zip",
                mime="application/zip"
            )
                
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Human Artifacts")
        st.markdown("For planning, review, and communication.")
        
        # 1. Strategic Modernization Assessment
        st.markdown("#### 1. Master Intelligence Report")
        st.caption("A comprehensive document covering system scope, KPIs, architectural risks, and dependency intelligence.")
        
        format_options = {
            "PDF Document (.pdf)": "pdf",
            "Word Document (.docx)": "docx",
            "Web Page (.html)": "html",
            "Raw Markdown (.md)": "md"
        }
        selected_format_label = st.selectbox("Select Export Format", list(format_options.keys()))
        selected_format = format_options[selected_format_label]
        
        btn_compile = st.button("Generate Assessment")
        if btn_compile:
            with st.spinner(f"Generating {selected_format.upper()} Report..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/human/{run_id}?format={selected_format}")
                if res.status_code == 200:
                    st.session_state[f"cached_human_{selected_format}"] = res.content
                    st.success(f"{selected_format.upper()} report generated!")
                else:
                    st.error("Failed to generate report.")
        
        cached_human_key = f"cached_human_{selected_format}"
        if st.session_state.get(cached_human_key) is not None:
            mime_types = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "html": "text/html",
                "md": "text/markdown"
            }
            st.download_button(
                label=f"📥 Download Master_Intelligence_Report.{selected_format}",
                data=st.session_state[cached_human_key],
                file_name=f"Master_Intelligence_Report.{selected_format}",
                mime=mime_types[selected_format]
            )
                     
        st.markdown("---")
        
        # 2. Risk CSV
        st.markdown("#### 2. Risk Summary (CSV)")
        st.caption("A flat CSV of all component risk scores for Jira or Excel.")
        
        btn_csv = st.button("Generate CSV Export")
        if btn_csv:
            with st.spinner("Generating CSV..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/csv/{run_id}")
                if res.status_code == 200:
                    st.session_state["cached_csv_data"] = res.text
                    st.success("CSV generated!")
                else:
                    st.error("Failed to generate CSV.")
                    
        if st.session_state.get("cached_csv_data") is not None:
            st.download_button(
                label="📥 Download risks.csv",
                data=st.session_state["cached_csv_data"],
                file_name="risks.csv",
                mime="text/csv"
            )

    with col2:
        st.markdown("### Machine Artifacts")
        st.markdown("For tooling, automation, and integrations.")
        
        # 1. SARIF
        st.markdown("#### 1. SARIF Export")
        st.caption("OASIS standard JSON format for static analysis findings. Ready for GitHub Code Scanning.")
        
        btn_sarif = st.button("Generate SARIF JSON")
        if btn_sarif:
            with st.spinner("Generating SARIF..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/sarif/{run_id}")
                if res.status_code == 200:
                    st.session_state["cached_sarif_data"] = json.dumps(res.json(), indent=2)
                    st.success("SARIF generated!")
                else:
                    st.error("Failed to generate SARIF.")
                    
        if st.session_state.get("cached_sarif_data") is not None:
            st.download_button(
                label="📥 Download results.sarif",
                data=st.session_state["cached_sarif_data"],
                file_name="results.sarif",
                mime="application/json"
            )

        st.markdown("---")
        
        # 2. Rector Config
        st.markdown("#### 2. AI-Synthesized Rector Configuration")
        st.caption("Automated PHP refactoring rules synthesized by the LLM based on detected legacy patterns (`rector.php`).")
        
        btn_rector = st.button("Generate rector.php")
        if btn_rector:
            with st.spinner("Synthesizing custom Rector rules via AI..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/rector/{run_id}")
                if res.status_code == 200:
                    st.session_state["cached_rector_data"] = res.text
                    st.success("Rector Configuration Synthesized")
                else:
                    st.error("Failed to generate Rector config.")
                    
        if st.session_state.get("cached_rector_data") is not None:
            with st.expander("View AI-Generated rector.php", expanded=True):
                st.code(st.session_state["cached_rector_data"], language="php")
            st.download_button(
                label="📥 Download rector.php",
                data=st.session_state["cached_rector_data"],
                file_name="rector.php",
                mime="text/php"
            )
                    
        st.markdown("---")
        
        # 3. Deptrac Config
        st.markdown("#### 3. Deptrac Layer Config")
        st.caption("Architectural boundary enforcement rules based on inferred layers (`deptrac.yaml`).")
        
        btn_deptrac = st.button("Generate deptrac.yaml")
        if btn_deptrac:
            with st.spinner("Generating Deptrac rules..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/deptrac/{run_id}")
                if res.status_code == 200:
                    st.session_state["cached_deptrac_data"] = res.text
                    st.success("Deptrac generated!")
                else:
                    st.error("Failed to generate Deptrac config.")
                    
        if st.session_state.get("cached_deptrac_data") is not None:
            st.download_button(
                label="📥 Download deptrac.yaml",
                data=st.session_state["cached_deptrac_data"],
                file_name="deptrac.yaml",
                mime="application/yaml"
            )
                    
        st.markdown("---")
        
        # 4. Strict JSON
        st.markdown("#### 4. Machine Data Dump")
        st.caption("A comprehensive, strict JSON schema dump of all system nodes, edges, and scores.")
        
        btn_json = st.button("Generate Strict JSON")
        if btn_json:
            with st.spinner("Generating JSON Dump..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/json/{run_id}")
                if res.status_code == 200:
                    st.session_state["cached_json_data"] = json.dumps(res.json(), indent=2)
                    st.success("Strict JSON generated!")
                else:
                    st.error("Failed to generate JSON dump.")
        if st.session_state.get("cached_json_data") is not None:
            st.download_button(
                label="📥 Download system_dump.json",
                data=st.session_state["cached_json_data"],
                file_name="system_dump.json",
                mime="application/json"
            )

if __name__ == "__main__":
    show_artifact_center()
