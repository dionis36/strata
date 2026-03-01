import traceback
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import AnalysisRunRepository
from infrastructure.parser_bridge import ParserBridge, FileScanner
from domain.models.graph_model import GraphModel
from domain.models.edge import EdgeType
from domain.services.metric_calculator import MetricCalculator

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisRunRepository(db)
        self.parser = ParserBridge()

    def run_analysis(self, project_id: int, project_path: str) -> dict:
        # Create "running" tracking record
        run = self.repo.create(project_id=project_id)
        
        try:
            # 1. File ingestion — no hardcoded file limit
            files = FileScanner.scan(project_path)
            
            # 2. Parse into typed AST representation (Phase A+B upgrade)
            nodes, edges = self.parser.parse_files(files, root_path=project_path)
            
            # 3. Build the fully-qualified dependency graph
            graph = GraphModel()
            for node in nodes:
                graph.add_node(node)
            for edge in edges:
                graph.add_edge(edge)
                
            total_files = len(files)
            total_classes = graph.get_class_count()
            total_edges = graph.get_edge_count()
            
            # 4. Calculate Phase 2 Structural Metrics on STRUCTURAL edge projection
            #    Excludes DB-write edges etc. to keep centrality semantically correct.
            STRUCTURAL_EDGES = [
                EdgeType.METHOD_CALL,
                EdgeType.INSTANTIATION,
                EdgeType.INHERITS,
                EdgeType.IMPLEMENTS,
            ]
            projected = MetricCalculator.project(
                graph.graph, edge_types=STRUCTURAL_EDGES
            )
            calculator = MetricCalculator(projected)
            metrics_matrix = calculator.calculate_all_metrics()

            # 5. Persist structural metrics in batch (include component type from graph)
            node_types = {
                n: data.get('type', 'class')
                for n, data in graph.graph.nodes(data=True)
            }
            self.repo.save_component_metrics(run.id, metrics_matrix, node_types)
            
            # 6. Save Graph JSON locally
            graph_data = graph.to_json_dict()
            self.repo.serialize_graph(run.id, graph_data)
            
            # 7. Persist minimal run metadata
            self.repo.update_metrics(run.id, total_files, total_classes, total_edges)
            self.repo.mark_completed(run.id)
            
            return {
                "run_id": run.id,
                "files": total_files,
                "classes": total_classes,
                "edges": total_edges
            }
            
        except Exception as e:
            error_msg = str(e) + "\n" + traceback.format_exc()
            self.repo.mark_failed(run.id, error_msg)
            raise e
