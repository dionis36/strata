"""
Requirement 11: Database Intelligence Service
Reads from SQLite (component_metrics + component_dependencies) so it works on
existing runs without requiring a re-scan. The graph JSON approach is kept as a
secondary fallback for table ownership and ERD which rely on WRITES_TO edges.
"""
import json
import os
import re
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text


class DatabaseIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    def get_db_intelligence(self, run_id: int) -> dict:
        graph_path = f"/data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Graph file not found: {graph_path}")

        with open(graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        nodes = graph_data.get("nodes", [])
        # node_link_data serializes edges as 'links'
        edges = graph_data.get("links", graph_data.get("edges", []))
        node_map = {n["id"]: n for n in nodes}

        # ---------------------------------------------------------------
        # 1. Taxonomy: walk every edge; if target is a sink:: node, count it
        # ---------------------------------------------------------------
        taxonomy = defaultdict(lambda: {
            "raw_sql": 0, "stored_procs": 0, "orm": 0,
            "transactions": 0, "credentials": 0
        })
        files_with_sql = set()
        files_with_tx  = set()
        credential_risks = []
        stored_procs_list = []

        for e in edges:
            src_id  = e.get("source", e.get("source_id", ""))
            tgt_id  = e.get("target", e.get("target_id", ""))
            etype   = e.get("type",   e.get("edge_type", ""))

            tgt_node = node_map.get(tgt_id, {})
            tgt_name = tgt_node.get("name", tgt_node.get("fqn", ""))

            src_node = node_map.get(src_id, {})
            src_fqn  = src_node.get("fqn", src_node.get("file_path", ""))
            src_name = os.path.basename(src_fqn) if src_fqn else src_node.get("name", "unknown")

            if not tgt_name.startswith("sink::") and etype != "writes_to":
                continue

            if etype == "writes_to":
                taxonomy[src_name]["orm"] += 1
                continue

            sink_type = tgt_name.replace("sink::", "")

            if sink_type == "RAW_SQL":
                taxonomy[src_name]["raw_sql"] += 1
                files_with_sql.add(src_fqn)
            elif sink_type == "STORED_PROCEDURE":
                taxonomy[src_name]["stored_procs"] += 1
                stored_procs_list.append({"file": src_fqn, "line": None, "snippet": "stored procedure call"})
            elif sink_type == "DB_TRANSACTION":
                taxonomy[src_name]["transactions"] += 1
                files_with_tx.add(src_fqn)
            elif sink_type == "HARDCODED_DB_CREDENTIALS":
                taxonomy[src_name]["credentials"] += 1
                credential_risks.append({"file": src_fqn, "line": None})

        # Unhandled transactions: files with raw SQL but no transaction wrapping
        unhandled_tx_files = []
        for fqn in files_with_sql:
            if fqn not in files_with_tx:
                fname = os.path.basename(fqn)
                unhandled_tx_files.append({
                    "file": fqn,
                    "query_count": taxonomy[fname]["raw_sql"]
                })
        unhandled_tx_files.sort(key=lambda x: x["query_count"], reverse=True)

        # ---------------------------------------------------------------
        # 2. Duplicate query detection from graph JSON metadata (new runs only)
        # ---------------------------------------------------------------
        duplicate_queries = []
        all_queries: dict = defaultdict(list)
        for n in nodes:
            if n.get("type") != "file":
                continue
            fqn = n.get("fqn", "")
            for req in n.get("metadata", {}).get("requirements", []):
                if req.get("type") in ("RAW_SQL", "STORED_PROCEDURE"):
                    raw_q = req.get("full_query", req.get("snippet", ""))
                    normalized = re.sub(r"'[^']*'", "?", raw_q)
                    normalized = re.sub(r"\b\d+\b", "?", normalized)
                    normalized = re.sub(r"\s+", " ", normalized).strip()
                    if normalized:
                        all_queries[normalized].append(fqn)

        for q, files in all_queries.items():
            unique = list(set(files))
            if len(unique) >= 2:
                duplicate_queries.append({"query": q[:80], "files": unique, "count": len(unique)})
        duplicate_queries.sort(key=lambda x: x["count"], reverse=True)

        # ---------------------------------------------------------------
        # 3. Table Ownership & ERD from WRITES_TO edges
        # ---------------------------------------------------------------
        def get_context(node):
            fqn = node.get("fqn", "")
            parts = fqn.strip("/").split("/")
            return parts[-2] if len(parts) >= 2 else "Root"

        node_to_context = {}
        for n in nodes:
            if n.get("type") in ("file", "class") and "vendor" not in n.get("fqn", ""):
                node_to_context[n["id"]] = get_context(n)

        table_ownership: dict = defaultdict(lambda: {"contexts": defaultdict(int), "total_writes": 0})
        file_to_tables: dict  = defaultdict(set)

        for e in edges:
            etype   = e.get("type", e.get("edge_type", ""))
            if etype != "writes_to":
                continue
            src_key = e.get("source", e.get("source_id", ""))
            tgt_key = e.get("target", e.get("target_id", ""))
            tgt_node = node_map.get(tgt_key, {})
            tgt_name = tgt_node.get("name", tgt_key)
            if "table::" not in tgt_name:
                continue
            table_name = tgt_name.replace("table::", "").strip()
            ctx = node_to_context.get(src_key, "Unknown")
            table_ownership[table_name]["contexts"][ctx] += 1
            table_ownership[table_name]["total_writes"] += 1
            file_to_tables[ctx].add(table_name)

        ownership_summary = []
        for table, tdata in table_ownership.items():
            owner = max(tdata["contexts"], key=tdata["contexts"].get) if tdata["contexts"] else "Unknown"
            ownership_summary.append({
                "table": table,
                "primary_owner": owner,
                "write_contexts": dict(tdata["contexts"]),
                "total_writes": tdata["total_writes"],
                "cross_module_write": len(tdata["contexts"]) > 1
            })
        ownership_summary.sort(key=lambda x: x["total_writes"], reverse=True)

        erd_relationships = []
        seen: set = set()
        for ctx, tables in file_to_tables.items():
            table_list = list(tables)
            for i in range(len(table_list)):
                for j in range(i + 1, len(table_list)):
                    key = tuple(sorted([table_list[i], table_list[j]]))
                    if key not in seen:
                        erd_relationships.append({"from": table_list[i], "to": table_list[j], "inferred_via": ctx})
                        seen.add(key)

        erd_dot = _build_erd_dot(ownership_summary, erd_relationships)

        return {
            "taxonomy": dict(taxonomy),
            "risk_audit": {
                "credential_risks": credential_risks,
                "duplicate_queries": duplicate_queries[:20],
                "unhandled_transactions": unhandled_tx_files[:20],
                "stored_procs": stored_procs_list
            },
            "table_ownership": ownership_summary,
            "erd_relationships": erd_relationships,
            "erd_dot": erd_dot
        }



def _build_erd_dot(ownership: list, relationships: list) -> str:
    lines = [
        'digraph ERD {',
        '  graph [rankdir=LR, fontname="Helvetica", bgcolor="#111111"];',
        '  node [shape=record, style=filled, fillcolor="#1e1e2e", fontcolor="#cdd6f4", color="#89b4fa", fontname="Helvetica"];',
        '  edge [color="#a6e3a1", fontcolor="#a6e3a1", fontname="Helvetica"];',
    ]
    added = set()
    for row in ownership:
        t = re.sub(r'[^a-zA-Z0-9_]', '_', row["table"])
        owner = row["primary_owner"]
        cross = " ⚠" if row["cross_module_write"] else ""
        label = f"{t}\\n[{owner}{cross}]"
        if t not in added:
            lines.append(f'  "{t}" [label="{label}"];')
            added.add(t)

    seen_edges = set()
    for rel in relationships:
        a = re.sub(r'[^a-zA-Z0-9_]', '_', rel["from"])
        b = re.sub(r'[^a-zA-Z0-9_]', '_', rel["to"])
        key = tuple(sorted([a, b]))
        if key not in seen_edges:
            via = rel["inferred_via"]
            lines.append(f'  "{a}" -> "{b}" [label="{via}", dir=both];')
            seen_edges.add(key)

    lines.append("}")
    return "\n".join(lines)
