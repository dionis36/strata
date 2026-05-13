import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Database Intelligence", page_icon="🗄️", layout="wide")

st.title("🗄️ Database Intelligence (Req 11)")
st.markdown("Deep analysis of all database access patterns — Raw SQL, ORM, transactions, credential risks, and an inferred ERD.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

# --- Run Selector ---
try:
    runs_res = requests.get(f"{FASTAPI_URL}/runs", timeout=5)
    if runs_res.status_code == 200:
        available_runs = runs_res.json()
        run_options = {f"Run {r['id']} - {r['started_at'][:10]} ({r['total_files']} Files)": r['id'] for r in available_runs if r['status'].upper() == 'COMPLETED'}
    else:
        run_options = {}
except Exception:
    run_options = {}

if not run_options:
    st.warning("⚠️ No completed runs found. Please run an Intelligence Scan from the Home page.")
    st.stop()

selected_run_label = st.selectbox("Select Analysis Run:", list(run_options.keys()))
run_id = run_options[selected_run_label]

@st.cache_data(ttl=60)
def fetch_db_data(rid):
    res = requests.get(f"{FASTAPI_URL}/db-intelligence/{rid}", timeout=30)
    if res.status_code == 200:
        return res.json()
    return None

with st.spinner("Analyzing database intelligence layer..."):
    data = fetch_db_data(run_id)

if not data:
    st.error("Failed to fetch database intelligence. Ensure the backend is running and the scan succeeded.")
    st.stop()

# --- Top KPI Banner ---
taxonomy = data.get("taxonomy", {})
risk = data.get("risk_audit", {})
ownership = data.get("table_ownership", [])

total_raw_sql   = sum(v.get("raw_sql", 0) for v in taxonomy.values())
total_orm       = sum(v.get("orm", 0) for v in taxonomy.values())
total_sprocs    = sum(v.get("stored_procs", 0) for v in taxonomy.values())
total_tx        = sum(v.get("transactions", 0) for v in taxonomy.values())
total_creds     = sum(v.get("credentials", 0) for v in taxonomy.values())
total_dupe_q    = len(risk.get("duplicate_queries", []))
cross_module    = sum(1 for t in ownership if t.get("cross_module_write"))

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
k1.metric("Raw SQL Calls",    total_raw_sql,  delta=None)
k2.metric("ORM Calls",        total_orm,      delta=None)
k3.metric("Stored Procs",     total_sprocs,   delta=None)
k4.metric("Transactions",     total_tx,       delta=None)
k5.metric("Cred Risks 🔴",   total_creds,    delta=None)
k6.metric("Duplicate Queries",total_dupe_q,   delta=None)
k7.metric("Cross-Module Writes ⚠️", cross_module, delta=None)

st.markdown("---")

tab_taxonomy, tab_risk, tab_ownership, tab_erd = st.tabs([
    "📊 Data Flow Taxonomy",
    "⚠️ Risk Audit",
    "🏛️ Table Ownership",
    "🔀 Inferred ERD"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Data Flow Taxonomy
# ──────────────────────────────────────────────────────────────────────────────
with tab_taxonomy:
    st.markdown("### Per-File Database Access Taxonomy")
    st.write("Each row represents a scanned file. Columns show how many of each DB pattern was detected via AST.")

    if taxonomy:
        rows = []
        for fname, counts in taxonomy.items():
            total = sum(counts.values())
            if total > 0:
                rows.append({
                    "File": fname,
                    "Raw SQL": counts.get("raw_sql", 0),
                    "ORM / Query Builder": counts.get("orm", 0),
                    "Stored Procs": counts.get("stored_procs", 0),
                    "Transactions": counts.get("transactions", 0),
                    "Cred Risks": counts.get("credentials", 0),
                })
        if rows:
            df = pd.DataFrame(rows).sort_values("Raw SQL", ascending=False)
            st.dataframe(
                df, hide_index=True, use_container_width=True,
                column_config={
                    "Cred Risks": st.column_config.NumberColumn("🔴 Cred Risks"),
                    "Raw SQL": st.column_config.NumberColumn("Raw SQL 🧱"),
                    "ORM / Query Builder": st.column_config.NumberColumn("ORM / QB ✅"),
                }
            )
        else:
            st.info("No database access patterns detected in this run. Try a scan with a DB-heavy codebase.")
    else:
        st.info("No taxonomy data available.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Risk Audit
# ──────────────────────────────────────────────────────────────────────────────
with tab_risk:
    creds  = risk.get("credential_risks", [])
    dupes  = risk.get("duplicate_queries", [])
    no_tx  = risk.get("unhandled_transactions", [])
    sprocs = risk.get("stored_procs", [])

    r1, r2 = st.columns(2)

    with r1:
        st.markdown("#### 🔴 Hardcoded DB Credentials")
        if creds:
            st.error(f"{len(creds)} occurrences of hardcoded connection strings detected.")
            df_creds = pd.DataFrame(creds)
            st.dataframe(df_creds, hide_index=True, use_container_width=True)
        else:
            st.success("✅ No hardcoded credentials detected.")

        st.markdown("#### 🔄 Stored Procedure Calls")
        if sprocs:
            st.warning(f"{len(sprocs)} stored procedure calls detected.")
            df_sprocs = pd.DataFrame(sprocs)
            st.dataframe(df_sprocs, hide_index=True, use_container_width=True)
        else:
            st.info("No stored procedure calls detected.")

    with r2:
        st.markdown("#### 🪞 Duplicated Queries")
        st.caption("Same normalized SQL found in multiple files — strong refactoring signal.")
        if dupes:
            st.warning(f"{len(dupes)} duplicated query patterns detected.")
            for d in dupes[:10]:
                with st.expander(f"`{d['query'][:60]}...` — duplicated in {d['count']} files"):
                    for f in d["files"]:
                        st.write(f"📄 `{f}`")
        else:
            st.success("✅ No duplicated queries detected.")

        st.markdown("#### ⚠️ SQL Without Transaction Safety")
        st.caption("Files that execute SQL writes without `beginTransaction` / `commit`.")
        if no_tx:
            st.warning(f"{len(no_tx)} files with unguarded SQL writes.")
            df_notx = pd.DataFrame(no_tx)
            st.dataframe(df_notx, hide_index=True, use_container_width=True,
                         column_config={"query_count": "SQL Write Count"})
        else:
            st.success("✅ All SQL writes appear to be inside transaction blocks.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Table Ownership
# ──────────────────────────────────────────────────────────────────────────────
with tab_ownership:
    st.markdown("### Table Ownership per Bounded Context")
    st.write("Identifies which module 'owns' each DB table based on write frequency. Cross-module writes are flagged as ⚠️.")

    if ownership:
        df_own = pd.DataFrame(ownership)
        df_own["⚠️ Cross-Module"] = df_own["cross_module_write"].map({True: "⚠️ YES", False: "✅ No"})
        df_own["Write Breakdown"] = df_own["write_contexts"].apply(
            lambda d: ", ".join([f"{ctx}({n})" for ctx, n in d.items()])
        )
        st.dataframe(
            df_own[["table", "primary_owner", "total_writes", "⚠️ Cross-Module", "Write Breakdown"]],
            hide_index=True, use_container_width=True,
            column_config={
                "table": "Table Name",
                "primary_owner": "Primary Owner (Context)",
                "total_writes": st.column_config.NumberColumn("Total Writes", format="%d"),
            }
        )
    else:
        st.info("No table ownership data. Re-run a scan on a codebase with active DB writes.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Inferred ERD
# ──────────────────────────────────────────────────────────────────────────────
with tab_erd:
    st.markdown("### Inferred Entity Relationship Diagram")
    st.write("Tables co-accessed within the same bounded context are linked. This reveals implicit domain relationships even without foreign keys.")

    erd_dot = data.get("erd_dot", "")
    erd_rels = data.get("erd_relationships", [])

    if erd_rels:
        try:
            st.graphviz_chart(erd_dot, use_container_width=True)
        except Exception:
            st.error("ERD graph too large to render inline. Download the DOT source.")

        st.download_button(
            "📥 Download ERD as Graphviz .dot",
            erd_dot,
            file_name=f"erd_{run_id}.dot",
            type="primary"
        )

        with st.expander("View Raw ERD Relationships Table"):
            st.dataframe(pd.DataFrame(erd_rels), hide_index=True, use_container_width=True)
    else:
        st.info("No implicit table relationships inferred. This codebase may use a single table or rely entirely on application-layer joins.")
