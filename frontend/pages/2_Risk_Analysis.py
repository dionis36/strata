import os
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Risk Analysis — Strata", layout="wide")
st.title("⚠️ Structural Risk Analysis")
st.markdown(
    "Inspect Phase 3 risk scores for each component — sorted by risk descending. "
    "Risk is computed from structural indicators derived from Phase 2 metrics."
)

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Status")
    try:
        health_url = FASTAPI_URL if FASTAPI_URL.endswith("/health") else f"{FASTAPI_URL}/health"
        res = requests.get(health_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"Status: {data.get('status')}")
            st.caption(f"Version: {data.get('version')}")
        else:
            st.error(f"API returned {res.status_code}")
    except requests.exceptions.RequestException:
        st.error("Failed to connect to API")

# ── Risk Level Colour Mapping ─────────────────────────────────────────────────
LEVEL_COLORS = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
}


def _badge(level: str) -> str:
    return f"{LEVEL_COLORS.get(level, '⚪')} {level}"


# ── Main Panel ────────────────────────────────────────────────────────────────
st.header("Risk Matrix")

run_id = st.number_input("Run ID", min_value=1, step=1, value=1)

if st.button("Query Risk Matrix"):
    with st.spinner(f"Loading risk scores for run {run_id}…"):
        try:
            risk_url = FASTAPI_URL.replace("/health", "") + f"/risk/{run_id}"
            response = requests.get(risk_url, timeout=30)

            if response.status_code == 404:
                st.warning(
                    f"No risk data found for Run ID {run_id}. "
                    "Run an analysis first via the home page."
                )
            elif response.status_code != 200:
                st.error(f"API error {response.status_code}: {response.text}")
            else:
                payload = response.json()
                components = payload.get("components", [])

                if not components:
                    st.info("No components returned for this run.")
                else:
                    # Summary metrics
                    total = len(components)
                    by_level = {
                        lvl: sum(1 for c in components if c["risk_level"] == lvl)
                        for lvl in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                    }
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Components", total)
                    c2.metric("🔴 Critical", by_level["CRITICAL"])
                    c3.metric("🟠 High",     by_level["HIGH"])
                    c4.metric("🟡 Medium",   by_level["MEDIUM"])
                    c5.metric("🟢 Low",      by_level["LOW"])

                    st.divider()

                    # Build DataFrame
                    df = pd.DataFrame(components)
                    df["risk_level"] = df["risk_level"].apply(_badge)
                    df = df.rename(columns={
                        "name":              "Component",
                        "type":              "Type",
                        "risk_score":        "Risk Score",
                        "risk_level":        "Risk Level",
                        "criticality_index": "Criticality",
                        "instability":       "Instability",
                        "cycle_flag":        "Cycle",
                        "coupling_pressure": "Coupling",
                    })

                    display_cols = [
                        "Component", "Type", "Risk Score", "Risk Level",
                        "Criticality", "Instability", "Cycle", "Coupling"
                    ]
                    st.dataframe(
                        df[[c for c in display_cols if c in df.columns]],
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Download
                    st.download_button(
                        label="⬇️ Download Raw JSON",
                        data=response.text,
                        file_name=f"risk_{run_id}.json",
                        mime="application/json",
                    )

        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
