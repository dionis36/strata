import streamlit as st
import requests
import os
import json

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def show_artifact_center():
    st.title("Artifact Center")
    st.markdown("##### Download Generated Machine & Human Artifacts")
    
    with st.expander("💡 About the Artifact Center", expanded=True):
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

    st.markdown("### 📦 Workspace Export Bundle")
    st.caption("Download all selected artifacts packaged in a structured ZIP archive.")
    
    with st.form("export_bundle_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            export_html = st.checkbox("Executive HTML Report", value=True)
            export_md = st.checkbox("Technical Assessment (MD)", value=True)
            export_csv = st.checkbox("Risk Summary (CSV)", value=True)
        with col_b:
            export_sarif = st.checkbox("SARIF Export", value=True)
            export_rector = st.checkbox("Rector Config", value=True)
            export_deptrac = st.checkbox("Deptrac Config", value=True)
            
        submit_bundle = st.form_submit_button("Generate Full Bundle (.zip)")
        
    if submit_bundle:
        with st.spinner("Compiling Workspace Bundle..."):
            params = {
                "html": export_html,
                "md": export_md,
                "csv": export_csv,
                "sarif": export_sarif,
                "rector": export_rector,
                "deptrac": export_deptrac
            }
            res = requests.get(f"{FASTAPI_URL}/artifacts/bundle/{run_id}", params=params)
            if res.status_code == 200:
                st.download_button(
                    label="⬇️ Download strata_workspace.zip",
                    data=res.content,
                    file_name=f"strata_workspace_{run_id}.zip",
                    mime="application/zip"
                )
            else:
                st.error("Failed to generate Workspace Bundle.")
                
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👨‍💼 Human Artifacts")
        st.markdown("For planning, review, and communication.")
        
        # 1. HTML Report
        st.markdown("#### 1. Executive HTML Report")
        st.caption("A standalone HTML document summarizing modernization readiness, KPIs, and top risks.")
        if st.button("Generate HTML Report"):
            with st.spinner("Generating Report..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/report/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download executive_report.html",
                        data=res.text,
                        file_name="executive_report.html",
                        mime="text/html"
                    )
                else:
                    st.error("Failed to generate report.")
                    
        st.markdown("---")
        
        # 2. Technical Assessment Report
        st.markdown("#### 2. Technical Assessment Report")
        st.caption("A markdown document outlining the phased refactoring approach, modules, and findings.")
        if st.button("Generate Technical Report (MD)"):
            with st.spinner("Generating Report..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/technical/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download technical_assessment.md",
                        data=res.text,
                        file_name="technical_assessment.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("Failed to generate report.")
                    
        st.markdown("---")
        
        # 3. Risk CSV
        st.markdown("#### 3. Risk Summary (CSV)")
        st.caption("A flat CSV of all component risk scores for Jira or Excel.")
        if st.button("Generate CSV Export"):
            with st.spinner("Generating CSV..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/csv/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download risks.csv",
                        data=res.text,
                        file_name="risks.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Failed to generate CSV.")

    with col2:
        st.markdown("### 🤖 Machine Artifacts")
        st.markdown("For tooling, automation, and integrations.")
        
        # 1. SARIF
        st.markdown("#### 1. SARIF Export")
        st.caption("OASIS standard JSON format for static analysis findings. Ready for GitHub Code Scanning.")
        if st.button("Generate SARIF JSON"):
            with st.spinner("Generating SARIF..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/sarif/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download results.sarif",
                        data=json.dumps(res.json(), indent=2),
                        file_name="results.sarif",
                        mime="application/json"
                    )
                else:
                    st.error("Failed to generate SARIF.")

        st.markdown("---")
        
        # 2. Rector Config
        st.markdown("#### 2. AI-Synthesized Rector Configuration")
        st.caption("Automated PHP refactoring rules synthesized by the LLM based on detected legacy patterns (`rector.php`).")
        if st.button("Generate rector.php"):
            with st.spinner("Synthesizing custom Rector rules via AI..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/rector/{run_id}")
                if res.status_code == 200:
                    st.success("✅ Rector Configuration Synthesized")
                    with st.expander("👁️ View AI-Generated rector.php", expanded=True):
                        st.code(res.text, language="php")
                    st.download_button(
                        label="⬇️ Download rector.php",
                        data=res.text,
                        file_name="rector.php",
                        mime="text/php"
                    )
                else:
                    st.error("Failed to generate Rector config.")
                    
        st.markdown("---")
        
        # 3. Deptrac Config
        st.markdown("#### 3. Deptrac Layer Config")
        st.caption("Architectural boundary enforcement rules based on inferred layers (`deptrac.yaml`).")
        if st.button("Generate deptrac.yaml"):
            with st.spinner("Generating Deptrac rules..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/deptrac/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download deptrac.yaml",
                        data=res.text,
                        file_name="deptrac.yaml",
                        mime="application/yaml"
                    )
                else:
                    st.error("Failed to generate Deptrac config.")
                    
        st.markdown("---")
        
        # 4. Strict JSON
        st.markdown("#### 4. Machine Data Dump")
        st.caption("A comprehensive, strict JSON schema dump of all system nodes, edges, and scores.")
        if st.button("Generate Strict JSON"):
            with st.spinner("Generating JSON Dump..."):
                res = requests.get(f"{FASTAPI_URL}/artifacts/json/{run_id}")
                if res.status_code == 200:
                    st.download_button(
                        label="⬇️ Download system_dump.json",
                        data=json.dumps(res.json(), indent=2),
                        file_name="system_dump.json",
                        mime="application/json"
                    )
                else:
                    st.error("Failed to generate JSON dump.")

if __name__ == "__main__":
    show_artifact_center()
