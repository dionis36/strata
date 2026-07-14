import logging
import yaml
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.models import Base, Project, Run
from application.services.metrics_service import MetricsService
from application.services.risk_service import RiskService
from application.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

class ExperimentRunner:
    """
    Spins up an isolated in-memory database to execute the entire Strata 
    intelligence pipeline (Phases 2-5) without polluting the main database.
    """
    def __init__(self, config_path: str = "evaluation/config.yaml"):
        import os
        if not os.path.exists(config_path):
            self.config = {}
        else:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            
        # Natively isolated for multi-run safety
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def _seed_environment(self, db, run_id: int) -> int:
        project = Project(name=f"Evaluation_Graph_{run_id}", git_url="memory", created_at=datetime.utcnow())
        db.add(project)
        db.commit()
        
        run = Run(id=run_id, project_id=project.id, commit_hash="ablation", analyzed_at=datetime.utcnow())
        db.add(run)
        db.commit()
        return project.id

    def execute_full_pipeline(self, run_id: int):
        """
        Executes the exact production pipeline completely mapped inside the 
        volitile memory space. Evaluates the config map constraints natively.
        """
        with self.SessionLocal() as db:
            project_id = self._seed_environment(db, run_id)
            
            # Phase 2: Structural Metrics Extraction
            metrics_service = MetricsService(db)
            metrics_service.analyze_project(project_id, run_id)
            
            # Phase 3 & 4: Risk and DB Behavior Calculation
            # Will be injected with config weights continuously
            risk_service = RiskService(db)
            risk_weights = self.config.get("weights", {}).get("risk_factors", None)
            risk_service.compute_risk(run_id, weight_overrides=risk_weights)
            
            # Phase 5: Architecture Simulation & Candidate Extraction
            # Will be injected with config weights continuously
            ext_service = ExtractionService(db)
            ext_weights = self.config.get("weights", {}).get("cluster_factors", None)
            candidates = ext_service.analyze_extraction(run_id, weight_overrides=ext_weights)
            
            return candidates
