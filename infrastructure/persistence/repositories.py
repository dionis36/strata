import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from infrastructure.persistence.models import Project, AnalysisRun, ComponentMetric, ComponentRisk, ComponentBehavior

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, name: str) -> Project:
        project = self.db.query(Project).filter(Project.name == name).first()
        if not project:
            project = Project(name=name)
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        return project

class AnalysisRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: int) -> AnalysisRun:
        run = AnalysisRun(project_id=project_id, status="started")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_metrics(self, run_id: int, total_files: int, total_classes: int, total_edges: int) -> AnalysisRun:
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.total_files = total_files
            run.total_classes = total_classes
            run.total_edges = total_edges
            self.db.commit()
            self.db.refresh(run)
        return run

    def mark_completed(self, run_id: int) -> AnalysisRun:
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(run)
        return run

    def mark_failed(self, run_id: int, error_message: str) -> AnalysisRun:
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.error_message = error_message
            self.db.commit()
            self.db.refresh(run)
        return run

    def serialize_graph(self, run_id: int, graph_data: dict) -> str:
        """
        Saves the graph JSON to the local /data directory.
        Returns the path saved.
        """
        data_dir = os.path.abspath("/data")
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, f"graph_{run_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)
        return filepath

    def save_component_metrics(
        self,
        run_id: int,
        metrics_matrix: dict,
        node_types: dict = None
    ):
        """Batch inserts all computed structural metrics for a run.

        Args:
            run_id: ID of the parent AnalysisRun.
            metrics_matrix: Dict of {node_id: metrics_dict} from MetricCalculator.
            node_types: Optional dict of {node_id: type_string} e.g. 'class', 'method'.
        """
        node_types = node_types or {}
        objects = []
        for component_name, metrics in metrics_matrix.items():
            cm = ComponentMetric(
                run_id=run_id,
                component_name=component_name,
                component_type=node_types.get(component_name, "class"),
                in_degree=metrics.get('in_degree', 0),
                out_degree=metrics.get('out_degree', 0),
                weighted_in=metrics.get('weighted_in', 0),
                weighted_out=metrics.get('weighted_out', 0),
                betweenness=metrics.get('betweenness', 0.0),
                closeness=metrics.get('closeness', 0.0),
                scc_id=metrics.get('scc_id', 0),
                scc_size=metrics.get('scc_size', 0),
                blast_radius=metrics.get('blast_radius', 0),
                fan_in_ratio=metrics.get('fan_in_ratio', 0.0),
                fan_out_ratio=metrics.get('fan_out_ratio', 0.0),
                scc_density=metrics.get('scc_density', 0.0),
                reachability_ratio=metrics.get('reachability_ratio', 0.0)
            )
            objects.append(cm)
            
        if objects:
            self.db.bulk_save_objects(objects)
            self.db.commit()


class BehaviorRepository:
    """Phase 4 persistence — stores ComponentBehavior rows."""

    def __init__(self, db: Session):
        self.db = db

    def save_behavior_metrics(self, run_id: int, metrics: list[dict]) -> None:
        objects = [
            ComponentBehavior(
                run_id=run_id,
                component_name=b["component_name"],
                write_intensity=b.get("write_intensity", 0.0),
                table_dependencies=b.get("table_dependencies", 0),
                shared_table_pressure=b.get("shared_table_pressure", 0.0)
            )
            for b in metrics
        ]
        if objects:
            self.db.bulk_save_objects(objects)
            self.db.commit()

    def get_behavior_by_run(self, run_id: int) -> list:
        return (
            self.db.query(ComponentBehavior)
            .filter(ComponentBehavior.run_id == run_id)
            .all()
        )



class RiskRepository:
    """Phase 3 persistence — stores and retrieves ComponentRisk rows."""

    def __init__(self, db: Session):
        self.db = db

    def save_risk_scores(self, run_id: int, risk_results: list[dict]) -> None:
        """Bulk-insert all risk score records for a run.

        Args:
            run_id: ID of the parent AnalysisRun.
            risk_results: List of dicts from RiskService, one per component.
        """
        objects = [
            ComponentRisk(
                run_id=run_id,
                component_name=r["component_name"],
                component_type=r.get("component_type", "class"),
                norm_betweenness=r.get("norm_betweenness", 0.0),
                norm_blast_radius=r.get("norm_blast_radius", 0.0),
                norm_in_degree=r.get("norm_in_degree", 0.0),
                norm_out_degree=r.get("norm_out_degree", 0.0),
                criticality_index=r.get("criticality_index", 0.0),
                instability=r.get("instability", 0.0),
                cycle_flag=r.get("cycle_flag", 0),
                coupling_pressure=r.get("coupling_pressure", 0.0),
                risk_score=r["risk_score"],
                risk_level=r["risk_level"],
                behavioral_factor=r.get("behavioral_factor", 0.0),
                final_risk=r.get("final_risk", r["risk_score"]),
            )
            for r in risk_results
        ]
        if objects:
            self.db.bulk_save_objects(objects)
            self.db.commit()

    def get_risk_by_run(self, run_id: int) -> list[ComponentRisk]:
        """Return all risk rows for a run, sorted by risk_score descending."""
        return (
            self.db.query(ComponentRisk)
            .filter(ComponentRisk.run_id == run_id)
            .order_by(ComponentRisk.final_risk.desc())
            .all()
        )
