import json
import os
from collections import defaultdict
from sqlalchemy.orm import Session

class LayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_layered_analysis(self, run_id: int) -> dict:
        graph_path = f"/data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Graph file not found: {graph_path}")
            
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # --- Layer 1: File System & Folder Classification ---
        file_types = {"php": 0, "js": 0, "css": 0, "html": 0, "other": 0}
        directories = defaultdict(lambda: {"count": 0, "type": "src", "files": []})
        entry_points = []
        
        for n in nodes:
            if n.get("type") == "file":
                path = n.get("fqn", "")
                ext = path.split('.')[-1].lower() if '.' in path else 'other'
                if ext in file_types:
                    file_types[ext] += 1
                else:
                    file_types["other"] += 1
                
                # Classify Directories
                dir_name = os.path.dirname(path)
                if not dir_name: dir_name = "/"
                
                cat = "src"
                if "/vendor/" in path: cat = "vendor"
                elif "/public/" in path or "/htdocs/" in path or path.endswith("index.php"): 
                    cat = "entry_point"
                    entry_points.append(path)
                elif "/assets/" in path or ext in ['css', 'js', 'jpg', 'png']: cat = "asset"
                elif "/uploads/" in path: cat = "upload"
                
                directories[dir_name]["type"] = cat
                directories[dir_name]["count"] += 1
                directories[dir_name]["files"].append(os.path.basename(path))

        # --- Layer 2: PHP AST OOP Manifest ---
        oop_entities = []
        class_to_sinks = defaultdict(list)
        
        # Map side-effects to their source
        for e in edges:
            if "sink::" in e["target_id"] or "global::" in e["target_id"]:
                class_to_sinks[e["source_id"]].append(e["target_id"])
        
        for n in nodes:
            if n.get("type") == "class":
                metadata = n.get("metadata", {})
                oop_entities.append({
                    "name": n.get("name"),
                    "namespace": n.get("namespace"),
                    "methods_count": len(metadata.get("methods", [])),
                    "is_interface": metadata.get("isInterface", False),
                    "is_trait": metadata.get("isTrait", False),
                    "parent_class": metadata.get("extends"),
                    "side_effects": list(set(class_to_sinks.get(n["id"], [])))
                })

        # --- Layer 3: Semantic Architecture & Bounded Contexts ---
        # Group logic files by their top-level directory to infer bounded contexts
        contexts = defaultdict(lambda: {"files": set(), "internal_edges": 0, "external_edges": 0, "db_access": False, "auth_access": False})
        
        node_to_context = {}
        for n in nodes:
            if n.get("type") in ["file", "class"] and "vendor" not in n.get("fqn", ""):
                # Naive bounded context grouping: Top level directory after project root
                parts = n.get("fqn", "").strip("/").split("/")
                # If path has at least 2 parts (e.g. data/proj/app/Billing), take the 4th part as context
                # To be safe, we'll just take the 2nd to last directory
                if len(parts) >= 2:
                    ctx = parts[-2]
                else:
                    ctx = "Root"
                    
                contexts[ctx]["files"].add(n["id"])
                node_to_context[n["id"]] = ctx
                
        for e in edges:
            src_ctx = node_to_context.get(e["source_id"])
            tgt_ctx = node_to_context.get(e["target_id"])
            
            if src_ctx:
                if tgt_ctx and src_ctx == tgt_ctx:
                    contexts[src_ctx]["internal_edges"] += 1
                elif tgt_ctx and src_ctx != tgt_ctx:
                    contexts[src_ctx]["external_edges"] += 1
                    
                # Flow Analysis
                if "sink::RAW_SQL" in e["target_id"] or "table::" in e["target_id"]:
                    contexts[src_ctx]["db_access"] = True
                if "sink::CUSTOM_AUTH" in e["target_id"] or "global::_SESSION" in e["target_id"]:
                    contexts[src_ctx]["auth_access"] = True
                    
        # Clean up contexts for serialization
        bounded_contexts = []
        for name, data in contexts.items():
            if len(data["files"]) > 0: # Only contexts with logic
                coupling_ratio = round(data["external_edges"] / (data["internal_edges"] + 1), 2)
                bounded_contexts.append({
                    "name": name,
                    "file_count": len(data["files"]),
                    "internal_edges": data["internal_edges"],
                    "external_edges": data["external_edges"],
                    "coupling_ratio": coupling_ratio,
                    "is_transactional": data["db_access"],
                    "handles_auth": data["auth_access"]
                })
        
        return {
            "layer_1": {
                "file_types": file_types,
                "directories": dict(directories),
                "entry_points": entry_points
            },
            "layer_2": {
                "oop_entities": oop_entities
            },
            "layer_3": {
                "bounded_contexts": bounded_contexts
            }
        }
