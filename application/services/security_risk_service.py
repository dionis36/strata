import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecurityRiskService:
    def __init__(self, db=None):
        self.data_dir = os.environ.get("DATA_DIR", "data")

    def get_security_risk_audit(self, run_id: int) -> Dict[str, Any]:
        graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
        if not os.path.exists(graph_file):
            return {}

        with open(graph_file, "r") as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Calculate Fan-Out and Fan-In dynamically
        fan_out_map = {}
        fan_in_map = {}
        adj = {} # Adjacency map for flow tracing
        for e in edges:
            u = e.get("source_id") or e.get("source")
            v = e.get("target_id") or e.get("target")
            if u and v:
                fan_out_map[u] = fan_out_map.get(u, 0) + 1
                fan_in_map[v] = fan_in_map.get(v, 0) + 1
                if u not in adj: adj[u] = []
                adj[u].append(v)
            
        file_matrix = []
        vulnerabilities = []
        architectural_rot = []
        
        # Identify entry points (sources) for taint flow
        entry_points = []
        for n in nodes:
            meta = n.get("metadata", {})
            if meta.get("server_request_uri", 0) > 0 or (len(meta.get("classes", {})) == 0 and len(meta.get("functions", {})) == 0 and meta.get("html_nodes", 0) > 0):
                entry_points.append(n.get("fqn") or n.get("name"))

        def find_taint_flow(sink_fqn):
            """Heuristic to see if any entry point can reach this sink."""
            for ep in entry_points:
                # BFS/DFS check
                visited = {ep}
                stack = [ep]
                while stack:
                    curr = stack.pop()
                    if curr == sink_fqn:
                        return f"Flow Trace: {ep} -> [Path] -> {sink_fqn}"
                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
            return None
        
        def find_keys(obj, key):
            if isinstance(obj, dict):
                if key in obj: yield obj[key]
                for k, v in obj.items(): yield from find_keys(v, key)
            elif isinstance(obj, list):
                for item in obj: yield from find_keys(item, key)

        total_cc = 0
        max_cc = 0
        max_cc_file = "None"
        total_danger = 0
        
        for n in nodes:
            node_type = n.get("type") or n.get("node_type")
            if node_type in ["file", "NodeType.FILE"]:
                fqn = n.get("fqn") or n.get("name")
                meta = n.get("metadata", {})
                
                cc = meta.get("complexity", 1)
                
                total_cc += cc
                if cc > max_cc:
                    max_cc = cc
                    max_cc_file = fqn
                
                file_sinks = 0
                for t in find_keys(meta, 'type'):
                    if t in ['DANGER', 'MYSQL_LEGACY', 'INCLUDE_ROUTING', 'VARIABLE_VARIABLE', 'HOSTING', 'LEGACY_HASH']:
                        file_sinks += 1
                        
                        vuln_type = t
                        magnitude = "CRITICAL" if t in ['DANGER', 'MYSQL_LEGACY', 'INCLUDE_ROUTING'] else "HIGH"
                        classification = "Security" if t in ['DANGER', 'MYSQL_LEGACY', 'LEGACY_HASH'] else "Architectural"
                        if t == 'DANGER': total_danger += 1
                        
                        flow = find_taint_flow(fqn)
                        evidence = f"Detected '{vuln_type}' signature in AST."
                        if flow:
                            evidence += f" {flow}"
                        
                        vulnerabilities.append({
                            "Risk Classification": classification,
                            "Risk Magnitude": magnitude,
                            "Vulnerability Type": vuln_type,
                            "File": fqn,
                            "Evidence": evidence
                        })
                        
                global_usage = sum(1 for g in meta.get("globals", []))
                if global_usage > 0:
                    architectural_rot.append({
                        "Risk Magnitude": "HIGH" if global_usage > 5 else "MEDIUM",
                        "Defect Type": "Global State Coupling",
                        "File": fqn,
                        "Impact": f"{global_usage} global variable access(es). Breaks testability."
                    })
                
                # Check for classes (God Object heuristic)
                num_classes = len(meta.get("classes", {}))
                num_funcs = len(meta.get("functions", {}))
                if num_classes > 1:
                    architectural_rot.append({
                        "Risk Magnitude": "HIGH",
                        "Defect Type": "Multiple Classes per File",
                        "File": fqn,
                        "Impact": f"{num_classes} classes defined in one file. Violates PSR-1/PSR-4."
                    })
                
                # Gap 4: Dead Code Heuristic
                fan_in = fan_in_map.get(n.get("id"), 0)
                if fan_in == 0 and fqn not in entry_points and "/vendor/" not in fqn.lower():
                    architectural_rot.append({
                        "Risk Magnitude": "MEDIUM",
                        "Defect Type": "Potential Dead Code",
                        "File": fqn,
                        "Impact": "Orphaned file with 0 incoming connections. Candidates for deletion."
                    })
                    
                # Composite Volumetrics
                nesting = meta.get("nesting_depth", 0)
                max_method_loc = meta.get("max_method_loc", 0)
                
                # Approximate Fan-out by summing fan-out of the file and its methods
                # Method IDs usually start with the file path hash or are inside the file.
                # For simplicity, we'll assign a heuristic fan-out based on includes and class dependencies if edge matching is complex,
                # or just use the length of dependencies found in requirements.
                fan_out = len(meta.get("includes", [])) + len(meta.get("calls", []))
                
                # Rule A: Strong Logic (High Refactor Risk)
                if cc > 20 and fan_out > 15 and global_usage > 5:
                    architectural_rot.append({
                        "Risk Magnitude": "CRITICAL",
                        "Defect Type": "High Refactor Risk",
                        "File": fqn,
                        "Impact": f"Complexity ({cc}), Fan-Out ({fan_out}), Globals ({global_usage}). Direct extraction is highly unstable."
                    })
                    
                # Rule B: Microservice Blocker
                if file_sinks > 2 and global_usage > 10:
                    architectural_rot.append({
                        "Risk Magnitude": "CRITICAL",
                        "Defect Type": "Microservice Extraction Blocker",
                        "File": fqn,
                        "Impact": f"Contains {file_sinks} severe sinks and {global_usage} global accesses. Direct microservice extraction is blocked."
                    })
                    
                overall_risk = "CRITICAL" if file_sinks > 0 or cc > 20 else ("HIGH" if cc > 10 else "LOW")
                # Maintainability Index heuristic (0-100)
                mi = max(0, 100 - (cc * 2.5) - (file_sinks * 10) - (global_usage * 2))
                    
                file_matrix.append({
                    "File Name": fqn,
                    "Overall Risk": overall_risk,
                    "Maintainability Index": round(mi, 1),
                    "Cyclomatic Complexity": cc,
                    "Max Nesting Depth": nesting,
                    "Max Method LOC": max_method_loc,
                    "Fan-Out": fan_out,
                    "Security Sinks": file_sinks,
                    "Global Accesses": global_usage
                })

        avg_mi = sum(f["Maintainability Index"] for f in file_matrix) / len(file_matrix) if file_matrix else 100

        return {
            "kpis": {
                "Average Maintainability": round(avg_mi, 1),
                "Critical Sinks": total_danger,
                "God File": max_cc_file.split("/")[-1] if "/" in max_cc_file else max_cc_file,
                "God File CC": max_cc
            },
            "file_matrix": sorted(file_matrix, key=lambda x: x["Cyclomatic Complexity"], reverse=True),
            "vulnerabilities": sorted(vulnerabilities, key=lambda x: 0 if x["Risk Magnitude"] == "CRITICAL" else 1),
            "architectural_rot": sorted(architectural_rot, key=lambda x: 0 if x["Risk Magnitude"] == "CRITICAL" else 1)
        }
