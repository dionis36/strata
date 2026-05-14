import streamlit as st
import requests
import pandas as pd
import os

def show_global_state_intelligence():
    st.title("Runtime & Global State Intelligence")
    st.markdown("### Superglobal Tracking · Session Flows · Side-Effect Classification")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
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
    explicit_g  = data.get("explicit_globals", [])
    se_totals   = data.get("side_effect_totals", {})
    se_files    = data.get("top_side_effect_files", [])
    danger      = data.get("danger_sinks", [])
    legacy_hash = data.get("legacy_hash_usages", [])

    # --- Top Metrics ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("⚡ Superglobal Hits",  sum(sg_totals.values()))
    k2.metric("✏️ State Mutations",   len(mutations))
    k3.metric("🔐 Session Writers",   len(sess_write))
    k4.metric("☠️ Danger Sinks",      se_totals.get("DANGER", 0))
    k5.metric("🔑 Weak Hash (MD5/SHA1)", len(legacy_hash))

    st.markdown("---")

    tabs = st.tabs([
        "📡 Superglobal Map",
        "🔐 Session Flows",
        "☠️ Side-Effect Registry",
        "🌐 Explicit Globals",
    ])

    # ── Tab 0: Superglobal Map ──────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### Superglobal Usage Distribution")
        if sg_totals:
            df_sg = pd.DataFrame([{"Variable": f"${k}", "Total Usages": v}
                                   for k, v in sorted(sg_totals.items(), key=lambda x: -x[1])])
            st.dataframe(df_sg, hide_index=True, use_container_width=True)
        else:
            st.info("No superglobal accesses detected.")

        st.markdown("#### State Mutation Records")
        if mutations:
            st.dataframe(pd.DataFrame(mutations), hide_index=True, use_container_width=True)
        else:
            st.success("No direct superglobal mutations detected.")

        st.markdown("---")
        total_sg = sum(sg_totals.values())
        top_sg = max(sg_totals, key=sg_totals.get) if sg_totals else None
        if total_sg > 0:
            st.warning("#### ⚡ Superglobal Coupling Risk")
            st.markdown("**METRIC**: Total superglobal accesses across all modules")
            st.markdown("**INTERPRETATION**: Each `$_POST`, `$_SESSION`, or `$_GET` access creates an implicit coupling. These cannot be traced by a type system, making the data flow invisible to refactoring tools.")
            st.markdown(f"**EVIDENCE**:\n1. {total_sg} total superglobal accesses detected.\n2. Most used: `${top_sg}` with {sg_totals.get(top_sg, 0)} usages.\n3. {len(mutations)} direct state mutations found.")
            st.markdown("**RECOMMENDATION**: Inject a `RequestContext` or `SessionContext` object at bootstrap and replace direct superglobal access. This makes all data flow explicit and type-safe.")
        else:
            st.success("#### ⚡ Superglobal Coupling Risk\nNo superglobal coupling detected. Clean architecture signal.")

    # ── Tab 1: Session Flows ─────────────────────────────────────────────
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📝 Session Writers (State Producers)")
            if sess_write:
                st.dataframe(pd.DataFrame(sess_write), hide_index=True, use_container_width=True)
            else:
                st.info("No session-writing files detected.")
        with c2:
            st.markdown("#### 📖 Session Readers (State Consumers)")
            if sess_read:
                st.dataframe(pd.DataFrame(sess_read), hide_index=True, use_container_width=True)
            else:
                st.info("No session-consuming files detected.")

        st.markdown("---")
        if sess_write:
            st.warning("#### 🔐 Session Flow Analysis")
            st.markdown("**METRIC**: Session Writer/Reader Asymmetry")
            st.markdown("**INTERPRETATION**: In legacy PHP, `$_SESSION` acts as a hidden shared-state bus. When many modules write to session, state mutations become untraceable, causing ghost bugs and login instability.")
            st.markdown(f"**EVIDENCE**:\n1. {len(sess_write)} file(s) write to `$_SESSION`.\n2. {len(sess_read)} file(s) consume session state.\n3. Ratio of producers to consumers: {len(sess_write)}/{len(sess_read) or 1:.1f}.")
            st.markdown("**RECOMMENDATION**: Centralize all session writes into a single `AuthSessionManager`. All reads should go through that class, not direct `$_SESSION` access.")

    # ── Tab 2: Side-Effect Registry ──────────────────────────────────────
    with tabs[2]:
        st.markdown("#### Side-Effect Type Breakdown")
        if se_totals:
            df_se = pd.DataFrame([{"Type": k, "Count": v} for k, v in se_totals.items() if v > 0]).sort_values("Count", ascending=False)
            st.dataframe(df_se, hide_index=True, use_container_width=True)

        st.markdown("#### Top Files by Side-Effect Volume")
        if se_files:
            st.dataframe(pd.DataFrame(se_files), hide_index=True, use_container_width=True)

        st.markdown("#### ☠️ Danger Sink Locations (eval/exec/extract)")
        if danger:
            st.dataframe(pd.DataFrame(danger), hide_index=True, use_container_width=True)
        else:
            st.success("No `eval()` / `exec()` / `extract()` danger sinks detected.")

        st.markdown("#### 🔑 Weak Cryptography (MD5 / SHA1)")
        if legacy_hash:
            st.dataframe(pd.DataFrame(legacy_hash), hide_index=True, use_container_width=True)
        else:
            st.success("No legacy hashing functions detected.")

        st.markdown("---")
        danger_count = se_totals.get("DANGER", 0)
        if danger_count > 0:
            st.error("#### ☠️ Execution Risk Assessment")
            st.markdown("**METRIC**: Dangerous Code Execution Sinks")
            st.markdown("**INTERPRETATION**: `eval()`, `extract()`, and `exec()` are code-execution vectors. A single unsanitized input reaching these functions equals Remote Code Execution (RCE).")
            st.markdown(f"**EVIDENCE**: {danger_count} dangerous execution sink(s) confirmed across {len(set(d['file'] for d in danger))} file(s).")
            st.markdown("**RECOMMENDATION**: IMMEDIATE ACTION. Remove all `eval()` and `extract()` calls. Replace with explicit assignments and dedicated parsing logic. Each of these is a CVE waiting to be exploited.")
        else:
            st.success("#### ☠️ Execution Risk Assessment\nNo dangerous execution sinks detected.")

    # ── Tab 3: Explicit Globals ──────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### Global Variable Declarations (`global $var`)")
        if explicit_g:
            st.dataframe(pd.DataFrame(explicit_g), hide_index=True, use_container_width=True)
        else:
            st.success("No explicit `global` keyword usage detected.")

        st.markdown("---")
        if explicit_g:
            st.warning("#### 🌐 Global State Coupling")
            st.markdown("**METRIC**: Explicit Global Variable Injections")
            st.markdown("**INTERPRETATION**: The `global $var` keyword creates invisible shared state between functions. When a variable is declared global, any function can mutate it silently, making testing and refactoring nearly impossible.")
            st.markdown(f"**EVIDENCE**: {len(explicit_g)} explicit global variable declarations found.")
            st.markdown("**RECOMMENDATION**: Replace global variables with dependency injection. Pass required data as function/constructor arguments instead of relying on global scope.")

if __name__ == "__main__":
    show_global_state_intelligence()
