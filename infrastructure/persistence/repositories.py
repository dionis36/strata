import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from infrastructure.persistence.models import Project, AnalysisRun

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
        data_dir = os.path.abspath("./data")
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, f"graph_{run_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)
        return filepath
