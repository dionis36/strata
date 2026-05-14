"""
Module F: Runtime & Global State Intelligence
Reads from the graph JSON node metadata to surface superglobal tracking,
session flow analysis, global mutation mapping, and side-effect classification.
"""
import json
import os
from collections import defaultdict


class GlobalStateService:
    def __init__(self, db):
        self.db = db

    def get_global_state_intelligence(self, run_id: int) -> dict:
        graph_path = f"/data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Graph file not found: {graph_path}")

        with open(graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        nodes = graph_data.get("nodes", [])

        # ---------------------------------------------------------------
        # 1. Superglobal Usage Map
        # ---------------------------------------------------------------
        superglobal_usage: dict = defaultdict(lambda: defaultdict(int))
        superglobal_mutations: list = []
        superglobal_totals: dict = defaultdict(int)

        SUPERGLOBALS = ["_SESSION", "_POST", "_GET", "_COOKIE", "_FILES", "_SERVER", "_REQUEST", "_ENV", "GLOBALS"]

        for n in nodes:
            fqn = n.get("fqn", n.get("file_path", ""))
            src_name = os.path.basename(fqn) if fqn else n.get("name", "unknown")
            metadata = n.get("metadata", {})

            for g in metadata.get("globals", []):
                var_name = g.get("name", "")
                gtype = g.get("type", "usage")
                if var_name in SUPERGLOBALS:
                    superglobal_usage[src_name][var_name] += 1
                    superglobal_totals[var_name] += 1
                    if gtype == "mutation":
                        superglobal_mutations.append({
                            "file": fqn,
                            "variable": f"${var_name}",
                            "line": g.get("line"),
                            "class": g.get("sourceClass"),
                            "method": g.get("sourceMethod"),
                        })

        # ---------------------------------------------------------------
        # 2. Session Flow Analysis
        # ---------------------------------------------------------------
        # Files that write to $_SESSION vs. those that only read
        session_writers: list = []
        session_readers: list = []

        for src_name, var_map in superglobal_usage.items():
            if "_SESSION" in var_map:
                # Heuristic: if there is also a mutation record for this file, it's a writer
                file_mutations = [m for m in superglobal_mutations if os.path.basename(m["file"]) == src_name and m["variable"] == "$_SESSION"]
                if file_mutations:
                    session_writers.append({"file": src_name, "count": var_map["_SESSION"]})
                else:
                    session_readers.append({"file": src_name, "count": var_map["_SESSION"]})

        # ---------------------------------------------------------------
        # 3. Side Effects Classification
        # ---------------------------------------------------------------
        side_effect_summary: dict = defaultdict(lambda: {"DB": 0, "IO": 0, "NET": 0, "DANGER": 0, "HOSTING": 0, "TEMPLATE": 0, "AUTH": 0, "LEGACY_HASH": 0})
        danger_files: list = []
        legacy_hash_files: list = []

        for n in nodes:
            fqn = n.get("fqn", n.get("file_path", ""))
            src_name = os.path.basename(fqn) if fqn else n.get("name", "unknown")
            metadata = n.get("metadata", {})

            # From class methods (classes stored as dict in metadata)
            classes_data = metadata.get("classes", {})
            if isinstance(classes_data, list):
                classes_iter = {c.get("name", str(i)): c for i, c in enumerate(classes_data)}
            else:
                classes_iter = classes_data

            for cls in classes_iter.values():
                for method in cls.get("methods", []):
                    for se in method.get("side_effects", []):
                        side_effect_summary[src_name][se] += 1
                        if se == "DANGER":
                            danger_files.append({"file": fqn, "method": f"{cls.get('name', '?')}::{method['name']}", "line": method.get("line")})
                        if se == "LEGACY_HASH":
                            legacy_hash_files.append({"file": fqn, "method": f"{cls.get('name', '?')}::{method['name']}", "line": method.get("line")})

            # From standalone functions
            functions_data = metadata.get("functions", {})
            if isinstance(functions_data, list):
                functions_iter = {f.get("name", str(i)): f for i, f in enumerate(functions_data)}
            else:
                functions_iter = functions_data
            for func in functions_iter.values():
                for se in func.get("side_effects", []):
                    side_effect_summary[src_name][se] += 1

            # Procedural side effects (also captures eval() at file/procedure scope)
            for se in metadata.get("file_side_effects", []):
                se_type = se.get("type", "UNKNOWN")
                side_effect_summary[src_name][se_type] += 1
                if se_type == "DANGER":
                    danger_files.append({
                        "file": fqn,
                        "method": "(procedural scope)",
                        "line": se.get("line"),
                    })
                if se_type == "LEGACY_HASH":
                    legacy_hash_files.append({
                        "file": fqn,
                        "method": "(procedural scope)",
                        "line": se.get("line"),
                    })

        # ---------------------------------------------------------------
        # 4. Global Variable Tracker (non-superglobal explicit globals)
        # ---------------------------------------------------------------
        explicit_globals: list = []
        for n in nodes:
            fqn = n.get("fqn", "")
            metadata = n.get("metadata", {})
            for g in metadata.get("globals", []):
                var_name = g.get("name", "")
                if var_name not in SUPERGLOBALS:
                    explicit_globals.append({
                        "file": fqn,
                        "variable": f"${var_name}",
                        "type": g.get("type", ""),
                        "line": g.get("line"),
                        "class": g.get("sourceClass"),
                        "method": g.get("sourceMethod"),
                    })

        # Build aggregate side effect totals
        total_side_effects = {
            k: sum(v.get(k, 0) for v in side_effect_summary.values())
            for k in ["DB", "IO", "NET", "DANGER", "HOSTING", "TEMPLATE", "AUTH", "LEGACY_HASH"]
        }

        # Top files by side effect volume
        top_side_effect_files = sorted(
            [{"file": f, **counts} for f, counts in side_effect_summary.items()
             if sum(counts.values()) > 0],
            key=lambda x: sum(v for k, v in x.items() if k != "file"),
            reverse=True
        )[:20]

        return {
            "superglobal_totals": dict(superglobal_totals),
            "superglobal_mutations": superglobal_mutations[:50],
            "superglobal_file_map": {f: dict(v) for f, v in superglobal_usage.items() if sum(v.values()) > 0},
            "session_writers": session_writers,
            "session_readers": session_readers,
            "explicit_globals": explicit_globals[:50],
            "side_effect_totals": total_side_effects,
            "top_side_effect_files": top_side_effect_files,
            "danger_sinks": danger_files[:30],
            "legacy_hash_usages": legacy_hash_files[:30],
        }
