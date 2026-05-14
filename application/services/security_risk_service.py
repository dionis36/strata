import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecurityRiskService:
    def __init__(self, db=None):
        self.data_dir = os.environ.get("DATA_DIR", "/data")

    def get_security_risk_audit(self, run_id: int) -> Dict[str, Any]:
        graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
        if not os.path.exists(graph_file):
            return {}

        with open(graph_file, "r") as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        
        file_matrix = []
        vulnerabilities = []
        architectural_rot = []
        
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
                        
                        vulnerabilities.append({
                            "Risk Classification": classification,
                            "Risk Magnitude": magnitude,
                            "Vulnerability Type": vuln_type,
                            "File": fqn,
                            "Evidence": f"Detected '{vuln_type}' signature in AST"
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
                    
                overall_risk = "CRITICAL" if file_sinks > 0 or cc > 20 else ("HIGH" if cc > 10 else "LOW")
                # Maintainability Index heuristic (0-100)
                mi = max(0, 100 - (cc * 2.5) - (file_sinks * 10) - (global_usage * 2))
                    
                file_matrix.append({
                    "File Name": fqn,
                    "Overall Risk": overall_risk,
                    "Maintainability Index": round(mi, 1),
                    "Cyclomatic Complexity": cc,
                    "Security Sinks": file_sinks,
                    "Global Accesses": global_usage,
                    "Classes Defined": num_classes,
                    "Functions": num_funcs
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
