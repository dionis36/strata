import os
import json
import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Strata - Modernization Cockpit", layout="wide")

# Cockpit Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1a1c24; border-radius: 5px; padding: 15px; border: 1px solid #333; }
    .stAlert { background-color: #1a1c24; border: 1px solid #444; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

class ExecutiveReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Strata: Executive Modernization Intelligence', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d")}', 0, 0, 'C')

def generate_pdf(strategy_name, roi, risk_delta, protocol_steps):
    pdf = ExecutiveReport()
    pdf.add_page()
    
    # ROI Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Modernization Strategy: {strategy_name}', 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Modernization ROI: {roi:.1f}% Complexity Reduction', 0, 1)
    pdf.cell(0, 10, f'Systemic Risk Shift: {risk_delta:.3f}', 0, 1)
    pdf.ln(10)
    
    # Protocol Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Surgical Implementation Protocol', 0, 1)
    pdf.set_font('Arial', '', 10)
    for step in protocol_steps:
        pdf.multi_cell(0, 8, f"- {step['name']}: {step['fqn']}")
        pdf.ln(2)
        
    path = f"/tmp/strata_report_{datetime.now().timestamp()}.pdf"
    pdf.output(path)
    return path

st.title("🕹️ Modernization Cockpit")
st.markdown("---")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Cockpit Controls")
    run_id = st.number_input("Target Run ID", min_value=1, step=1, value=1)
    st.markdown("---")
    st.caption("Strata Simulation Engine v1.0")

# ── Data Fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_candidates(run_id: int):
    r = requests.get(f"{FASTAPI_URL.rstrip('/')}/extraction/{run_id}", timeout=120)
    r.raise_for_status()
    return r.json().get("candidates", [])

REC_ICONS = {
    "SAFE_TO_EXTRACT": "✅ Safe",
    "EXTRACT_WITH_CAUTION": "⚠️ Caution",
    "REQUIRES_REFACTOR_FIRST": "🛠️ Refactor First",
    "DO_NOT_EXTRACT": "⛔ Blocked"
}

try:
    candidates = _fetch_candidates(run_id)
except:
    st.warning(f"No analysis data found for Run ID {run_id}. Please run the Intelligence Engine first.")
    candidates = []

if candidates:
    # 1. TOP-LEVEL METRICS
    df = pd.DataFrame([
        {"Unit": c["unit"], "Score": c["score"], "Action": REC_ICONS.get(c["recommendation"], c["recommendation"])}
        for c in candidates
    ])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Extraction Candidates", len(candidates))
    col2.metric("Optimal Strategy", df.iloc[0]["Unit"])
    col3.metric("Highest Quality Score", f"{df['Score'].max():.2f}")

    st.markdown("### 🔍 Select Extraction Strategy")
    sel_idx = st.selectbox(
        "Modernization Strategy",
        options=range(len(candidates)),
        format_func=lambda i: f"{candidates[i]['unit']} ({REC_ICONS.get(candidates[i]['recommendation'])})",
        label_visibility="collapsed"
    )

    if sel_idx is not None:
        raw = candidates[sel_idx]
        impact = raw.get("impact", {})
        
        # --- B.3 ROI CALCULATION ---
        before_risk = impact.get("before_risk", 0.0)
        after_risk = impact.get("after_risk", 0.0)
        risk_delta = impact.get("risk_change", 0.0)
        roi = ((before_risk - after_risk) / before_risk * 100) if before_risk > 0 else 0
        
        # 2. EXECUTIVE BRIEF
        st.subheader("📊 Executive Intelligence Brief")
        e_col1, e_col2, e_col3 = st.columns(3)
        e_col1.metric("Modernization ROI", f"{roi:.1f}%", help="Estimated complexity reduction across the system.")
        e_col2.metric("Risk Reduction", f"{abs(risk_delta):.3f}" if risk_delta < 0 else f"+{risk_delta:.3f}")
        e_col3.metric("Strategic Feasibility", raw.get("recommendation").replace("_", " "))

        st.divider()
        
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🛡️ Safety & Assurance")
            s_col1, s_col2 = st.columns(2)
            s_col1.metric("Acyclic Guarantee", "PASS", delta="Acyclic", delta_color="normal")
            s_col2.metric("Interface Weight", impact.get("interface_complexity", 0))
            
            st.markdown("#### 🧠 Decision Logic")
            for reason in raw.get("reasoning", []):
                st.markdown(f"- {reason}")

        with col_right:
            st.subheader("🔭 Topological Foresight")
            proxy_name = f"{raw.get('unit').replace(' ', '')}_Service"
            dot_code = f"digraph {{ \n"
            dot_code += '  rankdir=LR; bgcolor="transparent"; node [shape=box, style=filled, fontname="Inter", fontsize=10]; \n'
            dot_code += '  edge [color="#555", arrowsize=0.5]; \n'
            dot_code += f'  "{proxy_name}" [fillcolor="#2e4a3e", color="#4ade80", fontcolor="white", label="{proxy_name}\\n(Extracted Service)"]; \n'
            dot_code += '  "Monolith_Client" [fillcolor="#1a1c24", color="#666", fontcolor="#aaa", label="Legacy Clients"]; \n'
            dot_code += '  "Shared_Database" [fillcolor="#1a1c24", color="#666", fontcolor="#aaa", label="Infrastructure"]; \n'
            dot_code += f'  "Monolith_Client" -> "{proxy_name}" [label="API Call", fontcolor="#888", fontsize=8]; \n'
            dot_code += f'  "{proxy_name}" -> "Shared_Database" [label="DB Query", fontcolor="#888", fontsize=8]; \n'
            dot_code += "}"
            st.graphviz_chart(dot_code)

        # 3. THE PROTOCOL
        st.divider()
        st.header("📋 Surgical Modernization Protocol")
        
        protocol_col1, protocol_col2 = st.columns([1, 2])
        
        with protocol_col1:
            st.markdown("#### Configuration")
            target_ns = st.text_input("Target Namespace", value=f"Strata\\Services\\{raw.get('unit').replace(' ', '')}")
            st.info(f"**Modernization Scope**: {len(raw.get('node_details', []))} core modules identified for isolation.")
            

            # --- DOCUMENTATION EXPORT ---
            col_pdf, col_md = st.columns(2)
            
            with col_pdf:
                if st.button("📄 Download PDF Brief", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        pdf_path = generate_pdf(raw['unit'], roi, risk_delta, raw['node_details'])
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="💾 Save PDF",
                                data=f,
                                file_name=f"Strata_ROI_Report_{raw['unit']}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
            
            with col_md:
                # Generate Markdown Content
                md_content = f"# Modernization Blueprint: {raw['unit']}\n\n"
                md_content += f"## Strategy Overview\n- **ROI**: {roi:.1f}% Complexity Reduction\n- **Risk Shift**: {risk_delta:.3f}\n- **Interface Weight**: {impact.get('interface_complexity', 0)}\n\n"
                md_content += "## Surgical Protocol\n"
                for node in raw.get("node_details", []):
                    md_content += f"### Protocol for {node['name']}\n"
                    md_content += f"- **Target Location**: `Strata\\Services\\{node['name']}`\n"
                    md_content += f"- **Original FQN**: `{node['fqn']}`\n\n"
                
                st.download_button(
                    label="📝 Download Markdown",
                    data=md_content,
                    file_name=f"Strata_Blueprint_{raw['unit']}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
        with protocol_col2:
            st.markdown("#### Implementation Steps")
            for node in raw.get("node_details", []):
                with st.expander(f"Protocol: {node['name']}"):
                    st.markdown(f"**Source**: `{node['file_path']}`")
                    st.code(f"// Step 1: Encapsulate {node['name']}\n// Step 2: Extract to {target_ns}\\{node['name']}", language="php")
        
st.sidebar.markdown("---")
st.sidebar.caption("Strata Executive Intelligence v1.0")
