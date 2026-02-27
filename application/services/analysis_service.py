import traceback
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import AnalysisRunRepository
from infrastructure.parser_bridge import ParserBridge, FileScanner
from domain.models.graph_model import GraphModel

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisRunRepository(db)
        self.parser = ParserBridge()

    def run_analysis(self, project_id: int, project_path: str) -> dict:
        # Create "running" tracking record
        run = self.repo.create(project_id=project_id)
        
        try:
            # 1. File ingestion (Minimal)
            files = FileScanner.scan(project_path)
            
            # 2. Parse into minimal AST representation
            nodes, edges = self.parser.parse_files(files)
            
            # 3. Construct minimal dependency graph
            graph = GraphModel()
            for node in nodes:
                graph.add_node(node)
            for edge in edges:
                graph.add_edge(edge)
                
            total_files = len(files)
            total_classes = graph.get_class_count()
            total_edges = graph.get_edge_count()
            
            # 4. Save Graph JSON locally
            graph_data = graph.to_json_dict()
            self.repo.serialize_graph(run.id, graph_data)
            
            # 5. Persist minimal run metadata
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
