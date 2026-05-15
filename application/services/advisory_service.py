import json
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AdvisoryService:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.environ.get("DATA_DIR", "/data")

    def get_strategic_roadmap(self, run_id: int) -> Dict[str, Any]:
        graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
        if not os.path.exists(graph_file):
            return {"error": "Graph data not found"}

        with open(graph_file, "r") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # We leverage the semantic clustering from Module B if available
        # Or we fall back to directory-based context clustering
        contexts = self._group_by_context(nodes)
        
        recommendations = []
        for ctx_name, ctx_nodes in contexts.items():
            metrics = self._calculate_context_metrics(ctx_nodes, edges)
            strategy = self._infer_strategy(metrics)
            effort = self._estimate_effort(metrics)
            
            recommendations.append({
                "Context": ctx_name,
                "Recommended Strategy": strategy["option"],
                "Modernization ROI": strategy["roi"],
                "Migration Effort": f"{effort} Logic Points",
                "Rationale": strategy["rationale"],
                "Primary Blocker": metrics["primary_blocker"]
            })

        # Summary KPIs for the Dashboard
        total_effort = sum(int(r["Migration Effort"].split()[0]) for r in recommendations)
        
        return {
            "recommendations": sorted(recommendations, key=lambda x: x["Modernization ROI"], reverse=True),
            "kpis": {
                "Overall Migration Effort": f"{total_effort} Points",
                "Most Common Strategy": self._get_most_common(recommendations, "Recommended Strategy"),
                "High Value Targets": sum(1 for r in recommendations if r["Modernization ROI"] > 70)
            }
        }

    def _group_by_context(self, nodes: List[Dict]) -> Dict[str, List[Dict]]:
        groups = {}
        # Identify the most common root prefix to find project root
        all_paths = [n.get("fqn", "") for n in nodes if n.get("type") in ["file", "NodeType.FILE"]]
        if not all_paths: return {}
        
        # Simple heuristic: split by '/' and find the first part that varies across files
        # but is below the /data/ProjectRoot level
        for n in nodes:
            if n.get("type") not in ["file", "NodeType.FILE"]: continue
            fqn = n.get("fqn") or n.get("name", "unknown")
            parts = fqn.strip("/").split("/")
            
            # For /data/OWASPWebGoatPHP-master/app/controller/...
            # parts is ['data', 'OWASPWebGoatPHP-master', 'app', 'controller', ...]
            # We want 'app' (index 2)
            if len(parts) > 2:
                ctx_name = parts[2]
            else:
                ctx_name = "Core / Root"
            
            if ctx_name not in groups: groups[ctx_name] = []
            groups[ctx_name].append(n)
        return groups

    def _calculate_context_metrics(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        total_cc = 0
        total_mi = 0
        total_sinks = 0
        total_loc = 0
        node_ids = set(n.get("id") for n in nodes)
        
        external_calls = 0
        internal_calls = 0
        
        for e in edges:
            src = e.get("source_id") or e.get("source")
            tgt = e.get("target_id") or e.get("target")
            if src in node_ids and tgt in node_ids:
                internal_calls += 1
            elif src in node_ids or tgt in node_ids:
                external_calls += 1

        for n in nodes:
            meta = n.get("metadata", {})
            total_cc += meta.get("complexity", 1)
            total_mi += meta.get("maintainability", 100)
            total_loc += meta.get("loc", 0)
            
            for req in meta.get("requirements", []):
                if req.get("type") in ["DANGER", "MYSQL_LEGACY", "INCLUDE_ROUTING"]:
                    total_sinks += 1

        count = len(nodes)
        avg_cc = total_cc / count if count > 0 else 0
        avg_mi = total_mi / count if count > 0 else 100
        coupling = external_calls / (internal_calls + external_calls) if (internal_calls + external_calls) > 0 else 0
        
        # Identify primary blocker
        blocker = "None"
        if avg_cc > 20: blocker = "Logic Complexity"
        elif total_sinks > count * 0.5: blocker = "Security Surface"
        elif coupling > 0.6: blocker = "Network/IO Entanglement"

        return {
            "avg_cc": avg_cc,
            "avg_mi": avg_mi,
            "total_sinks": total_sinks,
            "total_loc": total_loc,
            "coupling": coupling,
            "cohesion": 1 - coupling,
            "count": count,
            "primary_blocker": blocker
        }

    def _infer_strategy(self, m: Dict) -> Dict[str, Any]:
        # Rule Engine Logic - Tuned for granularity
        if m["avg_mi"] < 40 and m["avg_cc"] > 10:
            return {
                "option": "REWRITE",
                "roi": 45 + (10 - m["avg_cc"]),
                "rationale": f"Critical logical rot (MI: {round(m['avg_mi'],1)}). Structural debt makes refactoring more expensive than greenfield rewrite."
            }
        
        if m["coupling"] > 0.4 and m["count"] > 5:
            return {
                "option": "STRANGLER FIG",
                "roi": 80 + int(m["cohesion"] * 10),
                "rationale": f"High coupling ({round(m['coupling']*100)}%) detected. Recommended to wrap in an API facade and migrate functionality to a modern service."
            }

        if m["total_sinks"] > 0:
            return {
                "option": "REPLATFORM",
                "roi": 75,
                "rationale": f"Security surface detected ({m['total_sinks']} sinks). Move to a modern framework with automated sanitization layers."
            }

        if m["coupling"] < 0.25 and m["avg_cc"] > 5:
            return {
                "option": "EXTRACT (MICROSERVICE)",
                "roi": 90,
                "rationale": "High isolation and logical value. Prime candidate for independent scaling and extraction."
            }
        
        return {
            "option": "RETAIN / REHOST",
            "roi": 60,
            "rationale": "Stable component with manageable metrics. Keep in monolith for now to focus on high-risk targets."
        }

    def _estimate_effort(self, m: Dict) -> int:
        # Point-based estimation formula
        base = (m["total_loc"] / 50)
        complexity_mult = 1 + (m["avg_cc"] / 15)
        coupling_mult = 1 + (m["coupling"] * 2)
        risk_mult = 1 + (m["total_sinks"] * 0.1)
        
        return int(base * complexity_mult * coupling_mult * risk_mult)

    def _get_most_common(self, items: List[Dict], key: str) -> str:
        if not items: return "None"
        counts = {}
        for i in items:
            val = i.get(key)
            counts[val] = counts.get(val, 0) + 1
        return max(counts, key=counts.get)
