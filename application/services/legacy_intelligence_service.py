"""
Module G: Legacy PHP Intelligence Service
Reads from both the graph JSON metadata and the persisted LegacyMetrics DB row
to surface PHP era classification, pattern detection, and modernization scoring.
"""
import json
import os
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text


class LegacyIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    def get_legacy_intelligence(self, run_id: int) -> dict:
        graph_path = f"data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Graph file not found: {graph_path}")

        with open(graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        nodes = graph_data.get("nodes", [])

        # ---------------------------------------------------------------
        # 1. Load persisted LegacyMetrics from SQLite (if available)
        # ---------------------------------------------------------------
        legacy_row = None
        try:
            result = self.db.execute(
                text("SELECT * FROM legacy_metrics WHERE run_id = :rid ORDER BY id DESC LIMIT 1"),
                {"rid": run_id}
            ).fetchone()
            if result:
                legacy_row = dict(result._mapping)
        except Exception:
            pass

        # ---------------------------------------------------------------
        # 2. Legacy Pattern Detection from graph node metadata
        # ---------------------------------------------------------------
        legacy_patterns: dict = defaultdict(list)
        pattern_totals: dict = defaultdict(int)

        # All detectable pattern types (PHP parser emits these as requirements)
        LEGACY_PATTERN_TYPES = [
            "LEGACY_AUTOLOAD",            # __autoload() — deprecated PHP 7.2
            "HARDCODED_DB_CREDENTIALS",   # mysql_connect/PDO with literal strings
            "VARIABLE_VARIABLE",          # $$var — dynamic binding
            "CUSTOM_AUTH",                # session_set_save_handler — non-standard auth
            "MYSQL_LEGACY",               # mysql_query, mysql_fetch_* family
            "REGISTER_GLOBALS_ASSUMPTION",# extract() / import_request_variables()
            "INCLUDE_ROUTING",            # dynamic include/require used as routing
            "INLINE_HTML",                # raw HTML mixed into PHP files
        ]

        for n in nodes:
            fqn = n.get("fqn", n.get("file_path", ""))
            src_name = os.path.basename(fqn) if fqn else n.get("name", "unknown")
            metadata = n.get("metadata", {})

            for req in metadata.get("requirements", []):
                rtype = req.get("type", "")
                if rtype in LEGACY_PATTERN_TYPES:
                    pattern_totals[rtype] += 1
                    legacy_patterns[rtype].append({
                        "file":     fqn,
                        "filename": src_name,
                        "line":     req.get("line"),
                        "detail":   req.get("function") or req.get("snippet") or req.get("bytes"),
                    })

        # ---------------------------------------------------------------
        # 3. Procedural vs OOP Ratio + Hosting Signal scan
        # ---------------------------------------------------------------
        total_files = 0
        files_with_classes = 0
        files_with_namespace = 0
        files_with_functions_only = 0
        variable_variable_files = set()
        hosting_signal_files = set()

        for n in nodes:
            ntype = n.get("type", "")
            if ntype != "file":
                continue
            fqn = n.get("fqn", "")
            if "vendor" in fqn or "doctrine" in fqn.lower():
                continue
            total_files += 1
            metadata = n.get("metadata", {})
            has_classes = bool(metadata.get("classes"))
            has_ns = bool(metadata.get("namespaces"))
            has_fns = bool(metadata.get("functions"))

            if has_classes:
                files_with_classes += 1
            if has_ns:
                files_with_namespace += 1
            if not has_classes and has_fns:
                files_with_functions_only += 1

            for req in metadata.get("requirements", []):
                rtype = req.get("type", "")
                if rtype == "VARIABLE_VARIABLE":
                    variable_variable_files.add(fqn)

            # Hosting signals: ini_set, header, set_time_limit in file_side_effects
            for se in metadata.get("file_side_effects", []):
                if se.get("type") == "HOSTING":
                    hosting_signal_files.add(fqn)

        procedural_ratio = (total_files - files_with_classes) / total_files if total_files > 0 else 0.0
        namespace_ratio  = files_with_namespace / total_files if total_files > 0 else 0.0

        # ---------------------------------------------------------------
        # 4. Era Signals — composite scoring
        # ---------------------------------------------------------------
        era_signals = []

        def _sig(signal, severity, era, count, detail=None):
            s = {"signal": signal, "severity": severity, "era": era, "count": count}
            if detail:
                s["detail"] = detail
            era_signals.append(s)

        # PHP 4 / Early PHP 5 signals
        if pattern_totals.get("MYSQL_LEGACY", 0) > 0:
            _sig("mysql_*() family usage", "HIGH", "PHP 4 / Early PHP 5",
                 pattern_totals["MYSQL_LEGACY"],
                 "Removed in PHP 7.0 — these calls will crash on modern PHP")
        if pattern_totals.get("LEGACY_AUTOLOAD", 0) > 0:
            _sig("__autoload() detected", "HIGH", "PHP 4 / Early PHP 5",
                 pattern_totals["LEGACY_AUTOLOAD"],
                 "Deprecated PHP 7.2, removed PHP 8.0")
        if pattern_totals.get("HARDCODED_DB_CREDENTIALS", 0) > 0:
            _sig("Hardcoded DB credentials in mysql_connect/PDO", "CRITICAL", "PHP 4 / Early PHP 5",
                 pattern_totals["HARDCODED_DB_CREDENTIALS"])
        if pattern_totals.get("REGISTER_GLOBALS_ASSUMPTION", 0) > 0:
            _sig("register_globals assumption (extract/import_request_variables)", "HIGH", "PHP 4",
                 pattern_totals["REGISTER_GLOBALS_ASSUMPTION"],
                 "Indicates codebase assumes register_globals=On — removed PHP 5.4")

        # PHP 4 / PHP 5 mixed signals
        if pattern_totals.get("INLINE_HTML", 0) > 0:
            _sig("Inline HTML/PHP mixing", "MEDIUM", "PHP 4 / PHP 5",
                 pattern_totals["INLINE_HTML"],
                 "HTML embedded directly in PHP files — no template layer")
        if pattern_totals.get("INCLUDE_ROUTING", 0) > 0:
            _sig("Dynamic include/require used as router", "MEDIUM", "PHP 4 / PHP 5",
                 pattern_totals["INCLUDE_ROUTING"],
                 "Routing via include($page) — no framework routing layer")
        if pattern_totals.get("VARIABLE_VARIABLE", 0) > 0:
            _sig("Variable Variables ($$var)", "MEDIUM", "PHP 4 / PHP 5",
                 pattern_totals["VARIABLE_VARIABLE"])
        if pattern_totals.get("CUSTOM_AUTH", 0) > 0:
            _sig("Custom session save handler", "LOW", "PHP 5",
                 pattern_totals["CUSTOM_AUTH"],
                 "Non-standard auth flow — risky to migrate")

        # Structural signals
        if namespace_ratio < 0.1 and total_files > 10:
            _sig(f"Low namespace adoption ({namespace_ratio*100:.1f}%)", "HIGH", "PHP 4 / PHP 5",
                 total_files - files_with_namespace)
        if procedural_ratio > 0.6:
            _sig(f"Predominantly procedural ({procedural_ratio*100:.1f}%)", "MEDIUM", "PHP 4 / PHP 5",
                 int(procedural_ratio * total_files))

        # Hosting signals
        if len(hosting_signal_files) > 0:
            _sig(f"Hosting assumption calls (ini_set/header/set_time_limit)", "LOW", "PHP 5 transitional",
                 len(hosting_signal_files),
                 "Assumes direct PHP server control — incompatible with containerized hosting")

        # ---------------------------------------------------------------
        # 5. Era Classification (composite score)
        # ---------------------------------------------------------------
        critical = sum(1 for s in era_signals if s["severity"] == "CRITICAL")
        high     = sum(1 for s in era_signals if s["severity"] == "HIGH")

        if legacy_row and legacy_row.get("php_era"):
            classified_era = legacy_row["php_era"]
        elif pattern_totals.get("MYSQL_LEGACY", 0) > 0 or critical > 0:
            classified_era = "Era A/B (PHP 4 / Early PHP 5)"
        elif high >= 2 or namespace_ratio < 0.2:
            classified_era = "Era B/C (PHP 5 Transitional)"
        elif namespace_ratio > 0.5 and files_with_classes > files_with_functions_only:
            classified_era = "Era D (PHP 7+)"
        else:
            classified_era = "Era C (PHP 5 Transitional)"

        # ---------------------------------------------------------------
        # 6. Modernization Score Dimensions from persisted LegacyMetrics
        # ---------------------------------------------------------------
        score_dimensions = {}
        if legacy_row:
            score_dimensions = {
                "PHP Era":                   legacy_row.get("php_era", "Unclassified / Custom"),
                "Framework":                 legacy_row.get("detected_framework", "Bespoke / No Framework"),
                "DB Layer":                  legacy_row.get("db_layer", "Custom / Bespoke"),
                "Auth Layer":                legacy_row.get("auth_layer", "Custom / Bespoke"),
                "Template Layer":            legacy_row.get("template_layer", "Custom / Bespoke"),
                "Autoloading":               legacy_row.get("autoloading_strategy", "Custom / Bespoke"),
                "Hosting Risk":              legacy_row.get("hosting_risk_level", "Unknown"),
                "Total Modernization Score": legacy_row.get("total_modernization_score", 0.0) / 100.0,
                "Namespace Score":           legacy_row.get("namespace_score", 0.0) / 10.0,
                "Security Score":            legacy_row.get("security_score", 0.0) / 20.0,
                "DB Layer Score":            legacy_row.get("db_layer_score", 0.0) / 15.0,
                "Testability Score":         legacy_row.get("testability_score", 0.0) / 10.0,
                "Coupling Score":            legacy_row.get("coupling_score", 0.0) / 15.0,
            }

        return {
            "classified_era":        classified_era,
            "pattern_totals":        dict(pattern_totals),
            "legacy_patterns":       {k: v[:20] for k, v in legacy_patterns.items()},
            "procedural_ratio":      round(procedural_ratio, 4),
            "namespace_ratio":       round(namespace_ratio, 4),
            "total_files_scanned":   total_files,
            "files_with_classes":    files_with_classes,
            "files_namespace_aware": files_with_namespace,
            "files_procedural_only": files_with_functions_only,
            "variable_variable_count": len(variable_variable_files),
            "hosting_signal_count":  len(hosting_signal_files),
            "era_signals":           era_signals,
            "score_dimensions":      score_dimensions,
        }
