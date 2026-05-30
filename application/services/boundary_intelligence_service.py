import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BoundaryIntelligenceService:
    def __init__(self, db=None):
        self.data_dir = os.environ.get("DATA_DIR", "/data")

    def get_boundary_intelligence(self, run_id: int) -> Dict[str, Any]:
        graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
        if not os.path.exists(graph_file):
            return {}

        with open(graph_file, "r") as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        unique_files = sorted(list(set(
            n.get("file_path") or n.get("fqn") or n.get("name") 
            for n in nodes 
            if (n.get("file_path") or n.get("fqn") or n.get("name")) 
            and (n.get("type") in ["file", "NodeType.FILE"])
            and not ("/vendor/" in (n.get("file_path") or n.get("fqn") or n.get("name", "")).lower())
        )))
        
        presentation_coupling = []
        api_surface = []
        vendor_intelligence = []
        vendor_files = set() # To track which files are vendor for edge filtering
        file_to_node = {} # For quick node lookup
        
        total_html_nodes = 0
        total_php_nodes = 0
        
        for n in nodes:
            node_type = n.get("type") or n.get("node_type")
            if node_type in ["file", "NodeType.FILE"]:
                fqn = n.get("fqn") or n.get("name")
                meta = n.get("metadata", {})
                
                # --- 1. Presentation Coupling (MVC Deficit) ---
                html_nodes = meta.get("html_nodes", 0)
                echo_nodes = meta.get("echo_nodes", 0)
                complexity = meta.get("complexity", 1)
                
                total_html_nodes += html_nodes
                total_php_nodes += complexity
                
                ui_entanglement = html_nodes + echo_nodes
                if ui_entanglement > 0:
                    db_writes = 0
                    if isinstance(meta.get("requirements"), list):
                        for req in meta.get("requirements", []):
                            if req.get("type") in ["DB_WRITE", "MYSQL_LEGACY", "RAW_SQL"]:
                                db_writes += 1
                                
                    ratio = (ui_entanglement / (complexity + ui_entanglement)) * 100 if (complexity + ui_entanglement) > 0 else 0
                    
                    if ratio > 15 and db_writes > 0:
                        presentation_coupling.append({
                            "File": fqn,
                            "Entanglement Ratio": f"{ratio:.1f}%",
                            "HTML/Echo Nodes": ui_entanglement,
                            "DB Operations": db_writes,
                            "Severity": "🔴 CRITICAL (Fat View)"
                        })
                    elif ratio > 0:
                        presentation_coupling.append({
                            "File": fqn,
                            "Entanglement Ratio": f"{ratio:.1f}%",
                            "HTML/Echo Nodes": ui_entanglement,
                            "DB Operations": db_writes,
                            "Severity": "🟡 MEDIUM" if ratio > 10 else "🟢 LOW"
                        })
                        
                # --- 2. API & Endpoint Surface ---
                api_headers = meta.get("api_headers", 0)
                json_encode = meta.get("json_encode", 0)
                request_uri = meta.get("server_request_uri", 0)
                num_classes = len(meta.get("classes", {}))
                num_funcs = len(meta.get("functions", {}))
                
                is_pure_script = num_classes == 0 and num_funcs == 0
                
                if api_headers > 0 or json_encode > 0:
                    api_surface.append({
                        "Entry Point": fqn,
                        "Type": "API Endpoint",
                        "Signature": "application/json or json_encode()",
                        "Pure Script": "Yes" if is_pure_script else "No"
                    })
                elif request_uri > 0:
                    api_surface.append({
                        "Entry Point": fqn,
                        "Type": "Procedural Router",
                        "Signature": "$_SERVER['REQUEST_URI']",
                        "Pure Script": "Yes" if is_pure_script else "No"
                    })
                elif is_pure_script and ui_entanglement > 0:
                    # Likely a direct server-rendered page
                    api_surface.append({
                        "Entry Point": fqn,
                        "Type": "Server-Rendered Page",
                        "Signature": "Direct HTML output",
                        "Pure Script": "Yes"
                    })
                    
                # --- 3. Vendor & Dependency Intelligence ---
                is_vendor = False
                vendor_name = "Unknown"
                
                if "/vendor/" in fqn.lower():
                    is_vendor = True
                    vendor_name = "Composer Vendor"
                elif "/lib/" in fqn.lower() or "/plugin/" in fqn.lower() or "/plugins/" in fqn.lower() or "/thirdparty/" in fqn.lower():
                    is_vendor = True
                    vendor_name = "Manual Library/Plugin"
                    
                namespaces = meta.get("namespaces", [])
                for ns in namespaces:
                    ns_name = ns.get("name", "").lower()
                    if "doctrine" in ns_name:
                        is_vendor = True
                        vendor_name = "Doctrine"
                    elif "smarty" in ns_name:
                        is_vendor = True
                        vendor_name = "Smarty"
                    elif "symfony" in ns_name:
                        is_vendor = True
                        vendor_name = "Symfony"
                        
                if is_vendor:
                    vulns = 0
                    if isinstance(meta.get("requirements"), list):
                        for req in meta.get("requirements", []):
                            if req.get("type") in ["MYSQL_LEGACY", "DANGER", "INCLUDE_ROUTING"]:
                                vulns += 1
                                
                    vendor_intelligence.append({
                        "File": fqn,
                        "Vendor Type": vendor_name,
                        "Known Vulnerabilities": vulns,
                        "Status": "🔴 ORPHANED RISK" if vulns > 0 and vendor_name != "Composer Vendor" else "🟢 OK"
                    })
                    vendor_files.add(fqn)
                
                # Store all file nodes for edge processing later
                file_to_node[n.get("id")] = fqn
                file_to_node[fqn] = fqn # Some edges use IDs, some use FQNs

        total_nodes = total_php_nodes + total_html_nodes
        global_entanglement = (total_html_nodes / total_nodes) * 100 if total_nodes > 0 else 0

        return {
            "kpis": {
                "Global UI Entanglement": f"{global_entanglement:.1f}%",
                "Total Endpoints Detected": len(api_surface),
                "Fat Views (DB-Coupled UI)": sum(1 for p in presentation_coupling if "CRITICAL" in p.get("Severity", "")),
                "Vendor Files Scanned": len(vendor_intelligence)
            },
            "presentation_coupling": sorted(presentation_coupling, key=lambda x: 0 if "CRITICAL" in x["Severity"] else 1),
            "api_surface": api_surface,
            "vendor_intelligence": sorted(vendor_intelligence, key=lambda x: 0 if "ORPHANED RISK" in x["Status"] else 1),
            "vendor_graph": self._build_vendor_graph(data.get("edges", []), vendor_files, file_to_node),
            "unique_files": unique_files,
            "nodes": nodes
        }

    def _build_vendor_graph(self, edges, vendor_files, file_to_node):
        """Builds a graph of connections from the monolith to vendor code."""
        nodes = {}
        graph_edges = []
        
        for e in edges:
            u_raw = e.get("source_id") or e.get("source")
            v_raw = e.get("target_id") or e.get("target")
            
            u = file_to_node.get(u_raw)
            v = file_to_node.get(v_raw)
            
            if u and v and v in vendor_files and u not in vendor_files:
                # This is a monolith -> vendor edge
                if u not in nodes:
                    nodes[u] = {"id": u, "label": os.path.basename(u), "color": "#58a6ff", "size": 15}
                if v not in nodes:
                    # Color-code vendor by risk
                    nodes[v] = {"id": v, "label": os.path.basename(v), "color": "#8b949e", "size": 10}
                
                graph_edges.append({"source": u, "target": v})
        
        return {"nodes": list(nodes.values()), "edges": graph_edges}
