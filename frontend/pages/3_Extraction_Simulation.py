import os
import json
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Extraction Simulation — Strata", layout="wide")
st.title("🏗️ Microservice Extraction Simulator")
st.markdown(
    "Evaluates candidates for service extraction by simulating their isolation behind an API boundary. "
    "This engine balances structural risk, internal cohesion, and the resulting architectural impact."
)

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Status")
    try:
        res = requests.get(f"{FASTAPI_URL.rstrip('/')}/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"Status: {data.get('status')}")
            st.caption(f"Version: {data.get('version')}")
        else:
            st.error(f"API returned {res.status_code}")
    except requests.exceptions.RequestException:
        st.error("Failed to connect to API")

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

# ── Main UI ───────────────────────────────────────────────────────────────────
col_in, col_btn = st.columns([4, 1])
with col_in:
    run_id = st.number_input(
        "Run ID", min_value=1, step=1, value=st.session_state.get("active_run_id_ext", 1)
    )
with col_btn:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("Simulate Extraction", use_container_width=True):
        st.session_state["active_run_id_ext"] = run_id

if "active_run_id_ext" in st.session_state:
    active_run = st.session_state["active_run_id_ext"]
    with st.spinner(f"Running simulation engine for run {active_run}…"):
        try:
            candidates = _fetch_candidates(active_run)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.warning(f"No risk data for Run ID {active_run}. Run Phase 1-4 analysis first.")
            else:
                st.error(f"API error {e.response.status_code}: {e.response.text}")
            candidates = []
        except Exception as e:
            st.error(f"Connection error: {e}")
            candidates = []

    if candidates:
        st.divider()

        # Build DataFrame
        rows = []
        for c in candidates:
            rows.append({
                "Unit Name": c.get("unit", ""),
                "Type": c.get("type", "").capitalize(),
                "Score": round(c.get("score", 0.0), 3),
                "Recommendation": REC_ICONS.get(c.get("recommendation", ""), c.get("recommendation")),
                "_raw": c  # Keep raw data for selection
            })

        df = pd.DataFrame(rows)

        # ── KPI Summary ──────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Candidates", len(candidates))
        col2.metric("✅ Safe", len(df[df["Recommendation"] == "✅ Safe"]))
        col3.metric("⚠️ Caution", len(df[df["Recommendation"] == "⚠️ Caution"]))
        col4.metric("⛔ Blocked", len(df[df["Recommendation"] == "⛔ Blocked"]))

        st.markdown("### Ranked Proposals")
        st.dataframe(
            df.drop(columns=["_raw"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Unit Name": st.column_config.TextColumn("Unit Name", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Score": st.column_config.ProgressColumn("Quality Score", min_value=0, max_value=1, format="%.2f"),
                "Recommendation": st.column_config.TextColumn("Action", width="medium"),
            }
        )

        st.divider()
        st.markdown("### 🔍 Simulated Architectural Impact")
        st.caption("Select a candidate to inspect the impact of its extraction.")
        
        display_names = [r["Unit Name"] for r in rows]
        sel_idx = st.selectbox(
            "Select Candidate",
            options=range(len(rows)),
            format_func=lambda i: f"{display_names[i]} ({rows[i]['Recommendation']})",
            label_visibility="collapsed"
        )
        
        if sel_idx is not None:
            raw = rows[sel_idx]["_raw"]
            impact = raw.get("impact", {})
            reasoning = raw.get("reasoning", [])
            nodes = raw.get("nodes", [])
            
            # --- OVERARCHING AI VERDICT ---
            verdict_text = ""
            details = []
            for r in reasoning:
                if "**AI Verdict:" in r:
                    verdict_text = r
                else:
                    details.append(r)
            
            if verdict_text:
                if "Safe to Extract" in verdict_text:
                    st.success(verdict_text)
                elif "Caution" in verdict_text:
                    st.warning(verdict_text)
                elif "Refactor First" in verdict_text:
                    st.warning(verdict_text)
                else:
                    st.error(verdict_text)

            detail_col1, detail_col2 = st.columns([1, 1])
            with detail_col1:
                st.markdown("#### 🧠 Decision Engine Logic")
                for d in details:
                    st.markdown(f"- {d}")
                        
                st.markdown("#### 📦 Internal Composition")
                st.caption(f"{len(nodes)} modules bundled in this unit")
                with st.expander("View Included Nodes"):
                    for n in nodes:
                        st.write(f" `{n}`")

            with detail_col2:
                st.markdown("#### 💥 Simulated Impact Metrics")
                before_risk = impact.get("before_risk", 0.0)
                after_risk = impact.get("after_risk", 0.0)
                r_change = impact.get("risk_change", 0.0)
                
                i_col1, i_col2 = st.columns(2)
                i_col1.metric(
                    "System Risk Shift", 
                    value=f"{after_risk:.3f}", 
                    delta=f"{r_change:.3f}" if r_change != 0 else None,
                    delta_color="inverse"
                )
                i_col2.metric("Dependency Breaks", impact.get("dependency_breaks", 0))
                
                i_col3, i_col4 = st.columns(2)
                i_col3.metric("Proxy API Complexity", impact.get("interface_complexity", 0), help="Number of edges crossing the new extraction boundary.")
                i_col4.metric("Shared Data Tables", impact.get("data_isolation_difficulty", 0), help="Number of tables accessed simultaneously from inside and outside the proposed boundary.")
