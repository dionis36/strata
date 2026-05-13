import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from infrastructure.persistence.database import init_db, get_db
from infrastructure.persistence.repositories import ProjectRepository, RiskRepository
from application.services.explanation_service import ExplanationService
from application.services.extraction_service import ExtractionService

from infrastructure.persistence.models import ComponentMetric, ComponentRisk
from application.services.analysis_service import AnalysisService

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    logger.info("API started")
    init_db()
    yield
    # On shutdown
    logger.info("API shutdown")

app = FastAPI(title="Strata API", version="0.1", lifespan=lifespan)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Verify db connectivity
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "version": "0.1",
            "database": "connected",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database connection failed during health check: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

class AnalyzeRequest(BaseModel):
    project_path: str
    project_name: str = "default_project"


@app.post("/analyze")
def analyze_project(req: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        project_repo = ProjectRepository(db)
        project = project_repo.get_or_create(req.project_name)
        
        service = AnalysisService(db)
        result = service.run_analysis(project.id, req.project_path)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/{run_id}")
def get_metrics(run_id: int, db: Session = Depends(get_db)):
    try:
        metrics = db.query(ComponentMetric).filter(ComponentMetric.run_id == run_id).all()
        components = []
        for m in metrics:
            components.append({
                "name": m.component_name,
                "type": m.component_type,
                "in_degree": m.in_degree,
                "out_degree": m.out_degree,
                "betweenness": m.betweenness,
                "scc_size": m.scc_size,
                "blast_radius": m.blast_radius
            })
        return {
            "run_id": run_id,
            "components": components
        }
    except Exception as e:
        logger.error(f"Failed to fetch metrics for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk/{run_id}")
def get_risk(run_id: int, db: Session = Depends(get_db)):
    """Returns Phase 3 structural risk scores for a run, sorted by risk_score desc."""
    try:
        repo = RiskRepository(db)
        rows = repo.get_risk_by_run(run_id)
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No risk data found for run_id={run_id}. Run POST /analyze first."
            )
        components = [
            {
                "name":              r.component_name,
                "type":              r.component_type,
                "risk_score":        r.risk_score,
                "risk_level":        r.risk_level,
                "behavioral_factor": r.behavioral_factor,
                "final_risk":        r.final_risk,
                "criticality_index": r.criticality_index,
                "instability":       r.instability,
                "cycle_flag":        r.cycle_flag,
                "coupling_pressure": r.coupling_pressure,
            }
            for r in rows
        ]
        return {"run_id": run_id, "components": components}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch risk for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explain/{run_id}")
def get_explanation(run_id: int, db: Session = Depends(get_db)):
    """Phase 4.5: Returns deterministic, rule-based explanations for all components in a run.

    Each component explanation includes:
      - Which rules fired (category, severity, message)
      - Evidence: dependent components, SCC members, source file path
    """
    try:
        # Verify risk data exists first (ExplanationService depends on it)
        repo = RiskRepository(db)
        if not repo.get_risk_by_run(run_id):
            raise HTTPException(
                status_code=404,
                detail=f"No risk data found for run_id={run_id}. Run POST /analyze first."
            )

        service = ExplanationService(db)
        explanations = service.explain_run(run_id)
        return {"run_id": run_id, "components": explanations}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate explanations for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/extraction/{run_id}")
def get_extraction(run_id: int, db: Session = Depends(get_db)):
    """Phase 5: Returns simulated architecture extraction candidates and impact metrics."""
    try:
        repo = RiskRepository(db)
        if not repo.get_risk_by_run(run_id):
            raise HTTPException(
                status_code=404,
                detail=f"No risk data found for run_id={run_id}. Run POST /analyze first."
            )

        service = ExtractionService(db)
        candidates = service.analyze_extraction(run_id)
        return {"run_id": run_id, "candidates": candidates}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate extraction candidates for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    """Returns a list of all completed analysis runs with metadata."""
    from infrastructure.persistence.models import AnalysisRun
    try:
        runs = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).all()
        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
                "total_files": r.total_files,
                "total_classes": r.total_classes,
                "total_edges": r.total_edges
            }
            for r in runs
        ]
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from application.services.tree_service import TreeService
@app.get("/graph/{run_id}/includes")
def get_includes(run_id: int, db: Session = Depends(get_db)):
    try:
        service = TreeService(db)
        return service.get_bootstrap_analysis(run_id)
    except Exception as e:
        logger.error(f"Failed to generate include tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from application.services.layer_service import LayerService
@app.get("/layer-analysis/{run_id}")
def get_layer_analysis(run_id: int, db: Session = Depends(get_db)):
    try:
        service = LayerService(db)
        return service.get_layered_analysis(run_id)
    except Exception as e:
        logger.error(f"Failed to generate layer analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from application.services.database_intelligence_service import DatabaseIntelligenceService
@app.get("/db-intelligence/{run_id}")
def get_db_intelligence(run_id: int, db: Session = Depends(get_db)):
    try:
        service = DatabaseIntelligenceService(db)
        return service.get_db_intelligence(run_id)
    except Exception as e:
        logger.error(f"Failed to generate DB intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Phase 5: Enterprise Reporting ---
from application.services.report_service import ReportService

@app.get("/report/roadmap/{run_id}")
def get_roadmap(run_id: int, db: Session = Depends(get_db)):
    try:
        service = ReportService(db)
        return service.generate_roadmap(run_id)
    except Exception as e:
        logger.error(f"Failed to generate roadmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/graphviz/{run_id}")
def get_graphviz(run_id: int, db: Session = Depends(get_db)):
    try:
        service = ReportService(db)
        return {"dot": service.generate_graphviz(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/neo4j/{run_id}")
def get_neo4j(run_id: int, db: Session = Depends(get_db)):
    try:
        service = ReportService(db)
        return {"cypher": service.generate_neo4j_cypher(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/ai-chunks/{run_id}")
def get_ai_chunks(run_id: int, db: Session = Depends(get_db)):
    try:
        service = ReportService(db)
        return {"chunks": service.generate_ai_chunks(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
