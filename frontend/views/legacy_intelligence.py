import streamlit as st
import requests
import pandas as pd
import os
from views import page_registry
from views.severity import SEVERITY_CRITICAL, SEVERITY_HIGH

def show_legacy_intelligence():
    st.title("Legacy PHP Intelligence")
    st.markdown("##### Era Classification · Pattern Detection · Modernization Scoring")

    with st.expander("Legacy PHP Intelligence Blueprint Key", expanded=True):
        colA, colB = st.columns(2)
        with colA:
            st.markdown("""
            **PHP Era Diagnostics**
            - **Era A/B (PHP 4/5)**: Highly procedural, globally coupled.
            - **Era C (PHP 5 Transitional)**: Mixed OOP, lacking PSR standards.
            - **Era D (PHP 7+)**: Modern structured code.
            - **Bespoke / Custom Era**: Proprietary or in-house framework built without modern standard libraries.
            """)
        with colB:
            st.markdown("""
            **Legacy Anti-Patterns**
            - **MYSQL_LEGACY**: Unsafe legacy driver calls.
            - **VARIABLE_VARIABLE**: Untraceable dynamic dispatch (`$$var`).
            - **INLINE_HTML**: Presentation logic tightly coupled with business logic.
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
    classified_era = data.get("classified_era", "Unknown")
    mod_score      = scores.get("Total Modernization Score", 0.0)

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(
        "PHP Era",
        classified_era.split("(")[0].strip(),
        help="The detected PHP generation of this codebase, inferred from actual source code patterns — not the declared php version. Era A/B (PHP 4/5) = fully procedural, globally coupled. Era D (PHP 7+) = modern, namespace-aware, OOP-first."
    )
    k2.metric(
        "Modernization Score",
        f"{mod_score:.1%}" if mod_score else "N/A",
        help="A composite 0.0–1.0 readiness score weighted across 5 dimensions: namespace adoption, security posture, DB abstraction level, testability, and coupling density. This is a migration cost estimator — not a quality score. Higher = easier to modernize."
    )
    k3.metric(
        "Procedural Ratio",
        f"{proc_ratio:.1%}",
        help="The percentage of files that contain no class definitions — purely function-based or script-based code. High ratios indicate a pre-OOP architecture requiring significant structural wrapping before containerization is possible."
    )
    k4.metric(
        "Namespace Coverage",
        f"{ns_ratio:.1%}",
        help="The percentage of files that declare a PHP namespace. Namespace adoption is the minimum prerequisite for PSR-4 autoloading, which is required for Composer-based dependency management and modern framework integration."
    )
    k5.metric(
        "Era Signals",
        len(era_signals),
        help="The total count of code patterns detected that are characteristic of a specific PHP era. A higher signal count increases classification confidence. Expand the Era Classification tab to see each individual signal."
    )

    st.markdown("---")

    tabs = st.tabs([
        f"Era & Pattern Analysis ({len(era_signals)})",
        f"Modernization Scorecard ({len(scores) if scores else 0})",
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 - Era Classification
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
            "Era A/B (PHP 4 / Early PHP 5)": ("", "Fully procedural, no namespaces, mysql_* API, inline HTML. Pre-OOP era."),
            "Era B/C (PHP 5 Transitional)":  ("", "Mixed OOP and procedural. Some namespaces. Still uses legacy DB or auth patterns."),
            "Era C (PHP 5 Transitional)":    ("", "OOP-dominant but inconsistent. Missing PSR-4, type hints, or framework."),
            "Era D (PHP 7+)":                ("", "Modern. PSR-4 autoloading, type hints, namespaces, OOP-first."),
            "Bespoke / Custom Era":          ("", "A proprietary or custom-built framework. The system relies on internal conventions rather than standard open-source framework patterns (like Laravel or Symfony)."),
            "Unknown":                       ("", "Insufficient signals to classify."),
        }
        icon, desc = ERA_DESC.get(classified_era, ("", classified_era))

        st.markdown(f"#### Classified Era: {classified_era}")
        st.info(f"{desc}", icon=":material/info:")
        st.markdown("---")

        PATTERN_META = {
            "MYSQL_LEGACY":               ("", "mysql_*() Family",          "Removed in PHP 7.0 - will crash on modern PHP"),
            "HARDCODED_DB_CREDENTIALS":   ("", "Hardcoded DB Credentials",   "mysql_connect/PDO with literal host/user/pass strings"),
            "REGISTER_GLOBALS_ASSUMPTION":("", "register_globals Assumption","extract() / import_request_variables() usage"),
            "LEGACY_AUTOLOAD":            ("", "__autoload() Usage",          "Deprecated PHP 7.2, removed PHP 8.0"),
            "INCLUDE_ROUTING":            ("", "Dynamic Include Routing",    "include($page) used as a routing mechanism"),
            "INLINE_HTML":                ("", "Inline HTML/PHP Mixing",     "Raw HTML embedded in PHP files - no template layer"),
            "VARIABLE_VARIABLE":          ("", "Variable Variables ($$var)", "Dynamic binding - untraceable by static analysis"),
            "CUSTOM_AUTH":                ("", "Custom Session Save Handler","Non-standard auth flow - risky to migrate"),
        }

        st.markdown("#### Legacy Anti-Pattern Inventory (Raw Evidence Logs)")
        st.caption("Each category represents a distinct type of legacy usage driving the era classification above. Expand to see exact file locations.")

        if pattern_totals:
            for ptype, count in sorted(pattern_totals.items(), key=lambda x: -x[1]):
                icon, label, explanation = PATTERN_META.get(ptype, ("", ptype, ""))
                with st.expander(f"{icon} **{label}** - {count} occurrence(s)  ·  *{explanation}*", expanded=count > 0):
                    instances = leg_patterns.get(ptype, [])
                    if instances:
                        st.dataframe(pd.DataFrame(instances), hide_index=True, use_container_width=True)
        else:
            st.success("No legacy anti-patterns detected.", icon=":material/check_circle:")

        # ── Unified Insight ──────────────────────────────────────────────────────
        st.markdown("---")
        critical = sum(1 for s in era_signals if str(s.get("severity", "")).upper() == SEVERITY_CRITICAL)
        high     = sum(1 for s in era_signals if str(s.get("severity", "")).upper() == SEVERITY_HIGH)
        total_patterns = sum(pattern_totals.values())
        mysql_count    = pattern_totals.get("MYSQL_LEGACY", 0)
        inline_count   = pattern_totals.get("INLINE_HTML", 0)
        routing_count  = pattern_totals.get("INCLUDE_ROUTING", 0)

        st.markdown("""
        <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Era & Anti-Pattern Intelligence</h4>
            <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">PHP Era Classification based on AST pattern density and detected technical debt.</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**METRIC**: PHP Era Classification & Legacy Anti-Pattern Count")
        st.markdown(
            "**INTERPRETATION**: PHP era classification is inferred directly from the legacy anti-patterns "
            "detected in the codebase (the inventory above). Each detected pattern represents a specific layer "
            "of technical debt. For instance, `MYSQL_LEGACY` locks the DB layer to an extinct PHP extension, "
            "while `INLINE_HTML` eliminates the separation between business logic and presentation. "
            "Era A/B codebases typically require structural rewrites, while Era C/D codebases can be iteratively refactored."
        )
        st.markdown(
            f"**EVIDENCE**:\n"
            f"1. Overall Classification: **{classified_era}**.\n"
            f"2. `{len(era_signals)}` total era signal(s) detected, including `{critical}` CRITICAL and `{high}` HIGH severity signals.\n"
            f"3. `{total_patterns}` total anti-pattern instance(s) found across `{len(pattern_totals)}` distinct categories.\n"
            f"4. Specifically, `{mysql_count}` `mysql_*()` call(s) and `{inline_count}` inline HTML block(s) detected.\n"
            f"5. Namespace coverage: `{ns_ratio:.1%}` - a key differentiator between Era B and Era C/D."
        )
        st.markdown(
            "**RECOMMENDATION**: Cross-reference the `MYSQL_LEGACY` file list with the "
            "**Database Intelligence** page - the same files will appear there in the "
            "Access Taxonomy as high write-volume DB files, confirming they are the "
            "core persistence layer candidates for structural rewrites."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 - Modernization Scorecard
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
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
        st.caption("Each dimension scores one aspect of modernization readiness on a 0.0 - 1.0 scale.")

        SCORE_DIMS = [
            ("Namespace Score",   "Proportion of files using PHP namespaces - PSR-4 compliance indicator"),
            ("Security Score",    "Inverse of dangerous pattern density - credentials, evals, weak crypto"),
            ("DB Layer Score",    "PDO/ORM usage vs mysql_* - DB abstraction completeness"),
            ("Testability Score", "Presence of class-based structure, interface contracts, and test files"),
            ("Coupling Score",    "Inverse of coupling density - superglobals, globals, cross-file mutations"),
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
        st.markdown("#### Overall Modernization Readiness")
        if mod_score > 0:
            bucket = "Modern (Era D)" if mod_score >= 0.7 else ("Transitional (Era C)" if mod_score >= 0.4 else "Legacy (Era A/B)")
            st.info(f"Composite score: **{mod_score:.1%}** — classified as **{bucket}**.", icon=":material/info:")
        else:
            st.info("Modernization score not yet computed for this run.", icon=":material/info:")

        st.markdown("**METRIC**: Composite Modernization Score (0.0 - 1.0)")
        st.markdown(
            "**INTERPRETATION**: This composite score weights five dimensions of code modernity. "
            "It is not a quality score - it is a **migration readiness score**. "
            "A low score does not mean the application doesn't work; it means the effort required "
            "to extract, test, containerize, or migrate it is proportionally higher. "
            "Each dimension targets a distinct refactoring concern: namespace adoption targets PSR-4 compliance, "
            "DB layer score targets the persistence migration path, and coupling score targets testability isolation."
        )
        if mod_score > 0:
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. Total modernization score: **{mod_score:.1%}**.\n"
                f"2. Namespace score: `{scores.get('Namespace Score', 0.0):.2f}` - "
                f"reflects how much of the codebase uses PHP namespaces.\n"
                f"3. DB layer score: `{scores.get('DB Layer Score', 0.0):.2f}` - "
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
            "with the **Pattern Detection** tab - the files driving the low scores will appear "
            "there under the corresponding pattern category."
        )




if __name__ == "__main__":
    show_legacy_intelligence()
