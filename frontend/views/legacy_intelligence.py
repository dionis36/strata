import streamlit as st
import requests
import pandas as pd
import os

def show_legacy_intelligence():
    st.title("Legacy PHP Intelligence")
    st.markdown("### Era Classification · Pattern Detection · Modernization Scoring")
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

    scores          = data.get("score_dimensions", {})
    era_signals     = data.get("era_signals", [])
    pattern_totals  = data.get("pattern_totals", {})
    legacy_patterns = data.get("legacy_patterns", {})
    total_files     = data.get("total_files_scanned", 0)
    proc_ratio      = data.get("procedural_ratio", 0.0)
    ns_ratio        = data.get("namespace_ratio", 0.0)
    vv_count        = data.get("variable_variable_count", 0)

    php_era = scores.get("PHP Era", "Unknown")
    mod_score = scores.get("Total Modernization Score", 0.0)

    # ── Top Metrics ───────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🏛️ PHP Era", php_era)
    k2.metric("📊 Modernization Score", f"{mod_score:.1%}")
    k3.metric("🔄 Procedural Ratio", f"{proc_ratio:.1%}")
    k4.metric("🏷️ Namespace Coverage", f"{ns_ratio:.1%}")
    k5.metric("⚠️ Era Signals", len(era_signals))

    st.markdown("---")

    tabs = st.tabs([
        "🏛️ Era Classification",
        "🔍 Pattern Detection",
        "📊 Modernization Scorecard",
        "📁 File Composition",
    ])

    # ── Tab 0: Era Classification ────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### PHP Era Signals Detected")
        if era_signals:
            df_era = pd.DataFrame(era_signals)
            st.dataframe(
                df_era,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "severity": st.column_config.TextColumn("Severity"),
                    "era": st.column_config.TextColumn("Estimated Era"),
                    "count": st.column_config.NumberColumn("Occurrences"),
                }
            )
        else:
            st.success("No legacy era signals detected. Codebase appears to use modern PHP patterns.")

        st.markdown("---")
        era_label_map = {
            "Era A (PHP 4)": "🔴 PHP 4 — Fully Procedural, No OOP, No Namespaces",
            "Era B (PHP 5 Early)": "🟠 PHP 5 Early — Basic OOP, No Namespaces, mysql_* era",
            "Era C (PHP 5 Transitional)": "🟡 PHP 5 Transitional — Namespaces, Composer, Mixed patterns",
            "Era D (PHP 7+)": "🟢 PHP 7+ — Modern. PSR-4, Type Hints, OOP-first",
            "Unknown": "⚪ Unknown — Insufficient signals",
        }
        era_display = era_label_map.get(php_era, f"⚪ {php_era}")
        st.info(f"#### Classified Era: {era_display}")
        st.markdown("**INTERPRETATION**: The PHP era determines the migration cost, tooling compatibility, and refactoring complexity. Era A/B codebases require a fundamentally different modernization approach vs. Era D.")

        if php_era in ("Era A (PHP 4)", "Era B (PHP 5 Early)"):
            st.markdown("**RECOMMENDATION**: Full strangler fig migration recommended. Incrementally wrap legacy modules in modern PHP 8 interfaces. Do NOT attempt a Big Bang rewrite.")
        elif php_era == "Era C (PHP 5 Transitional)":
            st.markdown("**RECOMMENDATION**: Targeted refactoring viable. Introduce strict types, complete namespace adoption, and migrate DB layer to PDO/ORM.")
        else:
            st.markdown("**RECOMMENDATION**: Codebase is in a modern state. Focus on microservice extraction rather than language-level modernization.")

    # ── Tab 1: Pattern Detection ─────────────────────────────────────────
    with tabs[1]:
        st.markdown("#### Legacy Anti-Pattern Inventory")

        PATTERN_LABELS = {
            "LEGACY_AUTOLOAD":           ("🔴", "__autoload() — Deprecated autoloader (PHP 7.2+)"),
            "HARDCODED_DB_CREDENTIALS":  ("🔴", "Hardcoded DB Credentials — mysql_connect/PDO with literal strings"),
            "VARIABLE_VARIABLE":         ("🟠", "Variable Variables ($$var) — Dynamic binding, untraceable"),
            "CUSTOM_AUTH":               ("🟡", "Custom Session Save Handler — Non-standard auth flow"),
        }

        if pattern_totals:
            for ptype, count in sorted(pattern_totals.items(), key=lambda x: -x[1]):
                icon, label = PATTERN_LABELS.get(ptype, ("⚪", ptype))
                with st.expander(f"{icon} {label} — {count} occurrence(s)", expanded=count > 0):
                    instances = legacy_patterns.get(ptype, [])
                    if instances:
                        st.dataframe(pd.DataFrame(instances), hide_index=True, use_container_width=True)
        else:
            st.success("No legacy anti-patterns detected.")

        st.markdown("---")
        total_patterns = sum(pattern_totals.values())
        if total_patterns > 0:
            st.warning("#### 🔍 Anti-Pattern Severity Assessment")
            st.markdown("**METRIC**: Legacy Anti-Pattern Count")
            st.markdown(f"**EVIDENCE**: {total_patterns} total anti-pattern instance(s) across {len(pattern_totals)} distinct categories.")
            st.markdown("**RECOMMENDATION**: Prioritize elimination in this order: ① Hardcoded credentials → ② `__autoload()` → ③ Variable Variables → ④ Custom Session handlers.")
        else:
            st.success("#### 🔍 Anti-Pattern Severity Assessment\nNo legacy anti-patterns detected. The codebase is clean of known high-risk patterns.")

    # ── Tab 2: Modernization Scorecard ───────────────────────────────────
    with tabs[2]:
        st.markdown("#### Modernization Score Dimensions")

        SCORE_KEYS = [
            ("Namespace Score", "namespace_score", "Measures adoption of PSR-4 namespace conventions"),
            ("Security Score", "security_score", "Inverse of dangerous pattern density"),
            ("DB Layer Score", "db_layer_score", "PDO/ORM vs mysql_* usage"),
            ("Testability Score", "testability_score", "Presence of unit tests and interface contracts"),
            ("Coupling Score", "coupling_score", "Inverse of coupling density"),
        ]

        if scores:
            # Quick-look framework summary
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Framework**: `{scores.get('Framework', 'None')}`")
            c2.markdown(f"**DB Layer**: `{scores.get('DB Layer', 'Unknown')}`")
            c3.markdown(f"**Auth Layer**: `{scores.get('Auth Layer', 'Unknown')}`")

            c4, c5 = st.columns(2)
            c4.markdown(f"**Template Layer**: `{scores.get('Template Layer', 'Unknown')}`")
            c5.markdown(f"**Autoloading**: `{scores.get('Autoloading', 'Unknown')}`")

            st.markdown("---")
            st.markdown("#### Score Breakdown")
            score_rows = []
            for label, key, desc in SCORE_KEYS:
                val = scores.get(label, 0.0)
                score_rows.append({"Dimension": label, "Score": val, "Interpretation": desc})
            df_scores = pd.DataFrame(score_rows)
            st.dataframe(
                df_scores,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="%.2f"),
                }
            )
        else:
            st.info("Modernization scores not yet computed. Run a full analysis to generate scores.")

        st.markdown("---")
        if mod_score > 0:
            bucket = "🟢 Modern" if mod_score >= 0.7 else ("🟡 Transitional" if mod_score >= 0.4 else "🔴 Legacy")
            st.info(f"#### 📊 Overall Modernization Readiness: {bucket} ({mod_score:.1%})")
            st.markdown("**INTERPRETATION**: This composite score weights namespace adoption, security posture, DB abstraction, and testability. It serves as the primary readiness gate before service extraction.")
            if mod_score < 0.4:
                st.markdown("**RECOMMENDATION**: Modernization score is critically low. A phased foundational uplift is required before any microservice extraction can safely proceed.")
            elif mod_score < 0.7:
                st.markdown("**RECOMMENDATION**: Targeted improvements in namespace adoption and DB abstraction will raise this score. Extraction is viable for isolated, low-coupling modules.")
            else:
                st.markdown("**RECOMMENDATION**: The codebase is ready for strategic service extraction. Proceed with the Extraction Simulator to identify optimal candidates.")

    # ── Tab 3: File Composition ──────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### Codebase Composition Analysis")

        comp_data = [
            {"Category": "Total Files Scanned", "Count": total_files},
            {"Category": "OOP Files (has classes)", "Count": data.get("files_with_classes", 0)},
            {"Category": "Namespace-aware Files", "Count": data.get("files_namespace_aware", 0)},
            {"Category": "Procedural-only Files (functions, no classes)", "Count": data.get("files_procedural_only", 0)},
            {"Category": "Variable Variable Usages ($$var)", "Count": vv_count},
        ]
        st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

        st.markdown("---")
        st.info("#### 📁 Structural Composition Intelligence")
        st.markdown("**METRIC**: OOP vs Procedural Distribution")
        st.markdown(f"**EVIDENCE**:\n1. `{proc_ratio:.1%}` of files are procedural (no class definitions).\n2. `{ns_ratio:.1%}` of files use PHP namespaces.\n3. {vv_count} variable-variable usages detected.")
        if proc_ratio > 0.5:
            st.markdown("**RECOMMENDATION**: High procedural ratio significantly complicates testing and extraction. Apply the Object Calisthenics refactoring strategy: wrap procedural functions into stateless service classes as an incremental step.")
        else:
            st.markdown("**RECOMMENDATION**: OOP-dominant structure. Focus on enforcing consistent namespace conventions and eliminating remaining procedural files.")

if __name__ == "__main__":
    show_legacy_intelligence()
