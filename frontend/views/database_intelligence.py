import streamlit as st
import requests
import pandas as pd
import os
from views import page_registry

def show_database_intelligence():
    st.title("Database Intelligence")
    st.markdown("##### Persistence Layer Analysis")

    with st.expander("Database Intelligence Blueprint Key", expanded=True):
        colA, colB = st.columns(2)
        with colA:
            st.markdown("""
            **Access Taxonomy**
            - **Raw SQL**: Hardcoded database queries. Indicates high coupling.
            - **ORM Abstractions**: Query logic separated from business logic.
            """)
        with colB:
            st.markdown("""
            **Risk Factors**
            - **Credential Risks**: Hardcoded usernames/passwords in connection calls.
            - **Duplicate Queries**: Copy-pasted SQL increasing maintenance overhead.
            - **Unguarded Writes**: INSERT/UPDATE outside of transaction blocks.
            """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
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

    # ── Pre-compute all derived values used across tabs ──────────────────
    taxonomy  = data.get("taxonomy", {})
    risk      = data.get("risk_audit", {})
    ownership = data.get("table_ownership", [])

    total_reads  = sum(v.get("reads", 0)  for v in taxonomy.values())
    total_writes = sum(v.get("writes", 0) for v in taxonomy.values())
    total_orm    = sum(v.get("orm", 0)    for v in taxonomy.values())
    total_raw    = total_reads + total_writes

    creds  = risk.get("credential_risks", [])
    dups   = risk.get("duplicate_queries", [])
    no_tx  = risk.get("unhandled_transactions", [])
    sprocs = risk.get("stored_procs", [])

    cross_module     = [t for t in ownership if t.get("cross_module_write")]
    total_risk_items = len(creds) + len(dups) + len(no_tx)

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Read Operations",
        total_reads,
        help="Total SELECT queries detected across all files. High read volume identifies data-heavy modules that will need a caching layer or read-replica strategy when extracted."
    )
    k2.metric(
        "Write Operations",
        total_writes,
        help="Total INSERT, UPDATE, and DELETE operations detected. Write-heavy files carry the highest data integrity risk during extraction they require a Data Access Layer or API Proxy."
    )
    k3.metric(
        "ORM Abstractions",
        total_orm,
        help="Database calls routed through an ORM layer (e.g., Eloquent, Doctrine) rather than raw SQL strings. Higher values indicate a more database-agnostic codebase that is easier to migrate to a new DB engine."
    )
    k4.metric(
        "Credential Risks",
        sum(v.get("credentials", 0) for v in taxonomy.values()),
        help="Files where database credentials (hostname, username, password) appear as hardcoded literal strings. A direct security vulnerability credentials cannot be rotated without a code change."
    )

    st.markdown("---")

    tabs = st.tabs([
        f"Access Taxonomy (CRUD Patterns) ({len(taxonomy)})",
        f"Risk Audit (Security & Integrity) ({total_risk_items})",
        f"Table Ownership (DB-per-Service) ({len(ownership)})",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 - Access Taxonomy
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### Architectural Access Patterns")
        st.caption("Every file ranked by its database interaction volume. Sorted by total operations descending.")

        rows = []
        if taxonomy:
            rows = [{"File": f, **c} for f, c in taxonomy.items() if sum(c.values()) > 0]
            if rows:
                df = pd.DataFrame(rows)
                reads_col  = df["reads"]  if "reads"  in df.columns else 0
                writes_col = df["writes"] if "writes" in df.columns else 0
                df["total_ops"] = reads_col + writes_col
                df = df.sort_values("total_ops", ascending=False).drop(columns=["total_ops"])
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("No persistence access patterns identified.")
        else:
            st.info("No taxonomy data available for this run.")

        # ── Tab-specific Insight ─────────────────────────────────────────
        st.markdown("---")
        raw_pct = f"{(total_raw / (total_raw + total_orm) * 100):.1f}%" if (total_raw + total_orm) > 0 else "N/A"
        top_files = [r["File"] for r in rows[:3]] if rows else []

        st.markdown("""
        <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Query Abstraction Intelligence</h4>
            <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Raw SQL vs. ORM usage ratio across the persistence layer.</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**METRIC**: Raw SQL vs. ORM Usage ratio across the persistence layer")
        st.markdown(
            "**INTERPRETATION**: This metric assesses how the system interacts with its database. "
            "Systems that rely entirely on raw SQL strings have every query hardcoded directly into "
            "the application code. ORM abstractions separate query logic from business logic, making "
            "the system database-agnostic. A high Raw SQL ratio means the DB driver is deeply embedded "
            "in the application layer."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. `{total_raw}` Raw SQL operations detected vs `{total_orm}` ORM-abstracted calls.\n"
            f"2. Raw SQL accounts for **{raw_pct}** of all database interactions.\n"
            f"3. Highest-volume files: {', '.join([f'`{f}`' for f in top_files]) if top_files else 'None detected'}."
        )
        if total_raw > 0 and total_orm == 0:
            st.markdown(
                "**RECOMMENDATION**: The persistence layer is entirely raw SQL. "
                "Review the **Risk Audit** tab to see which of these files also have duplicate queries or "
                "missing transaction boundaries - those are the highest-priority files to examine further."
            )
        elif total_raw == 0 and total_orm == 0:
            st.markdown(
                "**RECOMMENDATION**: No database interactions were detected in this analysis slice. "
                "If database access is expected, check the **Table Ownership** tab to verify whether "
                "the scanner reached the correct files."
            )
        else:
            st.markdown(
                "**RECOMMENDATION**: The persistence layer has a mix of raw SQL and ORM usage. "
                "Review the **Access Taxonomy** table above to identify which specific files are still "
                "using raw SQL - those are worth examining in the **Risk Audit** tab."
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 - Risk Audit
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        st.markdown("#### Security Risk: Hardcoded Credentials")
        st.caption("Files where DB credentials appear as literal strings inside connection calls.")
        if creds:
            st.dataframe(pd.DataFrame(creds), hide_index=True, use_container_width=True)
        else:
            st.success("No hardcoded credentials detected.", icon=":material/check_circle:")

        st.markdown("#### Performance Risk: Duplicate Queries")
        st.caption("Identical SQL strings copy-pasted across multiple files - increases maintenance surface area.")
        if dups:
            display_dups = []
            for d in dups:
                row = dict(d)
                if isinstance(row.get("files"), list):
                    row["files"] = ", ".join(row["files"])
                display_dups.append(row)
            st.dataframe(pd.DataFrame(display_dups), hide_index=True, use_container_width=True)
        else:
            st.success("No duplicated SQL queries detected.", icon=":material/check_circle:")

        st.markdown("#### Logic Risk: Unguarded Writes")
        st.caption("Files that execute INSERT/UPDATE/DELETE outside of a transaction block.")
        if no_tx:
            st.dataframe(pd.DataFrame(no_tx), hide_index=True, use_container_width=True)
        else:
            st.success("Transaction integrity verified across all write operations.", icon=":material/check_circle:")

        if sprocs:
            st.markdown("#### Stored Procedures / EXEC Calls")
            st.caption("Direct stored procedure calls - business logic that lives outside the application layer.")
            st.dataframe(pd.DataFrame(sprocs), hide_index=True, use_container_width=True)

        # ── Tab-specific Insight ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style="background-color: rgba(33,195,84,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Persistence Risk Intelligence</h4>
            <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Composite persistence vulnerability count and unhandled transactions.</span></div>
        </div>
        """, unsafe_allow_html=True)
        if total_risk_items > 0:
            st.warning(f"{total_risk_items} persistence risk item(s) detected credential, duplicate query, or transaction issues present.", icon=":material/warning:")
        else:
            st.success("Persistence risk profile is clean no credential, duplicate, or transaction risks detected.", icon=":material/check_circle:")

        st.markdown("**METRIC**: Composite Persistence Vulnerability Count")
        st.markdown(
            "**INTERPRETATION**: This section breaks down three distinct risk categories that affect "
            "database interactions. Credential leaks reflect how credentials are managed in the codebase. "
            "Duplicate queries reflect the degree of code reuse in the persistence layer. "
            "Unguarded writes reflect how write atomicity is handled - whether failures can leave "
            "the database in a partial state."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. `{len(creds)}` hardcoded credential instance(s) detected.\n"
            f"2. `{len(dups)}` duplicate SQL query pattern(s) found across multiple files.\n"
            f"3. `{len(no_tx)}` write-heavy file(s) operate outside transaction boundaries.\n"
            f"4. `{len(sprocs)}` stored procedure call(s) found."
        )
        if total_risk_items > 0:
            st.markdown(
                "**RECOMMENDATION**: Cross-reference the files listed above with the **Access Taxonomy** tab "
                "to see which modules carry the highest combined read/write volume alongside these risks - "
                "those files represent the most complex persistence hotspots in the system."
            )
        else:
            st.markdown(
                "**RECOMMENDATION**: The persistence risk profile is clean for this run. "
                "Proceed to the **Table Ownership** tab to assess whether database tables are "
                "properly isolated to individual modules."
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 - Table Ownership
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Table Ownership by Bounded Context")
        st.caption("Shows which architectural domain (folder/module) is the primary writer to each database table.")

        if ownership:
            df_own = pd.DataFrame(ownership)
            display_cols = [c for c in ["table", "primary_owner", "total_writes", "cross_module_write"] if c in df_own.columns]
            st.dataframe(
                df_own[display_cols],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "cross_module_write": st.column_config.CheckboxColumn("Cross-Module Conflict"),
                    "total_writes": st.column_config.NumberColumn("Total Writes"),
                }
            )
        else:
            st.info(
                "No table ownership data inferred for this run. "
                "This occurs when no INSERT/UPDATE/DELETE statements with recognizable table names are found."
            )

        # ── Tab-specific Insight ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style="background-color: rgba(255,193,7,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Data Entanglement Intelligence</h4>
            <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Cross-module write conflicts and shared table access analysis.</span></div>
        </div>
        """, unsafe_allow_html=True)
        if cross_module:
            st.warning(f"{len(cross_module)} table(s) written to by more than one module cross-module write conflicts detected.", icon=":material/warning:")
        else:
            st.info("All tables have a single identified primary owner no cross-module write conflicts.", icon=":material/info:")

        st.markdown("**METRIC**: Cross-Module Write Operations (Shared Table Access)")
        st.markdown(
            "**INTERPRETATION**: This metric measures how many database tables are written to by "
            "more than one architectural module. Each shared table represents a point of implicit "
            "coupling between modules - changes to that table's schema will ripple across every "
            "module that writes to it. The `primary_owner` column identifies which module has the "
            "highest write volume to that table."
        )
        if cross_module:
            affected = ", ".join([f"`{t['table']}`" for t in cross_module[:5]])
            extra = f" and {len(cross_module) - 5} more" if len(cross_module) > 5 else ""
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. `{len(cross_module)}` table(s) are written to by more than one module: {affected}{extra}.\n"
                f"2. `{len(ownership) - len(cross_module)}` table(s) have clean single-owner boundaries.\n"
                f"3. Check the `write_contexts` column in the raw data for the full ownership breakdown."
            )
            st.markdown(
                "**RECOMMENDATION**: Cross-reference the flagged tables with the **Access Taxonomy** tab "
                "to identify which modules have the highest write volume to these shared tables"
                "those modules are the primary candidates for data boundary refactoring."
            )
        else:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. `{len(ownership)}` table(s) analysed - all have a single identified primary owner.\n"
                f"2. No cross-module write conflicts detected in this run."
            )
            st.markdown(
                "**RECOMMENDATION**: Proceed to the **Risk Audit** tab to verify there are no "
                "credential risks or unguarded writes associated with these cleanly bounded tables."
            )


if __name__ == "__main__":
    show_database_intelligence()
