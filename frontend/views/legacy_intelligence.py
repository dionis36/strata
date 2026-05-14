import streamlit as st
import requests
import pandas as pd
import os

def show_legacy_intelligence():
    st.title("Legacy PHP Intelligence")
    st.markdown("##### Era Classification · Pattern Detection · Modernization Scoring")

    with st.expander("💡 About Legacy PHP Intelligence", expanded=True):
        st.markdown("""
        This view is the **expert-system layer** of the platform. It classifies the codebase's
        PHP era based on detected code patterns — from PHP 4 procedural roots through PHP 5
        transitional patterns to modern PHP 7+ architecture.

        Every signal here is derived directly from the AST of your source files.
        The era classification drives the **migration cost estimate** — a PHP 4 codebase
        requires a fundamentally different modernization strategy than a PHP 7 one.
        Use this view before any extraction or migration planning begins.
        """)
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")

    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=60)
    def fetch_data(rid):
        res = requests.get(f"{FASTAPI_URL}/legacy-intelligence/{rid}", timeout=30)
        if res.status_code == 200:
            return res.json()
        return None

    data = fetch_data(run_id)
    if not data:
        st.error("Could not retrieve legacy intelligence data.")
        return

    scores         = data.get("score_dimensions", {})
    era_signals    = data.get("era_signals", [])
    pattern_totals = data.get("pattern_totals", {})
    leg_patterns   = data.get("legacy_patterns", {})
    total_files    = data.get("total_files_scanned", 0)
    proc_ratio     = data.get("procedural_ratio", 0.0)
    ns_ratio       = data.get("namespace_ratio", 0.0)
    vv_count       = data.get("variable_variable_count", 0)
    host_signals   = data.get("hosting_signal_count", 0)
    classified_era = data.get("classified_era", "Unknown")
    mod_score      = scores.get("Total Modernization Score", 0.0)

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🏛️ PHP Era",             classified_era.split("(")[0].strip())
    k2.metric("📊 Modernization Score",  f"{mod_score:.1%}" if mod_score else "N/A")
    k3.metric("🔄 Procedural Ratio",     f"{proc_ratio:.1%}")
    k4.metric("🏷️ Namespace Coverage",   f"{ns_ratio:.1%}")
    k5.metric("⚠️ Era Signals",          len(era_signals))

    st.markdown("---")

    tabs = st.tabs([
        "🏛️ Era Classification",
        "🔍 Pattern Detection",
        "📊 Modernization Scorecard",
        "📁 File Composition",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 — Era Classification
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### PHP Era Signals Detected")
        st.caption(
            "Each signal is a code pattern that is characteristic of a specific PHP era. "
            "Severity reflects how far the pattern is from modern PHP best practices."
        )

        if era_signals:
            df_era = pd.DataFrame(era_signals)
            st.dataframe(
                df_era,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "severity": st.column_config.TextColumn("Severity"),
                    "era":      st.column_config.TextColumn("Estimated Era"),
                    "count":    st.column_config.NumberColumn("Occurrences"),
                    "detail":   st.column_config.TextColumn("Detail"),
                }
            )
        else:
            st.success("No legacy era signals detected. The codebase appears to use modern PHP patterns.")

        st.markdown("---")

        ERA_DESC = {
            "Era A/B (PHP 4 / Early PHP 5)": ("🔴", "Fully procedural, no namespaces, mysql_* API, inline HTML. Pre-OOP era."),
            "Era B/C (PHP 5 Transitional)":  ("🟠", "Mixed OOP and procedural. Some namespaces. Still uses legacy DB or auth patterns."),
            "Era C (PHP 5 Transitional)":    ("🟡", "OOP-dominant but inconsistent. Missing PSR-4, type hints, or framework."),
            "Era D (PHP 7+)":                ("🟢", "Modern. PSR-4 autoloading, type hints, namespaces, OOP-first."),
            "Unknown":                       ("⚪", "Insufficient signals to classify."),
        }
        icon, desc = ERA_DESC.get(classified_era, ("⚪", classified_era))

        st.info(f"#### {icon} Classified Era: {classified_era}")
        st.markdown(f"*{desc}*")
        st.markdown("---")

        # Insight
        critical = sum(1 for s in era_signals if s["severity"] == "CRITICAL")
        high     = sum(1 for s in era_signals if s["severity"] == "HIGH")

        st.info("#### 🏛️ Era Classification Assessment")
        st.markdown("**METRIC**: PHP Era Classification based on AST pattern density")
        st.markdown(
            "**INTERPRETATION**: PHP era classification is not based on the `php_version` file — "
            "it is inferred from the *actual patterns in the source code*. A codebase can declare "
            "PHP 7 as its minimum version while containing exclusively PHP 4-era patterns. "
            "Era classification is the primary input into migration cost estimation: "
            "Era A/B codebases require structural rewrites, while Era C/D codebases can be "
            "iteratively refactored."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. Classified as: **{classified_era}**.\n"
            f"2. `{len(era_signals)}` total era signal(s) detected.\n"
            f"3. `{critical}` CRITICAL and `{high}` HIGH severity signal(s) confirm the classification.\n"
            f"4. Namespace coverage: `{ns_ratio:.1%}` — a key differentiator between Era B and Era C/D."
        )
        st.markdown(
            "**RECOMMENDATION**: Review the **Pattern Detection** tab to see the specific "
            "instances driving this classification — particularly the `MYSQL_LEGACY` and "
            "`INLINE_HTML` entries, which are the strongest indicators of Era A/B origin."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 — Pattern Detection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        PATTERN_META = {
            "MYSQL_LEGACY":               ("🔴", "mysql_*() Family",          "Removed in PHP 7.0 — will crash on modern PHP"),
            "HARDCODED_DB_CREDENTIALS":   ("🔴", "Hardcoded DB Credentials",   "mysql_connect/PDO with literal host/user/pass strings"),
            "REGISTER_GLOBALS_ASSUMPTION":("🔴", "register_globals Assumption","extract() / import_request_variables() usage"),
            "LEGACY_AUTOLOAD":            ("🟠", "__autoload() Usage",          "Deprecated PHP 7.2, removed PHP 8.0"),
            "INCLUDE_ROUTING":            ("🟠", "Dynamic Include Routing",    "include($page) used as a routing mechanism"),
            "INLINE_HTML":                ("🟡", "Inline HTML/PHP Mixing",     "Raw HTML embedded in PHP files — no template layer"),
            "VARIABLE_VARIABLE":          ("🟡", "Variable Variables ($$var)", "Dynamic binding — untraceable by static analysis"),
            "CUSTOM_AUTH":                ("🟡", "Custom Session Save Handler","Non-standard auth flow — risky to migrate"),
        }

        st.markdown("#### Legacy Anti-Pattern Inventory")
        st.caption("Each category represents a distinct type of legacy usage. Expand to see exact file and line locations.")

        if pattern_totals:
            for ptype, count in sorted(pattern_totals.items(), key=lambda x: -x[1]):
                icon, label, explanation = PATTERN_META.get(ptype, ("⚪", ptype, ""))
                with st.expander(f"{icon} **{label}** — {count} occurrence(s)  ·  *{explanation}*", expanded=count > 0):
                    instances = leg_patterns.get(ptype, [])
                    if instances:
                        st.dataframe(pd.DataFrame(instances), hide_index=True, use_container_width=True)
        else:
            st.success("✅ No legacy anti-patterns detected.")

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        total_patterns = sum(pattern_totals.values())
        mysql_count    = pattern_totals.get("MYSQL_LEGACY", 0)
        inline_count   = pattern_totals.get("INLINE_HTML", 0)
        routing_count  = pattern_totals.get("INCLUDE_ROUTING", 0)

        if total_patterns > 0:
            st.warning("#### 🔍 Anti-Pattern Density")
        else:
            st.success("#### 🔍 Anti-Pattern Density")

        st.markdown("**METRIC**: Legacy Anti-Pattern Count by Category")
        st.markdown(
            "**INTERPRETATION**: Each detected pattern type represents a different layer of technical debt. "
            "`MYSQL_LEGACY` patterns mean the DB layer is bound to an extinct PHP extension. "
            "`INLINE_HTML` means there is no separation between business logic and presentation. "
            "`INCLUDE_ROUTING` means the application has no framework routing layer — "
            "every route is a physical file path, making URL refactoring destructive."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. `{total_patterns}` total anti-pattern instance(s) across `{len(pattern_totals)}` distinct categories.\n"
            f"2. `{mysql_count}` `mysql_*()` call(s) — these represent the DB layer refactoring scope.\n"
            f"3. `{inline_count}` inline HTML block(s) — each one mixes template and logic in the same file.\n"
            f"4. `{routing_count}` dynamic include-based routing call(s) — scope of routing refactoring."
        )
        st.markdown(
            "**RECOMMENDATION**: Cross-reference the `MYSQL_LEGACY` file list with the "
            "**Database Intelligence** page — the same files will appear there in the "
            "Access Taxonomy as high write-volume DB files, confirming they are the "
            "core persistence layer candidates for refactoring."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 — Modernization Scorecard
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Technology Stack Profile")
        st.caption("Detected framework, DB layer, auth layer, and template layer from the analysis run.")

        if scores:
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Framework**: `{scores.get('Framework', 'None')}`")
            c2.markdown(f"**DB Layer**: `{scores.get('DB Layer', 'Unknown')}`")
            c3.markdown(f"**Auth Layer**: `{scores.get('Auth Layer', 'Unknown')}`")

            c4, c5 = st.columns(2)
            c4.markdown(f"**Template Layer**: `{scores.get('Template Layer', 'Unknown')}`")
            c5.markdown(f"**Autoloading**: `{scores.get('Autoloading', 'Unknown')}`")
            st.markdown(f"**Hosting Risk**: `{scores.get('Hosting Risk', 'Unknown')}`")
        else:
            st.info("Stack profile not yet computed. This is populated by a full analysis run.")

        st.markdown("---")
        st.markdown("#### Score Dimensions")
        st.caption("Each dimension scores one aspect of modernization readiness on a 0.0 – 1.0 scale.")

        SCORE_DIMS = [
            ("Namespace Score",   "Proportion of files using PHP namespaces — PSR-4 compliance indicator"),
            ("Security Score",    "Inverse of dangerous pattern density — credentials, evals, weak crypto"),
            ("DB Layer Score",    "PDO/ORM usage vs mysql_* — DB abstraction completeness"),
            ("Testability Score", "Presence of class-based structure, interface contracts, and test files"),
            ("Coupling Score",    "Inverse of coupling density — superglobals, globals, cross-file mutations"),
        ]

        if scores:
            score_rows = [{"Dimension": label, "Score": scores.get(label, 0.0), "What it measures": desc}
                          for label, desc in SCORE_DIMS]
            st.dataframe(
                pd.DataFrame(score_rows),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="%.2f"),
                }
            )
        else:
            st.info("Score dimensions not yet available. Run a full analysis to generate scores.")

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        if mod_score > 0:
            bucket = "🟢 Modern (Era D)" if mod_score >= 0.7 else ("🟡 Transitional (Era C)" if mod_score >= 0.4 else "🔴 Legacy (Era A/B)")
            st.info(f"#### 📊 Overall Modernization Readiness: {bucket}")
        else:
            st.info("#### 📊 Overall Modernization Readiness")

        st.markdown("**METRIC**: Composite Modernization Score (0.0 — 1.0)")
        st.markdown(
            "**INTERPRETATION**: This composite score weights five dimensions of code modernity. "
            "It is not a quality score — it is a **migration readiness score**. "
            "A low score does not mean the application doesn't work; it means the effort required "
            "to extract, test, containerize, or migrate it is proportionally higher. "
            "Each dimension targets a distinct refactoring concern: namespace adoption targets PSR-4 compliance, "
            "DB layer score targets the persistence migration path, and coupling score targets testability isolation."
        )
        if mod_score > 0:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. Total modernization score: **{mod_score:.1%}**.\n"
                f"2. Namespace score: `{scores.get('Namespace Score', 0.0):.2f}` — "
                f"reflects how much of the codebase uses PHP namespaces.\n"
                f"3. DB layer score: `{scores.get('DB Layer Score', 0.0):.2f}` — "
                f"reflects the proportion of DB calls using PDO or an ORM vs raw mysql_*."
            )
        else:
            st.markdown(
                "**EVIDENCE**: Modernization scores not yet computed for this run.\n\n"
                "**RECOMMENDATION**: Check the **Era Classification** tab for signal-based scores "
                "that are derived directly from the AST without requiring a full LegacyMetrics run."
            )
        st.markdown(
            "**RECOMMENDATION**: Review the lowest-scoring dimensions above and cross-reference "
            "with the **Pattern Detection** tab — the files driving the low scores will appear "
            "there under the corresponding pattern category."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 3 — File Composition
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[3]:
        st.markdown("#### Codebase Structural Composition")
        st.caption("Distribution of file types by architectural structure — OOP, namespace-aware, or procedural.")

        comp_data = [
            {"Category": "Total Files Scanned",                          "Count": total_files},
            {"Category": "OOP Files (has at least one class)",           "Count": data.get("files_with_classes", 0)},
            {"Category": "Namespace-aware Files",                        "Count": data.get("files_namespace_aware", 0)},
            {"Category": "Procedural-only Files (functions, no classes)", "Count": data.get("files_procedural_only", 0)},
            {"Category": "Variable Variable Usages ($$var files)",        "Count": vv_count},
            {"Category": "Files with Hosting Assumption Calls",           "Count": host_signals},
        ]
        st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

        # ── Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        oop_count = data.get("files_with_classes", 0)
        proc_only = data.get("files_procedural_only", 0)

        st.info("#### 📁 Structural Composition Profile")
        st.markdown("**METRIC**: OOP vs Procedural Distribution")
        st.markdown(
            "**INTERPRETATION**: This table shows the raw structural split of the codebase. "
            "Files with classes can potentially be unit-tested in isolation. "
            "Procedural-only files (functions but no classes) require wrapping before testing. "
            "Files with neither classes nor functions are typically configuration, bootstrap, "
            "or entry-point files. "
            "Namespace-aware files are compatible with PSR-4 autoloading — a prerequisite for Composer-based modernization."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. `{proc_ratio:.1%}` of scanned files are procedural (no class definitions) — `{total_files - oop_count}` file(s).\n"
            f"2. `{ns_ratio:.1%}` of files use PHP namespaces — `{data.get('files_namespace_aware', 0)}` file(s).\n"
            f"3. `{proc_only}` file(s) have standalone functions but no classes — these are refactoring candidates.\n"
            f"4. `{host_signals}` file(s) contain hosting assumption calls (ini_set, header, set_time_limit)."
        )
        st.markdown(
            "**RECOMMENDATION**: The `{proc_only}` procedural function files are the primary target "
            "for wrapping into stateless service classes. Review them against the **Pattern Detection** tab — "
            "those containing `MYSQL_LEGACY` or `INLINE_HTML` are the highest-priority refactoring candidates."
        )


if __name__ == "__main__":
    show_legacy_intelligence()
