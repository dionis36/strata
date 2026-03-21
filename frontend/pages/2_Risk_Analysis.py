import os
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Risk Analysis — Strata", layout="wide")
st.title("⚠️ Structural & Behavioral Risk Analysis")
st.markdown(
    "Inspect risk scores sorted by final (amplified) risk. "
    "Click **🔍 Explain** on any component to understand *why* it is at risk."
)

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Status")
    try:
        health_url = f"{FASTAPI_URL.rstrip('/')}/health"
        res = requests.get(health_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"Status: {data.get('status')}")
            st.caption(f"Version: {data.get('version')}")
        else:
            st.error(f"API returned {res.status_code}")
    except requests.exceptions.RequestException:
        st.error("Failed to connect to API")

# ── Helpers ───────────────────────────────────────────────────────────────────
LEVEL_COLORS = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
SEV_COLORS   = {"high": "🔴", "medium": "🟠", "low": "🟢"}

def _badge(level: str) -> str:
    return f"{LEVEL_COLORS.get(level, '⚪')} {level}"

def _fetch_risk(run_id: int):
    url = f"{FASTAPI_URL.rstrip('/')}/risk/{run_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("components", [])

def _fetch_explain(run_id: int):
    url = f"{FASTAPI_URL.rstrip('/')}/explain/{run_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return {c["component_name"]: c for c in r.json().get("components", [])}

# ── Explanation Modal ─────────────────────────────────────────────────────────
@st.dialog("Component Explanation", width="large")
def show_explanation(component_name: str, run_id: int):
    with st.spinner("Loading explanation…"):
        try:
            explain_map = _fetch_explain(run_id)
        except Exception as e:
            st.error(f"Failed to load explanation: {e}")
            return

    comp = explain_map.get(component_name)
    if not comp:
        st.warning("No explanation data available for this component.")
        return

    # Header
    level = comp["risk_level"]
    final_risk = comp["final_risk"]
    st.markdown(f"### `{component_name.split(chr(92))[-1]}`")
    st.markdown(f"**{_badge(level)}** &nbsp;|&nbsp; Final Risk: `{final_risk:.3f}`")
    st.caption(f"Full ID: `{component_name}`")
    st.divider()

    # 3 Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Risk Summary", "🔍 Why Risky", "📄 Evidence"])

    # ── Tab 1: Risk Summary ──────────────────────────────────────────────────
    with tab1:
        ev = comp.get("evidence", {})
        m  = ev.get("metrics", {})

        col1, col2, col3 = st.columns(3)
        col1.metric("Structural Risk",   f"{m.get('blast_radius', 'N/A')}")
        col2.metric("Behavioral Factor", f"{m.get('behavioral_factor', 0.0):.3f}")
        col3.metric("Final Risk",        f"{final_risk:.3f}")

        st.divider()
        st.markdown("**Structural Indicators**")
        s_col1, s_col2 = st.columns(2)
        s_col1.metric("Criticality Index", f"{m.get('criticality_index', 0.0):.3f}")
        s_col1.metric("Instability",        f"{m.get('instability', 0.0):.3f}")
        s_col2.metric("Coupling Pressure",  f"{m.get('coupling_pressure', 0.0):.3f}")
        s_col2.metric("Cycle Member",       "Yes" if m.get("cycle_flag") else "No")

        st.markdown("**Behavioral Indicators**")
        b_col1, b_col2 = st.columns(2)
        b_col1.metric("Write Intensity",    f"{m.get('write_intensity', 0.0):.3f}")
        b_col2.metric("Table Dependencies", m.get("table_dependencies", 0))

    # ── Tab 2: Why Risky ────────────────────────────────────────────────────
    with tab2:
        explanations = comp.get("explanations", [])
        if not explanations:
            st.info("No significant risk contributors found for this component.")
        else:
            # Group by category
            grouped = {"structural": [], "behavioral": [], "combined": []}
            for ex in explanations:
                cat = ex.get("category", "structural")
                grouped.setdefault(cat, []).append(ex)

            cat_labels = {
                "structural": "🏗️ Structural",
                "behavioral": "🗄️ Behavioral",
                "combined":   "⚡ Combined",
            }
            for cat, items in grouped.items():
                if not items:
                    continue
                st.markdown(f"**{cat_labels.get(cat, cat.title())}**")
                for ex in items:
                    sev_icon = SEV_COLORS.get(ex["severity"], "⚪")
                    st.markdown(
                        f"{sev_icon} **[{ex['severity'].upper()}]** {ex['message']}"
                    )
                st.markdown("")  # spacer

    # ── Tab 3: Evidence ──────────────────────────────────────────────────────
    with tab3:
        ev   = comp.get("evidence", {})
        g    = ev.get("graph", {})
        code = ev.get("code", {})

        # Source file
        st.markdown("**📄 Source File**")
        file_path = code.get("file_path")
        if file_path:
            st.code(file_path, language="text")
        else:
            st.caption("File path not available.")

        # Dependent components
        st.markdown("**🔗 Dependent Components** *(other components that call into this one)*")
        dependents = g.get("dependent_components", [])
        if dependents:
            for dep in dependents:
                st.markdown(f"- `{dep}`")
        else:
            st.caption("No inbound dependencies detected.")

        # SCC members (cycle)
        scc = g.get("scc_members", [])
        if scc:
            st.markdown("**🔄 Cycle Members** *(sharing same strongly-connected component)*")
            for member in scc:
                st.markdown(f"- `{member}`")


# ── Main Panel ────────────────────────────────────────────────────────────────
st.header("Risk Matrix")

run_id = st.number_input("Run ID", min_value=1, step=1, value=1)

if st.button("Query Risk Matrix"):
    with st.spinner(f"Loading risk scores for run {run_id}…"):
        try:
            components = _fetch_risk(run_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.warning(
                    f"No risk data found for Run ID {run_id}. "
                    "Run an analysis first via the home page."
                )
            else:
                st.error(f"API error {e.response.status_code}: {e.response.text}")
            components = []
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
            components = []

    if components:
        # Summary row
        total  = len(components)
        by_lvl = {lvl: sum(1 for c in components if c["risk_level"] == lvl)
                  for lvl in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Components",   total)
        c2.metric("🔴 Critical",  by_lvl["CRITICAL"])
        c3.metric("🟠 High",      by_lvl["HIGH"])
        c4.metric("🟡 Medium",    by_lvl["MEDIUM"])
        c5.metric("🟢 Low",       by_lvl["LOW"])
        st.divider()

        # Slim table — Navigation only
        st.markdown("*Click **🔍 Explain** to see a full evidence-backed breakdown.*")
        st.session_state.setdefault("selected_component", None)

        for comp in components:
            name  = comp["name"]
            level = comp["risk_level"]
            fr    = comp.get("final_risk", comp.get("risk_score", 0.0))

            col_name, col_level, col_risk, col_btn = st.columns([4, 1.5, 1.5, 1.5])
            col_name.markdown(f"`{name.split(chr(92))[-1]}`", help=name)
            col_level.markdown(_badge(level))
            col_risk.markdown(f"`{fr:.3f}`")
            if col_btn.button("🔍 Explain", key=f"explain_{name}"):
                show_explanation(name, run_id)

        st.divider()
        # Keep download available
        import json
        st.download_button(
            label="⬇️ Download Raw Risk JSON",
            data=json.dumps(components, indent=2),
            file_name=f"risk_{run_id}.json",
            mime="application/json",
        )
