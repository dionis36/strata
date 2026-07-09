import streamlit as st
import requests
import os
import re

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def render_markdown_with_mermaid(content: str):
    import streamlit.components.v1 as components
    import uuid
    
    parts = re.split(r'```mermaid\n(.*?)\n```', content, flags=re.DOTALL)
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                st.markdown(part, unsafe_allow_html=True)
        else:
            code = part.strip()
            # Escape code for JS injection
            escaped_code = code.replace("`", "\\`")
            
            lines = code.count('\n')
            estimated_height = max(500, 200 + (lines * 30))
            
            html = f"""
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background-color: transparent; }}
            </style>
            <div class="mermaid" style="display: flex; justify-content: center;">
                {code}
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
            </script>
            """
            components.html(html, height=estimated_height, scrolling=False)

def show_report_viewer():
    if st.button("Back to Dashboard"):
        from views import page_registry
        st.switch_page(page_registry.PAGE_DASHBOARD)
    
    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.error("No active analysis run found.")
        return
        
    @st.cache_data(show_spinner=False)
    def fetch_human_cached(run_id_val):
        res = requests.get(f"{FASTAPI_URL}/artifacts/human/{run_id_val}?format=md")
        return res.content.decode('utf-8') if res.status_code == 200 else None
        
    with st.spinner("Loading Report..."):
        md_content = fetch_human_cached(run_id)
        
    if md_content:
        render_markdown_with_mermaid(md_content)
    else:
        st.error("Failed to load report from the server.")

if __name__ == "__main__":
    show_report_viewer()
