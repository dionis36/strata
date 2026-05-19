import traceback
import logging
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import AnalysisRunRepository, BehaviorRepository
from infrastructure.parser_bridge import ParserBridge, FileScanner
from domain.models.graph_model import GraphModel
from domain.models.edge import Edge, EdgeType
from domain.models.node import Node, NodeType
from domain.services.metric_calculator import MetricCalculator
from application.services.risk_service import RiskService
from domain.behavior.write_analyzer import WriteAnalyzer
from domain.behavior.behavioral_metrics import BehavioralMetricsCalculator
from application.services.legacy_analysis_service import LegacyAnalysisService

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisRunRepository(db)
        self.parser = ParserBridge(self.db)


    def run_analysis(self, project_id: int, project_path: str) -> dict:
        # Create "running" tracking record
        # Update project root_path if provided
        from infrastructure.persistence.models import Project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.root_path = project_path
            self.db.commit()

        run = self.repo.create(project_id=project_id)
        
        try:
            # 1. File ingestion
            files = FileScanner.scan(project_path)
            
            # --- Module C.2: Incremental Caching ---
            from infrastructure.persistence.models import FileCache
            import hashlib
            from typing import List
            import json
            
            all_nodes: List[Node] = []
            all_edges: List[Edge] = []
            file_metrics = {} # path -> {loc, complexity}
            to_parse = []
            
            # Prefetch existing cache
            existing_cache = {c.file_path: c for c in self.db.query(FileCache).all()}
            
            for path in files:
                with open(path, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                cached = existing_cache.get(path)

                if cached and cached.file_hash == file_hash:
                    n_data = json.loads(cached.nodes_data)
                    e_data = json.loads(cached.edges_data)
                    all_nodes.extend([Node(**n) for n in n_data])
                    all_edges.extend([Edge(**e) for e in e_data])
                    
                    # Recover stored LOC/Complexity from metadata if present
                    # For now, we'll re-extract from nodes if needed, but better to cache it.
                    # As a fallback for this upgrade, we'll re-parse if metrics missing from cache.
                    to_parse.append(path) 
                else:
                    to_parse.append(path)
            
            # 2. Parse
            if to_parse:
                # The parser bridge needs to return the new metadata
                new_nodes, new_edges = self.parser.parse_files(to_parse, root_path=project_path)
                all_nodes.extend(new_nodes)
                all_edges.extend(new_edges)
                
                # Extract file-level metrics from nodes metadata
                for n in new_nodes:
                    if getattr(n, "node_type", None) == NodeType.FILE:
                        meta = getattr(n, "metadata", {})
                        file_metrics[n.id] = {
                            "loc": meta.get("loc", 0),
                            "complexity": meta.get("complexity", 1)
                        }

            nodes, edges = all_nodes, all_edges
            
            # 3. Build graph
            graph = GraphModel()
            for node in nodes:
                graph.add_node(node)
                
                # 3.5 Phase 4 Behavioral Extraction
                if getattr(node, "node_type", None) == NodeType.CLASS and getattr(node, "file_path", None):
                    try:
                        with open(node.file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                        behavior_res = WriteAnalyzer.analyze_file(code_content)
                        for table_name in behavior_res.get("tables", []):
                            table_node_id = f"table::{table_name}"
                            if not graph.graph.has_node(table_node_id):
                                table_node = Node(id=table_node_id, name=table_name, node_type=NodeType.TABLE)
                                graph.add_node(table_node)
                            graph.add_edge(Edge(source_id=node.id, target_id=table_node_id, edge_type=EdgeType.WRITES_TO))
                    except Exception:
                        pass
            for edge in edges:
                graph.add_edge(edge)
            
            self.repo.save_graph_edges(run.id, edges)
                
            total_files = len(files)
            total_classes = graph.get_class_count()
            total_methods = graph.get_method_count()
            total_functions = graph.get_function_count()
            total_namespaces = graph.get_namespace_count()
            total_edges = graph.get_edge_count()
            
            # Aggregate Dashboard KPIs
            total_loc = sum(m["loc"] for m in file_metrics.values())
            total_complexity = sum(m["complexity"] for m in file_metrics.values())
            avg_complexity = total_complexity / total_files if total_files > 0 else 0
            
            # Heuristic Maintainability Index (MI)
            # Higher is better. Based on LOC and Complexity density.
            import math
            def calc_mi(loc, comp):
                if loc <= 0: return 100
                # Basic logarithmic penalty for scale and linear penalty for complexity
                score = 171 - (0.23 * comp) - (16.2 * math.log(loc))
                return max(0, min(100, (score * 100 / 171)))
            
            avg_mi = sum(calc_mi(m["loc"], m["complexity"]) for m in file_metrics.values()) / total_files if total_files > 0 else 100

            # 4. Calculate Phase 2 Structural Metrics
            STRUCTURAL_EDGES = [EdgeType.CALLS, EdgeType.INHERITS, EdgeType.DEPENDS_ON, EdgeType.DECLARES]
            projected = MetricCalculator.project(graph.graph, edge_types=STRUCTURAL_EDGES)
            calculator = MetricCalculator(projected)
            metrics_matrix = calculator.calculate_all_metrics()

            # 5. Persist
            node_types = {n: data.get('type', 'class') for n, data in graph.graph.nodes(data=True)}
            node_fqns = {n: data.get('fqn', n) for n, data in graph.graph.nodes(data=True)}
            self.repo.save_component_metrics(run.id, metrics_matrix, node_types, node_fqns)

            # 5.2 Behavioral
            behavior_calc = BehavioralMetricsCalculator(graph)
            behavior_metrics = behavior_calc.calculate_metrics()
            if behavior_metrics:
                BehaviorRepository(self.db).save_behavior_metrics(run.id, behavior_metrics)

            # 5.5 Risk
            risk_service = RiskService(self.db)
            risk_service.compute_risk(run.id)
            
            # --- Phase 2: Legacy Domain Intelligence ---
            legacy_service = LegacyAnalysisService(self.db)
            nodes_dict = [n.model_dump(mode='json') for n in nodes]
            edges_dict = [e.model_dump(mode='json') for e in edges]
            legacy_insights = legacy_service.analyze_legacy_environment(run.id, nodes_dict, edges_dict)

            # 6. Save Graph JSON
            graph_data = graph.to_json_dict()
            self.repo.serialize_graph(run.id, graph_data)
            
            # 7. Persist minimal run metadata
            self.repo.update_metrics(run.id, {
                "total_files": total_files,
                "total_loc": total_loc,
                "avg_complexity": avg_complexity,
                "avg_maintainability": avg_mi,
                "total_classes": total_classes,
                "total_methods": total_methods,
                "total_functions": total_functions,
                "total_namespaces": total_namespaces,
                "total_edges": total_edges
            })
            self.repo.mark_completed(run.id)
            
            return {
                "run_id": run.id,
                "files": total_files,
                "classes": total_classes,
                "edges": total_edges,
                "loc": total_loc,
                "avg_complexity": round(avg_complexity, 2),
                "avg_mi": round(avg_mi, 2),
                "legacy_insights": legacy_insights
            }
            
        except Exception as e:
            error_msg = str(e) + "\n" + traceback.format_exc()
            self.repo.mark_failed(run.id, error_msg)
            raise e
