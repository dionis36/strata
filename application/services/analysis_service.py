import traceback
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import AnalysisRunRepository
from infrastructure.parser_bridge import ParserBridge, FileScanner
from domain.models.graph_model import GraphModel
from domain.models.edge import Edge, EdgeType
from domain.models.node import Node, NodeType
from domain.services.metric_calculator import MetricCalculator
from application.services.risk_service import RiskService
from domain.behavior.write_analyzer import WriteAnalyzer
from domain.behavior.behavioral_metrics import BehavioralMetricsCalculator
from infrastructure.persistence.repositories import BehaviorRepository

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
                
                # 3.5 Phase 4 Behavioral Extraction
                # We do this here since the ParserBridge has already mapped file_paths to Node IDs
                if getattr(node, "node_type", None) == NodeType.CLASS and getattr(node, "file_path", None):
                    try:
                        with open(node.file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                        behavior_res = WriteAnalyzer.analyze_file(code_content)
                        for table_name in behavior_res.get("tables", []):
                            # Ensure TABLE node exists
                            table_node_id = f"table::{table_name}"
                            if not graph.graph.has_node(table_node_id):
                                table_node = Node(id=table_node_id, name=table_name, node_type=NodeType.TABLE)
                                graph.add_node(table_node)
                            # Add WRITES_TO edge
                            graph.add_edge(Edge(source_id=node.id, target_id=table_node_id, edge_type=EdgeType.WRITES_TO))
                    except Exception:
                        pass # Silently ignore unreadable files during behavior extraction


            for edge in edges:
                graph.add_edge(edge)
            
            # 3.8 Phase 3: Persist the graph edges to SQLite (CSOT)
            self.repo.save_graph_edges(run.id, edges)
                
            total_files = len(files)
            total_classes = graph.get_class_count()
            total_edges = graph.get_edge_count()

            
            # 4. Calculate Phase 2 Structural Metrics on STRUCTURAL edge projection
            #    Excludes DB-write edges etc. to keep centrality semantically correct.
            STRUCTURAL_EDGES = [
                EdgeType.CALLS,
                EdgeType.INHERITS,
                EdgeType.DEPENDS_ON,
            ]
            projected = MetricCalculator.project(
                graph.graph, edge_types=STRUCTURAL_EDGES
            )
            calculator = MetricCalculator(projected)
            metrics_matrix = calculator.calculate_all_metrics()


            # 5. Persist structural metrics in batch (include component type and readable FQN from graph)
            node_types = {}
            node_fqns = {}
            for n, data in graph.graph.nodes(data=True):
                node_types[n] = data.get('type', 'class')
                node_fqns[n] = data.get('fqn', n)
            
            self.repo.save_component_metrics(run.id, metrics_matrix, node_types, node_fqns)

            # 5.2 Phase 4: Compute behavioral metrics based on WRITES edges
            behavior_calc = BehavioralMetricsCalculator(graph)
            behavior_metrics = behavior_calc.calculate_metrics()
            if behavior_metrics:
                b_repo = BehaviorRepository(self.db)
                b_repo.save_behavior_metrics(run.id, behavior_metrics)

            # 5.5 Phase 3: Compute structural risk scores from Phase 2 metrics.
            #     Runs synchronously — risk scores are always ready with the analysis.
            risk_service = RiskService(self.db)
            risk_service.compute_risk(run.id)

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
