import json
import os
import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.environ.get("DATA_DIR", "/data")

    def get_extraction_impact(self, run_id: int, target_fqn: str) -> Dict[str, Any]:
        graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
        if not os.path.exists(graph_file):
            return {"error": "Graph data not found"}

        with open(graph_file, "r") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # 1. Map every node (method/class) to its parent file
        node_id_to_file = {}
        file_to_meta = {}
        all_files = set()
        
        for n in nodes:
            nid = n.get("id")
            # Heuristic: file_path is the parent. If node IS a file, use its FQN/path.
            fpath = n.get("file_path") or n.get("fqn") or n.get("name")
            if not fpath: continue
            
            node_id_to_file[nid] = fpath
            all_files.add(fpath)
            
            # Merge metadata into file-level meta
            if fpath not in file_to_meta:
                file_to_meta[fpath] = {"globals": [], "requirements": []}
            
            meta = n.get("metadata", {})
            file_to_meta[fpath]["globals"].extend(meta.get("globals", []))
            file_to_meta[fpath]["requirements"].extend(meta.get("requirements", []))

        # 2. Build file-to-file adjacency (Roll-up)
        downstream_adj = {} # Who calls this file?
        upstream_adj = {}   # Who does this file call?
        
        for e in edges:
            u_id = e.get("source_id") or e.get("source")
            v_id = e.get("target_id") or e.get("target")
            
            u_file = node_id_to_file.get(u_id)
            v_file = node_id_to_file.get(v_id)
            
            if u_file and v_file and u_file != v_file:
                # Upstream: u calls v (u depends on v)
                if u_file not in upstream_adj: upstream_adj[u_file] = set()
                upstream_adj[u_file].add(v_file)
                
                # Downstream: v is called by u (v impacts u)
                if v_file not in downstream_adj: downstream_adj[v_file] = set()
                downstream_adj[v_file].add(u_file)

        # Convert sets to lists for internal processing
        down_adj = {k: list(v) for k, v in downstream_adj.items()}
        up_adj = {k: list(v) for k, v in upstream_adj.items()}

        # 3. Blast Radius (Recursive Downstream)
        blast_radius = self._trace(target_fqn, down_adj)
        
        # 4. Dependency Payload (Recursive Upstream)
        dependency_payload = self._trace(target_fqn, up_adj)
        
        # 5. State Tear Aggregation
        global_deps = set()
        db_deps = set()
        for f in dependency_payload:
            meta = file_to_meta.get(f, {})
            for g in meta.get("globals", []):
                global_deps.add(g.get("name"))
            for req in meta.get("requirements", []):
                if req.get("type") in ["DB_WRITE", "RAW_SQL", "MYSQL_LEGACY", "DB_READ"]:
                    db_deps.add("Database State")

        return {
            "target": target_fqn,
            "blast_radius": {
                "count": len(blast_radius),
                "files": list(blast_radius)
            },
            "dependency_payload": {
                "count": len(dependency_payload),
                "files": list(dependency_payload)
            },
            "state_tear": {
                "globals": list(global_deps),
                "db_dependencies": list(db_deps)
            },
            "isolation_score": self._calculate_isolation_score(len(blast_radius), len(dependency_payload))
        }

    def _trace(self, start_fqn: str, adj: Dict[str, List[str]], depth: int = 5) -> Set[str]:
        visited = {start_fqn}
        stack = [(start_fqn, 0)]
        while stack:
            curr, curr_depth = stack.pop()
            if curr_depth >= depth: continue
            
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, curr_depth + 1))
        return visited

    def _calculate_isolation_score(self, blast_radius: int, payload_size: int) -> str:
        ratio = blast_radius / payload_size if payload_size > 0 else 0
        if ratio > 2: return "🔴 HIGH FRICTION (Extensive Refactoring Needed)"
        if ratio > 1: return "🟡 MODERATE (Manageable Side-Effects)"
        return "🟢 CLEAN (Independent / Leaf Node)"
