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
        graph_path = f"/data/graph_{run_id}.json"
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

        LEGACY_PATTERN_TYPES = [
            "LEGACY_AUTOLOAD",    # __autoload() usage
            "HARDCODED_DB_CREDENTIALS",  # mysql_connect with literal string
            "VARIABLE_VARIABLE",  # $$var style
            "CUSTOM_AUTH",        # session_set_save_handler usage
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
                        "file": fqn,
                        "filename": src_name,
                        "line": req.get("line"),
                    })

        # ---------------------------------------------------------------
        # 3. Procedural vs OOP Ratio
        # ---------------------------------------------------------------
        total_files = 0
        files_with_classes = 0
        files_with_namespace = 0
        files_with_functions_only = 0
        variable_variable_files = set()
        inline_html_files = []

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
                if req.get("type") == "VARIABLE_VARIABLE":
                    variable_variable_files.add(fqn)

        procedural_ratio = (total_files - files_with_classes) / total_files if total_files > 0 else 0.0
        namespace_ratio = files_with_namespace / total_files if total_files > 0 else 0.0

        # ---------------------------------------------------------------
        # 4. Era Signals Summary
        # ---------------------------------------------------------------
        era_signals = []

        if pattern_totals.get("LEGACY_AUTOLOAD", 0) > 0:
            era_signals.append({"signal": "__autoload() detected", "severity": "HIGH", "era": "PHP 4/5 early", "count": pattern_totals["LEGACY_AUTOLOAD"]})
        if pattern_totals.get("HARDCODED_DB_CREDENTIALS", 0) > 0:
            era_signals.append({"signal": "Hardcoded DB credentials", "severity": "CRITICAL", "era": "PHP 4/5 early", "count": pattern_totals["HARDCODED_DB_CREDENTIALS"]})
        if pattern_totals.get("VARIABLE_VARIABLE", 0) > 0:
            era_signals.append({"signal": "Variable Variables ($$var)", "severity": "MEDIUM", "era": "PHP 4/5", "count": pattern_totals["VARIABLE_VARIABLE"]})
        if namespace_ratio < 0.1 and total_files > 10:
            era_signals.append({"signal": f"Low namespace adoption ({namespace_ratio*100:.1f}%)", "severity": "HIGH", "era": "PHP 4/5", "count": total_files - files_with_namespace})
        if procedural_ratio > 0.6:
            era_signals.append({"signal": f"Predominantly procedural ({procedural_ratio*100:.1f}%)", "severity": "MEDIUM", "era": "PHP 4/5", "count": int(procedural_ratio * total_files)})

        # ---------------------------------------------------------------
        # 5. Modernization Score Dimensions from persisted LegacyMetrics
        # ---------------------------------------------------------------
        score_dimensions = {}
        if legacy_row:
            score_dimensions = {
                "PHP Era": legacy_row.get("php_era", "Unknown"),
                "Framework": legacy_row.get("detected_framework", "None Detected"),
                "DB Layer": legacy_row.get("db_layer", "Unknown"),
                "Auth Layer": legacy_row.get("auth_layer", "Unknown"),
                "Template Layer": legacy_row.get("template_layer", "Unknown"),
                "Autoloading": legacy_row.get("autoloading_strategy", "Unknown"),
                "Hosting Risk": legacy_row.get("hosting_risk_level", "Unknown"),
                "Total Modernization Score": legacy_row.get("total_modernization_score", 0.0),
                "Namespace Score": legacy_row.get("namespace_score", 0.0),
                "Security Score": legacy_row.get("security_score", 0.0),
                "DB Layer Score": legacy_row.get("db_layer_score", 0.0),
                "Testability Score": legacy_row.get("testability_score", 0.0),
                "Coupling Score": legacy_row.get("coupling_score", 0.0),
            }

        return {
            "pattern_totals": dict(pattern_totals),
            "legacy_patterns": {k: v[:20] for k, v in legacy_patterns.items()},
            "procedural_ratio": round(procedural_ratio, 4),
            "namespace_ratio": round(namespace_ratio, 4),
            "total_files_scanned": total_files,
            "files_with_classes": files_with_classes,
            "files_namespace_aware": files_with_namespace,
            "files_procedural_only": files_with_functions_only,
            "variable_variable_count": len(variable_variable_files),
            "era_signals": era_signals,
            "score_dimensions": score_dimensions,
        }
