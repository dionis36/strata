import json
import os
from datetime import datetime
from sqlalchemy.orm import Session

from infrastructure.persistence.models import Project, AnalysisRun, ComponentMetric, ComponentRisk, ComponentBehavior, ComponentDependency

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, name: str, root_path: str = None) -> Project:
        project = self.db.query(Project).filter(Project.name == name).first()
        if not project:
            project = Project(name=name, root_path=root_path)
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        elif root_path and project.root_path != root_path:
            project.root_path = root_path
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

    def update_metrics(self, run_id: int, metrics: dict) -> AnalysisRun:
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.total_files = metrics.get('total_files')
            run.total_loc = metrics.get('total_loc')
            run.avg_complexity = metrics.get('avg_complexity')
            run.avg_maintainability = metrics.get('avg_maintainability')
            run.total_classes = metrics.get('total_classes')
            run.total_edges = metrics.get('total_edges')
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
        node_types: dict = None,
        node_fqns: dict = None
    ):
        """Batch inserts all computed structural metrics for a run.

        Args:
            run_id: ID of the parent AnalysisRun.
            metrics_matrix: Dict of {node_id: metrics_dict} from MetricCalculator.
            node_types: Optional dict of {node_id: type_string} e.g. 'class', 'method'.
        """

        node_types = node_types or {}
        node_fqns = node_fqns or {}
        objects = []
        for component_id, metrics in metrics_matrix.items():
            cm = ComponentMetric(
                run_id=run_id,
                component_name=node_fqns.get(component_id, component_id),
                component_type=node_types.get(component_id, "class"),
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
                reachability_ratio=metrics.get('reachability_ratio', 0.0),
                domain_archetype=metrics.get('domain_archetype'),
                is_stateful=metrics.get('is_stateful', False),
                lcom=metrics.get('lcom', 0.0),
                wmc=metrics.get('wmc', 0)
            )
            objects.append(cm)
            

        if objects:
            self.db.bulk_save_objects(objects)
            self.db.commit()

    def save_graph_edges(self, run_id: int, edges: list):
        """
        Phase 3: Persists the graph edges to SQLite.
        """
        objects = [
            ComponentDependency(
                run_id=run_id,
                source_id=e.source_id,
                target_id=e.target_id,
                edge_type=e.edge_type.value
            )
            for e in edges
        ]
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
                domain_archetype=r.get("domain_archetype"),
                is_stateful=r.get("is_stateful", False),
                lcom=r.get("lcom", 0.0),
                wmc=r.get("wmc", 0),
                semantic_multiplier=r.get("semantic_multiplier", 1.0),
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


class LegacyRepository:
    """
    Phase 2: Handles persistence for specialized legacy insights (Era, Framework, Scores).
    """

    def __init__(self, db: Session):
        self.db = db

    def save_legacy_metrics(self, run_id: int, metrics: dict) -> None:
        from infrastructure.persistence.models import LegacyMetrics
        
        lm = LegacyMetrics(
            run_id=run_id,
            php_era=metrics.get("php_era"),
            version_score=metrics.get("version_score", 0.0),
            namespace_score=metrics.get("namespace_score", 0.0),
            db_layer_score=metrics.get("db_layer_score", 0.0),
            security_score=metrics.get("security_score", 0.0),
            testability_score=metrics.get("testability_score", 0.0),
            coupling_score=metrics.get("coupling_score", 0.0),
            total_modernization_score=metrics.get("total_modernization_score", 0.0),
            detected_framework=metrics.get("detected_framework"),
            hosting_risk_level=metrics.get("hosting_risk_level"),
            db_layer=metrics.get("db_layer"),
            auth_layer=metrics.get("auth_layer"),
            template_layer=metrics.get("template_layer"),
            autoloading_strategy=metrics.get("autoloading_strategy")
        )
        self.db.add(lm)
        self.db.commit()

    def get_legacy_metrics(self, run_id: int):
        from infrastructure.persistence.models import LegacyMetrics
        return (
            self.db.query(LegacyMetrics)
            .filter(LegacyMetrics.run_id == run_id)
            .first()
        )
