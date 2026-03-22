import os
import json
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Risk Analysis — Strata", layout="wide")
st.title("⚠️ Structural & Behavioral Risk Analysis")
st.markdown(
    "Full risk matrix with structural and behavioral metrics. "
    "Select any component below the table to open a detailed explanation."
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

# ── Helpers ───────────────────────────────────────────────────────────────────
LEVEL_ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
SEV_ICON   = {"high": "🔴", "medium": "🟠", "low": "🟢"}

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_risk(run_id: int):
    r = requests.get(f"{FASTAPI_URL.rstrip('/')}/risk/{run_id}", timeout=30)
    r.raise_for_status()
    return r.json().get("components", [])

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_explain(run_id: int):
    r = requests.get(f"{FASTAPI_URL.rstrip('/')}/explain/{run_id}", timeout=60)
    r.raise_for_status()
    return {c["component_name"]: c for c in r.json().get("components", [])}

def _short(name: str) -> str:
    """Return the last segment of a backslash-separated component name."""
    return name.split("\\")[-1]

# ── Explanation Modal ─────────────────────────────────────────────────────────
@st.experimental_dialog("Component Explanation", width="large")
def show_explanation(component_name: str, run_id: int):
    with st.spinner("Loading explanation…"):
        try:
            explain_map = _fetch_explain(run_id)
        except Exception as e:
            st.error(f"Failed to load explanation: {e}")
            return

    comp = explain_map.get(component_name)
    if not comp:
        st.warning("No explanation data found for this component.")
        return

    level = comp["risk_level"]
    final_risk = comp["final_risk"]
    st.markdown(f"### `{_short(component_name)}`")
    st.markdown(
        f"**{LEVEL_ICON.get(level, '⚪')} {level}** &nbsp;|&nbsp; Final Risk: `{final_risk:.3f}`"
    )
    st.caption(f"Full ID: `{component_name}`")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Risk Summary", "🔍 Why Risky", "📄 Evidence"])

    # ── Tab 1 ────────────────────────────────────────────────────────────────
    with tab1:
        m = comp.get("evidence", {}).get("metrics", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Structural Risk",   f"{m.get('blast_radius', 0.0):.3f}")
        c2.metric("Behavioral Factor", f"{m.get('behavioral_factor', 0.0):.3f}")
        c3.metric("Final Risk",        f"{final_risk:.3f}")
        st.divider()
        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Criticality",      f"{m.get('criticality_index', 0.0):.3f}")
        r1c1.metric("Instability",      f"{m.get('instability', 0.0):.3f}")
        r1c2.metric("Coupling",         f"{m.get('coupling_pressure', 0.0):.3f}")
        r1c2.metric("Cycle Member",     "Yes" if m.get("cycle_flag") else "No")
        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Write Intensity",  f"{m.get('write_intensity', 0.0):.3f}")
        r2c2.metric("Table Deps",       m.get("table_dependencies", 0))

    # ── Tab 2 ────────────────────────────────────────────────────────────────
    with tab2:
        explanations = comp.get("explanations", [])
        if not explanations:
            st.info("No significant risk contributors found for this component.")
        else:
            grouped = {}
            for ex in explanations:
                grouped.setdefault(ex.get("category", "structural"), []).append(ex)
            labels = {"structural": "🏗️ Structural", "behavioral": "🗄️ Behavioral", "combined": "⚡ Combined"}
            for cat, items in grouped.items():
                st.markdown(f"**{labels.get(cat, cat.title())}**")
                for ex in items:
                    st.markdown(f"{SEV_ICON.get(ex['severity'], '⚪')} **[{ex['severity'].upper()}]** {ex['message']}")
                st.markdown("")

    # ── Tab 3 ────────────────────────────────────────────────────────────────
    with tab3:
        ev = comp.get("evidence", {})
        g  = ev.get("graph", {})
        code = ev.get("code", {})

        st.markdown("**📄 Source File**")
        fp = code.get("file_path")
        st.code(fp if fp else "Not available", language="text")

        st.markdown("**🔗 Dependent Components**")
        deps = g.get("dependent_components", [])
        if deps:
            for d in deps:
                st.markdown(f"- `{d}`")
        else:
            st.caption("No inbound dependencies detected.")

        scc = g.get("scc_members", [])
        if scc:
            st.markdown("**🔄 Cycle Members**")
            for m in scc:
                st.markdown(f"- `{m}`")


# ── Main ──────────────────────────────────────────────────────────────────────
st.header("Risk Matrix")

col_in, col_btn = st.columns([4, 1])
with col_in:
    run_id = st.number_input(
        "Run ID", min_value=1, step=1, value=st.session_state.get("active_run_id", 1)
    )
with col_btn:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("Query Risk Matrix", use_container_width=True):
        st.session_state["active_run_id"] = run_id

if "active_run_id" in st.session_state:
    active_run = st.session_state["active_run_id"]
    with st.spinner(f"Fetching risk data for run {active_run}…"):
        try:
            components = _fetch_risk(active_run)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.warning(f"No risk data for Run ID {active_run}. Run an analysis first.")
            else:
                st.error(f"API error {e.response.status_code}: {e.response.text}")
            components = []
        except Exception as e:
            st.error(f"Connection error: {e}")
            components = []

    if components:
        # ── KPI Summary ──────────────────────────────────────────────────────
        total  = len(components)
        by_lvl = {lvl: sum(1 for c in components if c["risk_level"] == lvl)
                  for lvl in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total",       total)
        k2.metric("🔴 Critical", by_lvl["CRITICAL"])
        k3.metric("🟠 High",     by_lvl["HIGH"])
        k4.metric("🟡 Medium",   by_lvl["MEDIUM"])
        k5.metric("🟢 Low",      by_lvl["LOW"])
        st.divider()

        # ── Full Stats DataFrame ──────────────────────────────────────────────
        rows = []
        for c in components:
            rows.append({
                "Component":        c.get("name", ""),
                "Type":             c.get("type", ""),
                "Betweenness":      c.get("norm_betweenness", 0.0),
                "Blast Radius":     c.get("norm_blast_radius", 0.0),
                "In-Degree":        c.get("norm_in_degree", 0.0),
                "Out-Degree":       c.get("norm_out_degree", 0.0),
                "Criticality":      c.get("criticality_index", 0.0),
                "Instability":      c.get("instability", 0.0),
                "Cycle":            "✓" if c.get("cycle_flag") else "",
                "Coupling":         c.get("coupling_pressure", 0.0),
                "Structural Risk":  c.get("risk_score", 0.0),
                "Behavioral ×":     c.get("behavioral_factor", 0.0),
                "Final Risk":       c.get("final_risk", c.get("risk_score", 0.0)),
                "Level":            f"{LEVEL_ICON.get(c['risk_level'], '')} {c['risk_level']}",
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("Final Risk", ascending=False).reset_index(drop=True)

        st.dataframe(
            df,
            use_container_width=True,
            height=460,
            column_config={
                "Component":       st.column_config.TextColumn("Component", width="medium"),
                "Type":            st.column_config.TextColumn("Type", width="small"),
                "Betweenness":     st.column_config.NumberColumn("Betweenness",  format="%.3f"),
                "Blast Radius":    st.column_config.NumberColumn("Blast Radius", format="%.3f"),
                "In-Degree":       st.column_config.NumberColumn("In-Degree",    format="%.3f"),
                "Out-Degree":      st.column_config.NumberColumn("Out-Degree",   format="%.3f"),
                "Criticality":     st.column_config.NumberColumn("Criticality",  format="%.3f"),
                "Instability":     st.column_config.NumberColumn("Instability",  format="%.3f"),
                "Coupling":        st.column_config.NumberColumn("Coupling",     format="%.3f"),
                "Structural Risk": st.column_config.NumberColumn("Structural ⚠️",format="%.3f"),
                "Behavioral ×":    st.column_config.NumberColumn("Behavioral ×", format="%.3f"),
                "Final Risk":      st.column_config.ProgressColumn(
                                        "Final Risk", min_value=0, max_value=1, format="%.3f"
                                    ),
                "Level":           st.column_config.TextColumn("Level", width="small"),
            },
            hide_index=True,
        )

        # ── Explanation Selector ─────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🔍 Explain a Component")
        st.caption("Select any component to open an evidence-backed explanation.")

        # Build name list in same sort order as table (by Final Risk desc)
        sorted_names = [c.get("name", "") for c in sorted(
            components, key=lambda x: x.get("final_risk", x.get("risk_score", 0)), reverse=True
        )]
        display_names = [_short(n) for n in sorted_names]

        col_sel, col_btn = st.columns([5, 1])
        with col_sel:
            selected_idx = st.selectbox(
                "Component",
                options=range(len(sorted_names)),
                format_func=lambda i: f"{display_names[i]}",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("Open →", use_container_width=True):
                show_explanation(sorted_names[selected_idx], active_run)

        # ── Download ─────────────────────────────────────────────────────────
        st.divider()
        st.download_button(
            label="⬇️ Download Raw Risk JSON",
            data=json.dumps(components, indent=2),
            file_name=f"risk_{active_run}.json",
            mime="application/json",
        )
