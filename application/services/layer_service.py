import json
import os
from collections import defaultdict
from sqlalchemy.orm import Session

class LayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_layered_analysis(self, run_id: int) -> dict:
        graph_path = f"data/graph_{run_id}.json"
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"Graph file not found: {graph_path}")
            
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("links", [])
        
        # --- Layer 1: File System & Folder Classification ---
        file_types = defaultdict(int)
        directories = defaultdict(lambda: {"count": 0, "type": "src", "files": []})
        entry_points = []
        
        from domain.models.node import NodeType
        
        # Valid file-like node types from our new taxonomy
        FILE_ROLES = [
            NodeType.FILE.value, NodeType.ENTRY_POINT.value, NodeType.BOOTSTRAP.value,
            NodeType.CONTROLLER.value, NodeType.VIEW.value, NodeType.CONFIG.value,
            NodeType.ASSET.value, NodeType.JOB.value, NodeType.VENDOR.value,
            NodeType.MODEL.value, NodeType.SCHEMA.value
        ]
        
        for n in nodes:
            ntype = n.get("type")
            if ntype in FILE_ROLES:
                path = n.get("fqn", "")
                ext = path.split('.')[-1].lower() if '.' in path else 'other'
                file_types[ext] += 1
                
                # Classify Directories
                dir_name = os.path.dirname(path)
                if not dir_name: dir_name = "/"
                
                # Use the node's assigned role as the directory type hint
                # (We take the most 'important' role in the directory)
                current_cat = directories[dir_name]["type"]
                if ntype == NodeType.ENTRY_POINT.value: 
                    directories[dir_name]["type"] = "entry_point"
                    entry_points.append(path)
                elif ntype == NodeType.VENDOR.value: # Assuming we might add VENDOR later
                    directories[dir_name]["type"] = "vendor"
                elif ntype == NodeType.ASSET.value and current_cat != "entry_point":
                    directories[dir_name]["type"] = "asset"
                elif ntype == NodeType.CONFIG.value and current_cat not in ["entry_point", "asset"]:
                    directories[dir_name]["type"] = "config"
                
                directories[dir_name]["count"] += 1
                directories[dir_name]["files"].append({
                    "name": os.path.basename(path),
                    "role": ntype
                })

        # --- Layer 2: PHP AST OOP Manifest ---
        oop_entities = []
        class_to_sinks = defaultdict(list)
        
        # Map side-effects to their source
        for e in edges:
            target = str(e.get("target", ""))
            source = str(e.get("source", ""))
            if "sink::" in target or "global::" in target:
                class_to_sinks[source].append(target)
        
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
        # Group logic into logical domains and calculate coupling metrics
        contexts = defaultdict(lambda: {"files": set(), "internal_edges": 0, "external_edges": 0, "db_access": False, "auth_access": False})
        
        node_to_context = {}
        
        def get_context(fqn: str) -> str:
            if not fqn: return "Global"
            # Remove method/function boundaries to get base entity
            base_fqn = fqn.split("::")[0]
            
            # Era 3 / Namespaced Era 2 mapping
            if "\\" in base_fqn:
                parts = base_fqn.split("\\")
                return parts[0] if parts[0] else "Global"
            # Era 1 / File-based mapping
            elif "/" in base_fqn:
                parts = base_fqn.strip("/").split("/")
                # Detect Multi-Site Variant
                if "site/" in base_fqn.lower():
                    try:
                        site_idx = [p.lower() for p in parts].index("site")
                        if site_idx + 1 < len(parts):
                            return f"Site: {parts[site_idx + 1].capitalize()}"
                    except ValueError:
                        pass
                        
                if len(parts) >= 2:
                    return parts[-2]
            return "Global"

        # Pass 1: Assign EVERY node (not just files) to a Bounded Context
        for n in nodes:
            fqn = n.get("fqn", "")
            # Skip pure vendor/plugin files from taking over our domain logic
            if "vendor" in fqn.lower() or "plugin" in fqn.lower():
                continue
                
            ctx = get_context(fqn)
            node_to_context[n["id"]] = ctx
            
            # Count the 'Physical' size of the domain
            if n.get("type") in ["file", "class", "interface", "trait", "entry_point", "config"]:
                contexts[ctx]["files"].add(n["id"])
                
        id_to_fqn = {n["id"]: str(n.get("fqn", "")).lower() for n in nodes}
        
        # Pass 2: Calculate Edge Boundaries
        for e in edges:
            src_ctx = node_to_context.get(e.get("source"))
            tgt_ctx = node_to_context.get(e.get("target"))
            
            if src_ctx:
                if tgt_ctx and src_ctx == tgt_ctx:
                    contexts[src_ctx]["internal_edges"] += 1
                elif tgt_ctx and src_ctx != tgt_ctx:
                    contexts[src_ctx]["external_edges"] += 1
                    
                # Intelligent Flow Analysis (Detecting Sinks)
                tgt_fqn = id_to_fqn.get(e.get("target"), "")
                if "sink::raw_sql" in tgt_fqn or "table::" in tgt_fqn or "pdo" in tgt_fqn or "mysql" in tgt_fqn:
                    contexts[src_ctx]["db_access"] = True
                if "sink::custom_auth" in tgt_fqn or "global::_session" in tgt_fqn or "auth" in tgt_fqn:
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
