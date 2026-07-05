import streamlit as st
import requests
import pandas as pd
import os
from views import page_registry

def show_global_state_intelligence():
    st.title("Runtime & Global State Intelligence")
    st.markdown("##### Superglobal Tracking · Session Flows · Side-Effect Classification")

    with st.expander("About Global State Intelligence", expanded=True):
        st.markdown("""
        This view exposes how the application **shares data invisibly** across its modules.
        Legacy PHP systems rely heavily on superglobals (`$_SESSION`, `$_POST`, `$_GET`), the
        `global` keyword, and implicit side effects to pass state between files.
        
        Because this data flow is **not typed, not declared, and not visible to static analysis tools**,
        it is one of the primary reasons legacy PHP monoliths are difficult to test, refactor, or split.
        Use this view to map where hidden state dependencies exist before making any extraction decisions.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    @st.cache_data(ttl=60)
    def fetch_data(rid):
        res = requests.get(f"{FASTAPI_URL}/global-state/{rid}", timeout=30)
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_data(run_id)
    if not data:
        st.error("Could not retrieve global state intelligence data.")
        return

    sg_totals   = data.get("superglobal_totals", {})
    mutations   = data.get("superglobal_mutations", [])
    sess_write  = data.get("session_writers", [])
    sess_read   = data.get("session_readers", [])
    sess_keys   = data.get("session_key_flow", [])
    explicit_g  = data.get("explicit_globals", [])
    se_totals   = data.get("side_effect_totals", {})
    se_files    = data.get("top_side_effect_files", [])
    danger      = data.get("danger_sinks", [])
    legacy_hash = data.get("legacy_hash_usages", [])

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Superglobal Hits",     sum(sg_totals.values()))
    k2.metric("State Mutations",      len(mutations))
    k3.metric("Session Writers",      len(sess_write))
    k4.metric("Danger Sinks",         se_totals.get("DANGER", 0))
    k5.metric("Weak Hash (MD5/SHA1)", len(legacy_hash))

    st.markdown("---")

    tabs = st.tabs([
        "Superglobal Map",
        "Session Flows",
        "Side-Effect Registry",
        "Explicit Globals",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 — Superglobal Map
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### Superglobal Usage Distribution")
        st.caption("Total access count per superglobal variable across the entire codebase.")
        if sg_totals:
            df_sg = pd.DataFrame([
                {"Variable": f"${k}", "Total Usages": v}
                for k, v in sorted(sg_totals.items(), key=lambda x: -x[1])
            ])
            st.dataframe(df_sg, hide_index=True, use_container_width=True)
        else:
            st.info("No superglobal accesses detected.")

        st.markdown("#### State Mutation Records")
        st.caption("Specific lines where a superglobal is directly written to (not just read).")
        if mutations:
            st.dataframe(pd.DataFrame(mutations), hide_index=True, use_container_width=True)
        else:
            st.success("No direct superglobal mutations detected.", icon=":material/check_circle:")

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        total_sg = sum(sg_totals.values())
        top_sg   = max(sg_totals, key=sg_totals.get) if sg_totals else None

        st.info("#### Superglobal Coupling")
        st.markdown("**METRIC**: Total superglobal accesses across all modules")
        st.markdown(
            "**INTERPRETATION**: Every access to `$_POST`, `$_GET`, `$_SESSION`, or similar variables "
            "creates an **invisible data dependency** between the HTTP request context and the file "
            "reading it. Unlike function parameters or constructor arguments, this coupling is not "
            "declared in any type signature — it exists only at runtime. This makes it undetectable "
            "by standard static analysis or IDE refactoring tools."
        )
        if total_sg > 0:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. `{total_sg}` total superglobal accesses detected across the codebase.\n"
                f"2. Most accessed: `${top_sg}` with `{sg_totals.get(top_sg, 0)}` usages.\n"
                f"3. `{len(mutations)}` direct write mutations recorded — "
                f"these are the points where state is *created*, not just consumed."
            )
            st.markdown(
                "**RECOMMENDATION**: Cross-reference the most accessed superglobal (`$" + str(top_sg) + "`) "
                "with the **Session Flows** tab to see whether its writes and reads are distributed "
                "across many files or concentrated in a few."
            )
        else:
            st.markdown("**EVIDENCE**: No superglobal accesses detected in this run.")
            st.markdown(
                "**RECOMMENDATION**: If superglobal access is expected, verify the scan covered "
                "the correct entry point files by reviewing the **Monolith Navigator**."
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 — Session Flows
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Session Writers (State Producers)")
            st.caption("Files that actively mutate `$_SESSION` — they create or update session state.")
            if sess_write:
                st.dataframe(pd.DataFrame(sess_write), hide_index=True, use_container_width=True)
            else:
                st.info("No session-writing files detected.")

        with c2:
            st.markdown("#### Session Readers (State Consumers)")
            st.caption("Files that access `$_SESSION` without writing to it — they depend on state set elsewhere.")
            if sess_read:
                st.dataframe(pd.DataFrame(sess_read), hide_index=True, use_container_width=True)
            else:
                st.info("No session-consuming files detected.")

        # ── Session Key Flow Table ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Session Key Flow (Write → Read Tracing)")
        st.caption(
            "Key-level tracing: shows exactly which key inside `$_SESSION`, `$_POST`, etc. "
            "is written by which file and read by which file. Requires a re-scan to populate."
        )
        if sess_keys:
            df_keys = pd.DataFrame(sess_keys)
            st.dataframe(
                df_keys,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "direction": st.column_config.TextColumn("Direction"),
                    "variable":  st.column_config.TextColumn("Variable[Key]"),
                    "key":       st.column_config.TextColumn("Key Name"),
                    "file":      st.column_config.TextColumn("File"),
                    "line":      st.column_config.NumberColumn("Line"),
                }
            )
        else:
            st.info(
                "No key-level session accesses detected yet. "
                "This table populates after a re-scan with the updated parser — "
                "it will show entries like `$_SESSION['user']` WRITE in `login.php`, "
                "READ in `dashboard.php`."
            )

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        st.info("#### Session Flow Analysis")
        st.markdown("**METRIC**: Session Writer/Reader Distribution")
        st.markdown(
            "**INTERPRETATION**: Session state in PHP flows **one-directionally but invisibly** — "
            "a file sets a value into `$_SESSION`, and a completely different file reads it later "
            "in the request lifecycle. This creates a **temporal coupling**: the reader will silently "
            "fail or behave incorrectly if the writer has not run first. "
            "The ratio of writers to readers indicates how concentrated or distributed session management is."
        )
        total_session = len(sess_write) + len(sess_read)
        if total_session > 0:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. `{len(sess_write)}` file(s) actively write to `$_SESSION` (producers).\n"
                f"2. `{len(sess_read)}` file(s) read from `$_SESSION` without writing (consumers).\n"
                f"3. Session usage is detected across `{total_session}` file(s) in total."
            )
            st.markdown(
                "**RECOMMENDATION**: Review the writer file(s) listed above alongside the "
                "**Superglobal Map** tab mutation records — together they show the full picture "
                "of where session state originates in the application."
            )
        else:
            st.markdown(
                "**EVIDENCE**: No `$_SESSION` usage detected in this run.\n\n"
                "**RECOMMENDATION**: If session handling is expected, check the **Superglobal Map** "
                "tab to confirm whether `$_SESSION` appears in the usage distribution table."
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 — Side-Effect Registry
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Side-Effect Type Breakdown")
        st.caption("Classification of all detected side effects — operations that interact with systems outside the application's own memory.")
        if se_totals:
            df_se = pd.DataFrame([
                {"Type": k, "Count": v}
                for k, v in se_totals.items() if v > 0
            ]).sort_values("Count", ascending=False)
            st.dataframe(df_se, hide_index=True, use_container_width=True)

        st.markdown("#### Top Files by Side-Effect Volume")
        st.caption("Files with the highest concentration of side-effecting operations — the most behaviourally complex files in the system.")
        if se_files:
            st.dataframe(pd.DataFrame(se_files), hide_index=True, use_container_width=True)

        st.markdown("#### Danger Sink Locations (eval / exec / extract)")
        st.caption("Functions that execute arbitrary code or inject variables into the current scope from external data.")
        if danger:
            st.dataframe(pd.DataFrame(danger), hide_index=True, use_container_width=True)
        else:
            st.success("No `eval()` / `exec()` / `extract()` danger sinks detected.", icon=":material/check_circle:")

        st.markdown("#### Weak Cryptography (MD5 / SHA1)")
        st.caption("Usage of cryptographic functions that are no longer considered secure for password hashing.")
        if legacy_hash:
            st.dataframe(pd.DataFrame(legacy_hash), hide_index=True, use_container_width=True)
        else:
            st.success("No legacy hashing functions detected.", icon=":material/check_circle:")

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        dominant_effect = max(se_totals, key=se_totals.get) if se_totals else None
        dominant_count  = se_totals.get(dominant_effect, 0) if dominant_effect else 0

        st.info("#### Behavioural Complexity Profile")
        st.markdown("**METRIC**: Side-Effect Classification Distribution")
        st.markdown(
            "**INTERPRETATION**: Side effects classify what the system *does beyond returning values* — "
            "writes to files (`IO`), makes network calls (`NET`), interacts with databases (`DB`), "
            "renders templates (`TEMPLATE`), or modifies runtime state (`HOSTING`). "
            "A system with high side-effect volume concentrated in few files has very high "
            "behavioural complexity — those files are difficult to test in isolation and "
            "risky to modify without understanding their full execution context."
        )
        if dominant_effect:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. Dominant side-effect category: `{dominant_effect}` with `{dominant_count}` occurrences.\n"
                f"2. `{se_totals.get('DANGER', 0)}` dangerous execution sink(s) detected (`eval`/`exec`/`extract`).\n"
                f"3. `{len(legacy_hash)}` weak cryptographic hash usage(s) identified.\n"
                f"4. `{se_totals.get('NET', 0)}` outbound network call(s) detected — external dependency surface."
            )
            st.markdown(
                "**RECOMMENDATION**: Review the **Top Files by Side-Effect Volume** table above — "
                "files appearing at the top of that list with multiple side-effect categories are "
                "the most complex units in the system. Cross-reference these with the **Modernization Risk** "
                "page to see how their behavioural complexity contributes to their overall risk score."
            )
        else:
            st.markdown(
                "**EVIDENCE**: No side effects detected in this run.\n\n"
                "**RECOMMENDATION**: If side effects are expected, verify the scan covered "
                "the application's controller and service files."
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 3 — Explicit Globals
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[3]:
        st.markdown("#### Global Variable Declarations (`global $var`)")
        st.caption("Every use of the `global` keyword — variables pulled from global PHP scope into a local function or method context.")
        if explicit_g:
            st.dataframe(pd.DataFrame(explicit_g), hide_index=True, use_container_width=True)
        else:
            st.success("No explicit `global` keyword usage detected.", icon=":material/check_circle:")

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        unique_vars = list(set(g.get("variable", "") for g in explicit_g))

        if explicit_g:
            st.warning("#### Global State Coupling")
        else:
            st.info("#### Global State Coupling")

        st.markdown("**METRIC**: Explicit Global Variable Injections (`global $var` usage count)")
        st.markdown(
            "**INTERPRETATION**: The `global` keyword in PHP pulls a variable from the global scope "
            "into a function's local scope. Unlike superglobals, these are **application-defined** "
            "shared variables. Every function that declares the same variable as `global` is "
            "implicitly coupled to every other function that does the same — they all share "
            "and can mutate the same value. This coupling is completely invisible to the call graph."
        )
        if explicit_g:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. `{len(explicit_g)}` explicit `global` keyword usage(s) detected.\n"
                f"2. `{len(unique_vars)}` distinct variable(s) are shared through global scope: "
                + ", ".join([f"`{v}`" for v in unique_vars[:5]])
                + (f" and {len(unique_vars) - 5} more." if len(unique_vars) > 5 else ".")
            )
            st.markdown(
                "**RECOMMENDATION**: Cross-reference the variable names listed above with the "
                "**Superglobal Map** tab — if `$GLOBALS` appears there, that is the superglobal-level "
                "equivalent of these explicit declarations, confirming a deeper pattern of "
                "global state reliance across this codebase."
            )
        else:
            st.markdown(
                "**EVIDENCE**: No `global` keyword usage detected in this run. "
                "The codebase does not rely on PHP global scope injection.\n\n"
                "**RECOMMENDATION**: Confirm this by checking the **Superglobal Map** tab — "
                "if `GLOBALS` also shows zero usage there, the codebase is clean of global state coupling."
            )


if __name__ == "__main__":
    show_global_state_intelligence()
