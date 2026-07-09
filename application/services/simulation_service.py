import json
import os
import logging
from typing import Dict, List, Any, Set
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self, db: Session = None, data_dir: str = None):
        self.db = db
        self.data_dir = data_dir or os.environ.get("DATA_DIR", "/data")

    def _get_db(self):
        if self.db is not None:
            return self.db
        from infrastructure.persistence.database import SessionLocal
        return SessionLocal()

    def get_extraction_impact(self, run_id: int, target_fqn: str) -> Dict[str, Any]:
        from infrastructure.persistence.models import GraphNode, GraphEdge
        
        db = self._get_db()
        try:
            # Query nodes and edges from SQLite
            nodes = db.query(GraphNode).filter(GraphNode.run_id == run_id).all()
            edges = db.query(GraphEdge).filter(GraphEdge.run_id == run_id).all()
            
            if not nodes:
                # Fallback to local file
                graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
                if os.path.exists(graph_file):
                    with open(graph_file, "r") as f:
                        data = json.load(f)
                    raw_nodes = data.get("nodes", [])
                    raw_edges = data.get("edges", [])
                else:
                    return {"error": "Graph data not found"}
            else:
                raw_nodes = []
                for n in nodes:
                    raw_nodes.append({
                        "id": n.id,
                        "name": n.name,
                        "fqn": n.fqn,
                        "type": n.node_type,
                        "file_path": n.file_path,
                        "metadata": json.loads(n.metadata_json or "{}")
                    })
                raw_edges = []
                for e in edges:
                    raw_edges.append({
                        "source": e.source_id,
                        "target": e.target_id,
                        "type": e.edge_type
                    })
        finally:
            if self.db is None:
                db.close()

        # 1. Map every node (method/class) to its parent file
        node_id_to_file = {}
        file_to_meta = {}
        all_files = set()
        
        for n in raw_nodes:
            nid = n.get("id")
            fpath = n.get("file_path") or n.get("fqn") or n.get("name")
            if not fpath: continue
            
            node_id_to_file[nid] = fpath
            all_files.add(fpath)
            
            if fpath not in file_to_meta:
                file_to_meta[fpath] = {"globals": [], "requirements": []}
            
            meta = n.get("metadata", {})
            file_to_meta[fpath]["globals"].extend(meta.get("globals", []))
            file_to_meta[fpath]["requirements"].extend(meta.get("requirements", []))

        # 2. Build file-to-file adjacency (Roll-up)
        downstream_adj = {}
        upstream_adj = {}
        
        for e in raw_edges:
            u_id = e.get("source_id") or e.get("source")
            v_id = e.get("target_id") or e.get("target")
            
            u_file = node_id_to_file.get(u_id)
            v_file = node_id_to_file.get(v_id)
            
            if u_file and v_file and u_file != v_file:
                if u_file not in upstream_adj: upstream_adj[u_file] = set()
                upstream_adj[u_file].add(v_file)
                
                if v_file not in downstream_adj: downstream_adj[v_file] = set()
                downstream_adj[v_file].add(u_file)

        down_adj = {k: list(v) for k, v in downstream_adj.items()}
        up_adj = {k: list(v) for k, v in upstream_adj.items()}

        # 3. Blast Radius
        blast_radius = self._trace(target_fqn, down_adj)
        
        # 4. Dependency Payload
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

        # Phase 11: Add target coverage
        from infrastructure.persistence.models import ComponentMetric
        target_metric = db.query(ComponentMetric).filter(
            ComponentMetric.run_id == run_id, 
            ComponentMetric.component_name == target_fqn
        ).first()
        target_coverage = target_metric.test_coverage if target_metric else None

        return {
            "target": target_fqn,
            "target_coverage": target_coverage,
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
        if ratio > 2: return " HIGH FRICTION (Extensive Refactoring Needed)"
        if ratio > 1: return " MODERATE (Manageable Side-Effects)"
        return " CLEAN (Independent / Leaf Node)"

    def get_ghost_graph(self, run_id: int, target_fqn: str) -> Dict[str, Any]:
        import networkx as nx
        from domain.simulation.graph_simulator import GraphSimulator
        from domain.simulation.impact_analyzer import ImpactAnalyzer
        from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType
        from infrastructure.persistence.models import ComponentRisk, GraphNode, GraphEdge
        
        db = self._get_db()
        try:
            nodes = db.query(GraphNode).filter(GraphNode.run_id == run_id).all()
            edges = db.query(GraphEdge).filter(GraphEdge.run_id == run_id).all()
            
            # Build DiGraph
            G = nx.DiGraph()
            
            if not nodes:
                # Fallback to local file
                graph_file = os.path.join(self.data_dir, f"graph_{run_id}.json")
                if os.path.exists(graph_file):
                    with open(graph_file, "r", encoding="utf-8") as f:
                        raw_graph = json.load(f)
                    for node_data in raw_graph.get("nodes", []):
                        G.add_node(node_data.get("id"), **node_data)
                    for link in raw_graph.get("links", []) or raw_graph.get("edges", []):
                        source = link.get("source") or link.get("source_id") or link.get("caller")
                        target = link.get("target") or link.get("target_id") or link.get("callee")
                        if source and target:
                            G.add_edge(source, target, type=link.get("type", "CALLS"))
                else:
                    return {"error": "Graph data not found"}
            else:
                for n in nodes:
                    metadata_raw = json.loads(n.metadata_json or "{}")
                    G.add_node(
                        n.id,
                        id=n.id,
                        name=n.name,
                        fqn=n.fqn,
                        type=n.node_type,
                        file_path=n.file_path,
                        metadata=metadata_raw
                    )
                for e in edges:
                    G.add_edge(e.source_id, e.target_id, type=e.edge_type)
            
            # Find all nodes belonging to the target file
            target_nodes = []
            for n, d in G.nodes(data=True):
                fpath = d.get("file_path") or d.get("fqn") or d.get("name", "")
                if fpath == target_fqn or d.get("fqn", "").startswith(target_fqn):
                    target_nodes.append(n)
                    
            if not target_nodes:
                base = os.path.basename(target_fqn).lower()
                for n, d in G.nodes(data=True):
                    fpath = d.get("file_path") or d.get("fqn") or d.get("name", "")
                    if base in fpath.lower() or base in d.get("fqn", "").lower():
                        target_nodes.append(n)

            # Get original risk map from DB
            risk_rows = db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
            original_risk_map = {row.component_name: row.final_risk for row in risk_rows}
            
            # Construct unit
            unit_label = os.path.basename(target_fqn).replace(".php", "")
            unit = ExtractionUnit(
                label=unit_label,
                type=ExtractionUnitType.SINGLE,
                nodes=target_nodes
            )
            
            # Simulate
            simulator = GraphSimulator(G)
            g_sim = simulator.simulate_extraction(unit)
            
            # Analyze
            analyzer = ImpactAnalyzer(G, original_risk_map)
            impact = analyzer.analyze(unit, g_sim)
            
            proxy_node = f"{unit_label}_Service"
            
            # Extract the immediate neighborhood of the proxy node in g_sim
            neighbor_nodes = set()
            if proxy_node in g_sim:
                neighbor_nodes.add(proxy_node)
                for pred in g_sim.predecessors(proxy_node):
                    neighbor_nodes.add(pred)
                for succ in g_sim.successors(proxy_node):
                    neighbor_nodes.add(succ)
                    
            # Build ghost graph response
            nodes_out = []
            for n in neighbor_nodes:
                d = g_sim.nodes[n]
                nodes_out.append({
                    "id": n,
                    "label": d.get("name") or os.path.basename(n) or n,
                    "type": d.get("type", "class"),
                    "file_path": d.get("file_path"),
                    "group": "extracted" if n == proxy_node else ("database" if d.get("type") == "table" else "monolith")
                })
                
            edges_out = []
            if proxy_node in g_sim:
                for u, v, data in g_sim.in_edges(proxy_node, data=True):
                    if u in neighbor_nodes:
                        edges_out.append({
                            "source": u,
                            "target": v,
                            "type": data.get("type", "CALLS")
                        })
                for u, v, data in g_sim.out_edges(proxy_node, data=True):
                    if v in neighbor_nodes:
                        edges_out.append({
                            "source": u,
                            "target": v,
                            "type": data.get("type", "CALLS")
                        })
                        
            return {
                "target": target_fqn,
                "proxy_node": proxy_node,
                "nodes": nodes_out,
                "edges": edges_out,
                "metrics": {
                    "before_risk": impact.before_risk,
                    "after_risk": impact.after_risk,
                    "risk_change": impact.risk_change,
                    "interface_complexity": impact.interface_complexity,
                    "data_isolation_difficulty": impact.data_isolation_difficulty
                }
            }
        finally:
            if self.db is None:
                db.close()
