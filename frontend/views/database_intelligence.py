import streamlit as st
import requests
import pandas as pd
import os

def show_database_intelligence():
    st.title("Database Intelligence")
    st.markdown("### Persistence Layer Analysis")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=60)
    def fetch_db_data(rid):
        res = requests.get(f"{FASTAPI_URL}/db-intelligence/{rid}", timeout=30)
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_db_data(run_id)
    if not data:
        st.error("Technical error retrieving persistence intelligence data.")
        return

    # --- Metrics Aggregate ---
    taxonomy = data.get("taxonomy", {})
    risk = data.get("risk_audit", {})
    ownership = data.get("table_ownership", [])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🧱 Raw SQL Vectors", sum(v.get("raw_sql", 0) for v in taxonomy.values()))
    k2.metric("📦 ORM/QB Abstractions", sum(v.get("orm", 0) for v in taxonomy.values()))
    k3.metric("🔄 Transaction Guards", sum(v.get("transactions", 0) for v in taxonomy.values()))
    k4.metric("🚨 Credential Risks", sum(v.get("credentials", 0) for v in taxonomy.values()))

    st.markdown("---")

    tabs = st.tabs([
        "Access Taxonomy",
        "Risk Audit",
        "Table Ownership",
        "Inferred Domain Model"
    ])

    with tabs[0]:
        st.markdown("#### Architectural Access Patterns")
        if taxonomy:
            rows = [{"File": f, **c} for f, c in taxonomy.items() if sum(c.values()) > 0]
            if rows:
                df = pd.DataFrame(rows).sort_values("raw_sql", ascending=False)
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("No persistence access patterns identified.")

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Security Risk: Hardcoded Credentials")
            creds = risk.get("credential_risks", [])
            if creds:
                st.dataframe(pd.DataFrame(creds), hide_index=True, use_container_width=True)
            else:
                st.success("No hardcoded credentials detected.")

        with c2:
            st.markdown("#### Logic Risk: Unguarded Writes")
            no_tx = risk.get("unhandled_transactions", [])
            if no_tx:
                st.dataframe(pd.DataFrame(no_tx), hide_index=True, use_container_width=True)
            else:
                st.success("Transaction integrity verified.")

    with tabs[2]:
        st.markdown("#### Table Ownership by Bounded Context")
        if ownership:
            df_own = pd.DataFrame(ownership)
            st.dataframe(df_own[["table", "primary_owner", "total_writes", "cross_module_write"]], 
                         hide_index=True, use_container_width=True)

    with tabs[3]:
        st.markdown("#### Inferred Domain Relationships")
        erd_dot = data.get("erd_dot", "")
        if erd_dot:
            st.graphviz_chart(erd_dot, use_container_width=True)
        else:
            st.info("Insufficient data to infer domain relationships.")

if __name__ == "__main__":
    show_database_intelligence()
