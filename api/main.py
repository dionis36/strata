import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from infrastructure.persistence.database import init_db, get_db
from infrastructure.persistence.repositories import ProjectRepository, RiskRepository
from application.services.explanation_service import ExplanationService
from application.services.extraction_service import ExtractionService

from infrastructure.persistence.models import ComponentMetric, ComponentRisk
from application.services.analysis_service import AnalysisService
from application.services.tree_service import TreeService
from application.services.layer_service import LayerService
from application.services.database_intelligence_service import DatabaseIntelligenceService
from application.services.global_state_service import GlobalStateService
from application.services.legacy_intelligence_service import LegacyIntelligenceService
from application.services.boundary_intelligence_service import BoundaryIntelligenceService
from application.services.security_risk_service import SecurityRiskService
from application.services.advisory_service import AdvisoryService
from application.services.simulation_service import SimulationService
from application.services.report_service import ReportService

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

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- App Description ---
DESCRIPTION = """
**Strata** is an enterprise-grade Modernization Intelligence Platform designed to de-risk the transformation of legacy PHP monoliths into modern, distributed architectures.

### 🔬 The Strata Methodology
Unlike traditional static analysis, Strata converts raw source code into a **Structural Intelligence Graph**. By parsing Abstract Syntax Trees (AST) and projecting them into a NetworkX-backed mathematical model, we identify the hidden "gravity" of your codebase—the components that hold the monolith together and the chokepoints that prevent agility.

### The Intelligence Stack
The system is organized into four strategic pillars, mirrored in the API and UI:

**1. Architectural Discovery**
- **Monolith Navigator**: Recursive structural exploration and file classification.
- **Layered Structure**: Inference of semantic layers (UI, Service, Data, Infrastructure).
- **System Topology**: High-level relationship mapping and Bounded Context clustering.

**2. Intelligence Reports**
- **Database Intelligence**: Detection of SQL operations and table ownership mapping.
- **Runtime & Global State**: Audit of superglobals (`$_SESSION`, `$_POST`) and shared mutable state.
- **Legacy PHP Intelligence**: Expert detection of PHP 4/5 era anti-patterns (e.g., `mysql_*`).
- **Modernization Risk**: Multi-dimensional risk scoring (Structural, Behavioral, Complexity).
- **Boundary Intelligence**: Detection of MVC entrypoints and external API/Vendor interfaces.

**3. Strategic Advisory**
- **Modernization Decision Engine**: Rule-based strategy selection (Refactor, Rewrite, Strangler Fig).
- **Extraction Simulator**: Predictive impact analysis and component blast radius.
- **Strategic Roadmap**: Prioritized modernization timeline and effort estimation.
- **Legacy Bootstrapper**: Automated generation of Composer and PSR-4 namespace mappings.

**4. Enterprise Reporting**
- Generating Graphviz/DOT visualizations, Neo4j Cypher imports, and AI-ready knowledge chunks.

---
*Developed by the Strata Team.*
"""

app = FastAPI(
    title="Strata: Modernization Advisory API",
    description=DESCRIPTION,
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs to use custom one with theme toggle
    redoc_url=None,
    contact={
        "name": "Strata Support",
        "url": "https://github.com/dionis36/strata",
    }
)

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

@app.get("/docs", include_in_schema=False)
async def scalar_html():
    """Native, premium API documentation using Scalar."""
    return HTMLResponse(
        content=f"""
        <!doctype html>
        <html>
          <head>
            <title>{app.title}</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
              body {{ margin: 0; }}
            </style>
          </head>
          <body>
            <script
              id="api-reference"
              data-url="{app.openapi_url}"></script>
            <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
          </body>
        </html>
        """
    )

# --- Schemas (Pydantic Models) ---

class Message(BaseModel):
    detail: str

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    version: str = Field(..., example="0.2.0")
    database: str = Field(..., example="connected")
    timestamp: str

class AnalyzeRequest(BaseModel):
    project_path: str = Field(..., description="Absolute path inside the container to the legacy source code.", example="/data/test_project")
    project_name: str = Field("default_project", description="Human-readable name for the project.")

class AnalyzeResponse(BaseModel):
    run_id: int = Field(..., example=1)
    files: int = Field(..., example=100)
    classes: int = Field(..., example=85)
    edges: int = Field(..., example=120)
    loc: int = Field(..., example=5000)
    avg_complexity: float = Field(..., example=3.5)
    avg_mi: float = Field(..., example=75.0)
    legacy_insights: Dict[str, Any] = Field(..., example={})

class ComponentMetricSchema(BaseModel):
    name: str = Field(..., example="UserController")
    type: str = Field(..., example="class")
    in_degree: int = Field(..., example=5)
    out_degree: int = Field(..., example=2)
    betweenness: float = Field(..., example=0.15)
    scc_size: int = Field(..., example=1)
    blast_radius: int = Field(..., example=3)

class MetricsResponse(BaseModel):
    run_id: int
    components: List[ComponentMetricSchema]

class RiskSchema(BaseModel):
    name: str
    type: str
    risk_score: float = Field(..., example=0.85)
    risk_level: str = Field(..., example="Critical")
    behavioral_factor: float
    final_risk: float
    criticality_index: float
    instability: float
    cycle_flag: bool
    coupling_pressure: float

class RiskResponse(BaseModel):
    run_id: int
    components: List[RiskSchema]

class RuleFiring(BaseModel):
    category: str
    severity: str
    message: str

class ExplanationSchema(BaseModel):
    name: str
    rules: List[RuleFiring]
    evidence: Dict[str, Any]

class ExplanationResponse(BaseModel):
    run_id: int
    components: List[ExplanationSchema]

class ExtractionCandidate(BaseModel):
    name: str
    cohesion: float
    coupling: float
    independence_score: float

class ExtractionResponse(BaseModel):
    run_id: int
    candidates: List[ExtractionCandidate]

class AnalysisRunSchema(BaseModel):
    id: int
    project_id: int
    status: str
    started_at: str
    completed_at: Optional[str]
    total_files: int
    total_loc: int
    avg_complexity: float
    avg_maintainability: float
    total_classes: int
    total_edges: int
    error_message: Optional[str] = None

class GraphvizResponse(BaseModel):
    dot: str

class DashboardResponse(BaseModel):
    project: Dict[str, Any]
    latest_run: Optional[Dict[str, Any]]

# --- API Endpoints ---

@app.get("/health", 
         response_model=HealthResponse, 
         tags=["System"],
         summary="Check API and Database health")
def health_check(db: Session = Depends(get_db)):
    """Verifies that the API is running and the SQLite database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "version": "0.2.0",
            "database": "connected",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database connection failed during health check: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


def background_synthesize_intelligence(run_id: int):
    from infrastructure.persistence.database import SessionLocal
    from infrastructure.persistence.models import AnalysisRun, ComponentRisk, LegacyMetrics
    from application.services.publishing.ai_advisory_service import AIAdvisoryService
    import json
    
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run: return
        # 1. Synthesize exec summary
        run.status = "synthesizing_summary"
        db.commit()
        
        class DummyCtx:
            project_name = "Strata Analysis"
            total_files = run.total_files
            lines_of_code = run.total_loc
            framework = "Unknown"
            php_era = "Unknown"
            overall_readiness = 50.0
            architectural_footprint = {}
            
        ctx = DummyCtx()
        legacy = db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        if legacy:
            ctx.framework = legacy.detected_framework or "Unknown"
            ctx.php_era = legacy.php_era or "Unknown"
            ctx.overall_readiness = legacy.total_modernization_score * 10 if legacy.total_modernization_score else 0.0
            
        from application.services.layer_service import LayerService
        try:
            layer_service = LayerService(db)
            l_data = layer_service.get_layered_analysis(run_id)
            dirs = l_data.get("layer_1", {}).get("directories", {})
            models = controllers = views = 0
            for info in dirs.values():
                for f in info.get("files", []):
                    role = f.get("role", "file") if isinstance(f, dict) else "file"
                    if role == "model": models += 1
                    elif role == "controller": controllers += 1
                    elif role == "view": views += 1
            ctx.architectural_footprint = {
                "Models": models,
                "Controllers": controllers,
                "Views": views
            }
        except Exception:
            pass
            
        ai_service = AIAdvisoryService()
        summary = ai_service.synthesize_executive_summary(ctx, legacy)
        
        run.ai_executive_summary_json = json.dumps(summary)
        run.error_message = None
        run.status = "intelligence_ready"
        db.commit()
    except Exception as e:
        logger.error(f"Background AI synthesis failed: {e}")
        try:
            run.error_message = str(e)
            fallback = ai_service._generate_summary_fallback(ctx)
            run.ai_executive_summary_json = json.dumps(fallback)
            run.status = "intelligence_failed" # We mark it as failed so the "Retry" button appears, but we still have fallback data!
            db.commit()
        except Exception as fallback_e:
            logger.error(f"Fallback synthesis also failed: {fallback_e}")
            run.error_message = f"Fallback error: {fallback_e}"
            run.status = "intelligence_failed"
            db.commit()
    finally:
        db.close()

@app.post("/runs/{run_id}/retry_intelligence",
          tags=["Reporting & Visuals"],
          summary="Retry failed AI synthesis")
def retry_intelligence(run_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers the background intelligence synthesis for a run that failed."""
    from infrastructure.persistence.models import AnalysisRun
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    run.status = "analysis_complete"
    db.commit()
    
    background_tasks.add_task(background_synthesize_intelligence, run_id)
    return {"message": "AI Synthesis retry queued.", "run_id": run_id}

@app.post("/analyze", 
          response_model=AnalyzeResponse, 
          tags=["Core Analysis"],
          summary="Trigger deep structural analysis")
def analyze_project(req: AnalyzeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Initiates a new analysis run for a given project directory.
    - Scans all PHP files.
    - Builds the dependency graph.
    - Projects structural metrics.
    - Persists results to SQLite.
    """
    try:
        project_repo = ProjectRepository(db)
        project = project_repo.get_or_create(req.project_name)
        
        service = AnalysisService(db)
        result = service.run_analysis(project.id, req.project_path)
        
        # result might be a dict or a Pydantic model
        run_id = result.get("run_id") if isinstance(result, dict) else result.run_id
        
        from infrastructure.persistence.models import AnalysisRun
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.status = "analysis_complete"
            db.commit()
            
        background_tasks.add_task(background_synthesize_intelligence, run_id)
        
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/{run_id}", 
         response_model=MetricsResponse, 
         tags=["Core Analysis"],
         summary="Fetch raw structural metrics")
def get_metrics(run_id: int, db: Session = Depends(get_db)):
    """Returns the NetworkX-derived structural metrics for every component found in the run."""
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


@app.get("/risk/{run_id}", 
         response_model=RiskResponse, 
         tags=["Modernization Advisory"],
         summary="Audit structural risk scores")
def get_risk(run_id: int, db: Session = Depends(get_db)):
    """Returns Phase 3 structural risk scores, identifying high-instability and high-coupling areas."""
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


@app.get("/explain/{run_id}", 
         response_model=ExplanationResponse, 
         tags=["Modernization Advisory"],
         summary="Get rule-based risk explanations")
def get_explanation(run_id: int, db: Session = Depends(get_db)):
    """
    Phase 4.5: Returns deterministic, rule-based explanations for all components.
    Includes firing rules, severity levels, and specific structural evidence.
    """
    try:
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


@app.get("/extraction/{run_id}", 
         response_model=ExtractionResponse, 
         tags=["Modernization Advisory"],
         summary="Identify extraction candidates")
def get_extraction(run_id: int, db: Session = Depends(get_db)):
    """Phase 5: Returns candidates for microservice or module extraction based on independence metrics."""
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


@app.get("/runs", 
         response_model=List[AnalysisRunSchema], 
         tags=["Core Analysis"],
         summary="List all analysis runs")
def list_runs(db: Session = Depends(get_db)):
    """Returns a history of all analysis attempts with high-level file and class counts."""
    from infrastructure.persistence.models import AnalysisRun
    try:
        runs = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).all()
        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "total_files": r.total_files or 0,
                "total_loc": r.total_loc or 0,
                "avg_complexity": r.avg_complexity or 0.0,
                "avg_maintainability": r.avg_maintainability or 0.0,
                "total_classes": r.total_classes or 0,
                "total_edges": r.total_edges or 0,
                "error_message": r.error_message
            }
            for r in runs
        ]
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{run_id}/includes", tags=["Intelligence Modules"], summary="Bootstrap include tree")
def get_includes(run_id: int, db: Session = Depends(get_db)):
    """Analyzes the PHP `include/require` structure to find entrypoint bottlenecks."""
    try:
        service = TreeService(db)
        return service.get_bootstrap_analysis(run_id)
    except Exception as e:
        logger.error(f"Failed to generate include tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/layer-analysis/{run_id}", tags=["Intelligence Modules"], summary="Layered architectural analysis")
def get_layer_analysis(run_id: int, db: Session = Depends(get_db)):
    """Maps components into theoretical layers (UI, Service, Data) based on dependency direction."""
    try:
        service = LayerService(db)
        return service.get_layered_analysis(run_id)
    except Exception as e:
        logger.error(f"Failed to generate layer analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/db-intelligence/{run_id}", tags=["Intelligence Modules"], summary="Database interaction audit")
def get_db_intelligence(run_id: int, db: Session = Depends(get_db)):
    """Identifies which components perform direct SQL or ORM operations."""
    try:
        service = DatabaseIntelligenceService(db)
        return service.get_db_intelligence(run_id)
    except Exception as e:
        logger.error(f"Failed to generate DB intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/global-state/{run_id}", tags=["Intelligence Modules"], summary="Global state usage report")
def get_global_state(run_id: int, db: Session = Depends(get_db)):
    """Module F: Tracks usage of globals, superglobals ($GLOBALS, $_SESSION), and static patterns."""
    try:
        service = GlobalStateService(db)
        return service.get_global_state_intelligence(run_id)
    except Exception as e:
        logger.error(f"Failed to generate global state intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/legacy-intelligence/{run_id}", tags=["Intelligence Modules"], summary="Legacy PHP pattern detection")
def get_legacy_intelligence(run_id: int, db: Session = Depends(get_db)):
    """Module G: Detects anti-patterns common in PHP 5.x/4.x era codebases."""
    try:
        service = LegacyIntelligenceService(db)
        return service.get_legacy_intelligence(run_id)
    except Exception as e:
        logger.error(f"Failed to generate legacy intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/boundary-intelligence/{run_id}", tags=["Intelligence Modules"], summary="Boundary & Interface audit")
def get_boundary_intelligence(run_id: int, db: Session = Depends(get_db)):
    """Module C+: Identifies API entrypoints and external vendor touchpoints."""
    try:
        service = BoundaryIntelligenceService(db)
        return service.get_boundary_intelligence(run_id)
    except Exception as e:
        logger.error(f"Failed to generate boundary intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategic-roadmap/{run_id}", tags=["Modernization Advisory"], summary="Get prioritized modernization steps")
def get_strategic_roadmap(run_id: int):
    """Module D: Returns a step-by-step strategic modernization plan."""
    try:
        service = AdvisoryService()
        return service.get_strategic_roadmap(run_id)
    except Exception as e:
        logger.error(f"Failed to generate strategic roadmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{run_id}/autoload", tags=["Modernization Advisory"], summary="Generate PSR-4 autoload mapping")
def get_autoload(run_id: int):
    """Module D.1: Generates dynamic PSR-4 autoload mapping based on AST taxonomy."""
    try:
        service = AdvisoryService()
        return service.get_autoload_mappings(run_id)
    except Exception as e:
        logger.error(f"Failed to generate autoload mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/simulation/impact/{run_id}", tags=["Modernization Advisory"], summary="Simulate extraction impact")
def get_simulation_impact(run_id: int, fqn: str):
    """Module D: Predicts what will break if a specific component is extracted into a service."""
    try:
        service = SimulationService()
        return service.get_extraction_impact(run_id, fqn)
    except Exception as e:
        logger.error(f"Failed to run simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulation/ghost-graph/{run_id}", tags=["Modernization Advisory"], summary="Simulate post-extraction ghost graph")
def get_simulation_ghost_graph(run_id: int, fqn: str):
    """Module A.2: Simulates and visualizes the target decoupled to-be architecture."""
    try:
        service = SimulationService()
        return service.get_ghost_graph(run_id, fqn)
    except Exception as e:
        logger.error(f"Failed to run ghost graph simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/query-graph/{run_id}", tags=["Discovery & Ingestion"], summary="Query normalized graph relations")
def query_graph_relations(
    run_id: int,
    node_type: Optional[str] = None,
    namespace: Optional[str] = None,
    edge_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Module A.3: Directly queries SQLite GraphNode and GraphEdge tables for custom subgraphs."""
    try:
        from infrastructure.persistence.models import GraphNode, GraphEdge
        import json
        
        node_query = db.query(GraphNode).filter(GraphNode.run_id == run_id)
        if node_type:
            node_query = node_query.filter(GraphNode.node_type == node_type)
        if namespace:
            node_query = node_query.filter(GraphNode.namespace.like(f"{namespace}%"))
            
        nodes = node_query.all()
        node_ids = {n.id for n in nodes}
        
        edge_query = db.query(GraphEdge).filter(GraphEdge.run_id == run_id)
        if edge_type:
            edge_query = edge_query.filter(GraphEdge.edge_type == edge_type)
            
        edges = edge_query.all()
        
        filtered_edges = []
        for e in edges:
            if not node_type and not namespace:
                filtered_edges.append(e)
            elif e.source_id in node_ids and e.target_id in node_ids:
                filtered_edges.append(e)
                
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "fqn": n.fqn,
                    "type": n.node_type,
                    "namespace": n.namespace,
                    "file_path": n.file_path,
                    "metadata": json.loads(n.metadata_json or "{}")
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.edge_type
                }
                for e in filtered_edges
            ]
        }
    except Exception as e:
        logger.error(f"Failed to query graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/security-risk/{run_id}", tags=["Intelligence Modules"], summary="Security & Vulnerability audit")
def get_security_risk(run_id: int, db: Session = Depends(get_db)):
    """Module H: Cross-references structural risk with security anti-patterns."""
    try:
        service = SecurityRiskService(db)
        return service.get_security_risk_audit(run_id)
    except Exception as e:
        logger.error(f"Failed to generate security risk audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Phase 5: Enterprise Reporting ---

@app.get("/report/roadmap/{run_id}", tags=["Reporting & Visuals"], summary="Generate PDF/Markdown roadmap")
def get_roadmap(run_id: int, db: Session = Depends(get_db)):
    """Returns a structured roadmap ready for document generation."""
    try:
        service = ReportService(db)
        return service.generate_roadmap(run_id)
    except Exception as e:
        logger.error(f"Failed to generate roadmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/advisory/ai/{run_id}", tags=["Reporting & Visuals"], summary="Get AI-driven advisory findings")
def get_ai_advisory(run_id: int, db: Session = Depends(get_db)):
    """Returns the Canonical Model with AI findings and playbook recommendations."""
    from application.services.publishing.evidence_builder import EvidenceBuilder
    try:
        model = EvidenceBuilder(db).build(run_id)
        return model.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch AI advisory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/summary-network/{run_id}", tags=["Reporting & Visuals"], summary="Get high-level interactive network")
def get_summary_network(run_id: int, db: Session = Depends(get_db)):
    """Returns a simplified JSON network representing directory-level coupling."""
    try:
        service = ReportService(db)
        return service.generate_summary_network(run_id)
    except Exception as e:
        logger.error(f"Failed to generate summary network: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/graphviz/{run_id}", response_model=GraphvizResponse, tags=["Reporting & Visuals"], summary="Get full DOT graph")
def get_graphviz(run_id: int, db: Session = Depends(get_db)):
    """Returns the complete component-level DOT string for visualization tools."""
    try:
        service = ReportService(db)
        return {"dot": service.generate_graphviz(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/neo4j/{run_id}", tags=["Reporting & Visuals"], summary="Get Neo4j Cypher script")
def get_neo4j(run_id: int, db: Session = Depends(get_db)):
    """Returns a list of Cypher commands to import the graph into Neo4j."""
    try:
        service = ReportService(db)
        return {"cypher": service.generate_neo4j_cypher(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/ai-chunks/{run_id}", tags=["Reporting & Visuals"], summary="Get AI-ready knowledge chunks")
def get_ai_chunks(run_id: int, db: Session = Depends(get_db)):
    """Splits the analysis into optimal chunks for LLM context windows."""
    try:
        service = ReportService(db)
        return {"chunks": service.generate_ai_chunks(run_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/{project_id}", response_model=DashboardResponse, tags=["Reporting & Visuals"], summary="Executive Dashboard data")
def get_dashboard(project_id: int, db: Session = Depends(get_db)):
    """Requirement 4.A: Returns consolidated metrics and risk scores for the Project Dashboard."""
    from infrastructure.persistence.models import Project, AnalysisRun, LegacyMetrics
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        latest_run = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.project_id == project_id, AnalysisRun.status.in_([
                "completed", "analysis_complete", "intelligence_ready", "intelligence_failed", 
                "synthesizing_findings", "synthesizing_summary", "synthesizing_rector"
            ]))
            .order_by(AnalysisRun.id.desc())
            .first()
        )
        
        if not latest_run:
            return {
                "project": {
                    "name": project.name,
                    "root_path": project.root_path,
                    "created_at": project.created_at.isoformat()
                },
                "latest_run": None
            }
            
        legacy = db.query(LegacyMetrics).filter(LegacyMetrics.run_id == latest_run.id).first()
        
        from infrastructure.persistence.models import ComponentMetric
        from sqlalchemy.sql import func
        avg_coverage_result = db.query(func.avg(ComponentMetric.test_coverage)).filter(
            ComponentMetric.run_id == latest_run.id,
            ComponentMetric.test_coverage.isnot(None)
        ).scalar()
        global_coverage = float(avg_coverage_result) if avg_coverage_result is not None else None
        
        return {
            "project": {
                "name": project.name,
                "root_path": project.root_path,
                "created_at": project.created_at.isoformat()
            },
            "latest_run": {
                "id": latest_run.id,
                "completed_at": latest_run.completed_at.isoformat(),
                "total_files": latest_run.total_files,
                "total_loc": latest_run.total_loc,
                "avg_complexity": latest_run.avg_complexity,
                "avg_maintainability": latest_run.avg_maintainability,
                "total_classes": latest_run.total_classes,
                "total_edges": latest_run.total_edges,
                "risk_score": legacy.total_modernization_score if legacy else 0.0,
                "php_era": legacy.php_era if legacy else "Unknown",
                "framework": legacy.detected_framework if legacy else "Unknown",
                "test_coverage": global_coverage
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Artifact Generation Endpoints ---

@app.get("/artifacts/sarif/{run_id}", tags=["Artifacts"], summary="Generate SARIF JSON")
def get_sarif_artifact(run_id: int, db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    return ArtifactService(db).generate_sarif(run_id)

@app.get("/artifacts/rector/{run_id}", tags=["Artifacts"], summary="Generate rector.php config")
def get_rector_config(run_id: int, db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(ArtifactService(db).generate_rector_config(run_id))

@app.get("/artifacts/deptrac/{run_id}", tags=["Artifacts"], summary="Generate deptrac.yaml config")
def get_deptrac_config(run_id: int, db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(ArtifactService(db).generate_deptrac_yaml(run_id))

@app.get("/artifacts/json/{run_id}", tags=["Artifacts"], summary="Generate strict Machine JSON dump")
def get_machine_json(run_id: int, db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    import json
    return json.loads(ArtifactService(db).generate_machine_json(run_id))

@app.get("/artifacts/csv/{run_id}", tags=["Artifacts"], summary="Generate CSV risk export")
def get_csv_export(run_id: int, db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(ArtifactService(db).generate_csv_export(run_id))

@app.get("/artifacts/human/{run_id}", tags=["Artifacts"], summary="Generate Human-Readable Assessment")
def get_human_assessment(run_id: int, format: str = "html", db: Session = Depends(get_db)):
    from application.services.artifact_service import ArtifactService
    from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
    import os
    import tempfile
    
    service = ArtifactService(db)
    
    if format == "html":
        return HTMLResponse(service.generate_human_report(run_id))
    elif format == "md":
        return PlainTextResponse(service.generate_technical_report(run_id))
    elif format == "pdf":
        tmp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(tmp_dir, f"technical_assessment_{run_id}.pdf")
        service.generate_pdf_report(run_id, pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename="technical_assessment.pdf")
    elif format == "docx":
        tmp_dir = tempfile.mkdtemp()
        docx_path = os.path.join(tmp_dir, f"technical_assessment_{run_id}.docx")
        service.generate_docx_report(run_id, docx_path)
        return FileResponse(docx_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="technical_assessment.docx")
    else:
        raise HTTPException(status_code=400, detail="Invalid format selected")

@app.get("/artifacts/bundle/{run_id}", tags=["Artifacts"], summary="Download Full Workspace Bundle")
def get_artifact_bundle(
    run_id: int, 
    html: bool = True, md: bool = True, csv: bool = True,
    sarif: bool = True, rector: bool = True, deptrac: bool = True,
    pdf: bool = True, docx: bool = True,
    db: Session = Depends(get_db)
):
    from application.services.artifact_service import ArtifactService
    from fastapi.responses import StreamingResponse
    import io
    
    zip_bytes = ArtifactService(db).generate_workspace_bundle(
        run_id, html=html, md=md, csv=csv, sarif=sarif, rector=rector, deptrac=deptrac, pdf=pdf, docx=docx
    )
    return StreamingResponse(
        io.BytesIO(zip_bytes), 
        media_type="application/zip", 
        headers={"Content-Disposition": f"attachment; filename=strata_workspace_{run_id}.zip"}
    )

