import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from infrastructure.persistence.database import init_db, get_db
from infrastructure.persistence.repositories import ProjectRepository
from infrastructure.persistence.models import ComponentMetric
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
