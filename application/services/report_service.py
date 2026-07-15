import json
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from infrastructure.persistence.models import (
    ComponentDependency,
    ComponentRisk,
    ComponentMetric,
    ComponentBehavior,
    AnalysisRun,
    LegacyMetrics
)
from application.services.boundary_intelligence_service import BoundaryIntelligenceService
from application.services.layer_service import LayerService

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_roadmap(self, run_id: int) -> dict:
        """
        Dynamically constructs a deterministic extraction roadmap based on AST metrics (5-Phase Algorithm).
        """
        legacy = self.db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        
        phases = []
        
        if not legacy:
            return {"phases": phases}

        ai_prose = {}
        if legacy.run_id:
            run = self.db.query(AnalysisRun).filter(AnalysisRun.id == legacy.run_id).first()
            if run and run.ai_executive_summary_json:
                try:
                    summary = json.loads(run.ai_executive_summary_json)
                    prose_list = summary.get("strategic_roadmap_prose", [])
                    for item in prose_list:
                        ai_prose[item.get("phase_id")] = item.get("executive_summary")
                except Exception:
                    pass

        import os
        data_dir = os.environ.get("DATA_DIR", "/data")
        graph_file = os.path.join(data_dir, f"graph_{run_id}.json")
        fqn_to_path = {}
        if os.path.exists(graph_file):
            try:
                with open(graph_file, "r") as f:
                    gdata = json.load(f)
                    for n in gdata.get("nodes", []):
                        fqn = n.get("fqn") or n.get("name")
                        fpath = n.get("file_path")
                        if fqn and fpath:
                            fqn_to_path[fqn] = fpath
            except Exception:
                pass

        # Phase 0: The Safety Net
        avg_coverage_result = self.db.query(func.avg(ComponentMetric.test_coverage)).filter(
            ComponentMetric.run_id == run_id,
            ComponentMetric.test_coverage.isnot(None)
        ).scalar()
        global_coverage = float(avg_coverage_result) if avg_coverage_result is not None else 0.0

        high_risk_uncovered = [
            {"file_name": fqn_to_path.get(r.component_name, r.component_name), "wmc": r.wmc, "coverage": r.test_coverage or 0.0}
            for r in risks if (r.test_coverage is None or r.test_coverage == 0.0) and r.wmc > 10
        ]
        high_risk_uncovered = sorted(high_risk_uncovered, key=lambda x: x["wmc"], reverse=True)[:10]

        phases.append({
            "phase_id": 0,
            "title": "Phase 0: The Safety Net (Instrumentation & Coverage)",
            "status": "PASSED" if global_coverage > 80.0 else "ACTION_REQUIRED",
            "executive_summary": ai_prose.get(0, "Test coverage metrics evaluated."),
            "evidence_tables": {
                "high_risk_uncovered": high_risk_uncovered,
                "global_coverage": round(global_coverage, 2)
            }
        })

        # Phase 1: Boundary & Presentation Decoupling
        boundary_service = BoundaryIntelligenceService(self.db)
        try:
            boundary_data = boundary_service.get_boundary_intelligence(run_id)
            fat_views = boundary_data.get("presentation_coupling", [])[:10]
        except Exception:
            fat_views = []
            
        fat_views_list = [
            {
                "file_name": fqn_to_path.get(f.get("File"), f.get("File")),
                "html_nodes": f.get("HTML/Echo Nodes"),
                "db_queries": f.get("DB Operations"),
                "entanglement": f.get("Entanglement Ratio")
            } for f in fat_views
        ]

        phases.append({
            "phase_id": 1,
            "title": "Phase 1: Boundary & Presentation Decoupling (Strangler Facade)",
            "status": "PASSED" if not fat_views_list else "ACTION_REQUIRED",
            "executive_summary": ai_prose.get(1, "Boundary layer logic evaluated."),
            "evidence_tables": {
                "fat_views": fat_views_list
            }
        })

        # Phase 2: State & Data Layer Isolation
        stateful_files = [
            {"file_name": fqn_to_path.get(r.component_name, r.component_name), "type": "Global State", "pressure": round(r.coupling_pressure, 2)} 
            for r in risks if r.is_stateful
        ]
        
        db_layer_direct = legacy.db_layer in ["Direct SQL", "Legacy Pattern", "None Detected"]
        
        shared_table_pressure = []
        behaviors = self.db.query(ComponentBehavior).filter(
            ComponentBehavior.run_id == run_id, 
            ComponentBehavior.shared_table_pressure > 0
        ).all()
        for b in behaviors:
            shared_table_pressure.append({
                "table_name": fqn_to_path.get(b.component_name, b.component_name),
                "pressure": round(b.shared_table_pressure, 2)
            })

        phases.append({
            "phase_id": 2,
            "title": "Phase 2: State & Data Layer Isolation (Database-Per-Service)",
            "status": "PASSED" if not stateful_files and not db_layer_direct and not shared_table_pressure else "ACTION_REQUIRED",
            "executive_summary": ai_prose.get(2, "Data layer independence evaluated."),
            "evidence_tables": {
                "global_mutators": sorted(stateful_files, key=lambda x: x["pressure"], reverse=True)[:10],
                "shared_table_pressure": sorted(shared_table_pressure, key=lambda x: x["pressure"], reverse=True)[:10],
                "has_direct_sql": db_layer_direct
            }
        })
            
        # Phase 3: Dismantling Architectural Chokepoints
        god_classes = [
            {
                "file_name": fqn_to_path.get(r.component_name, r.component_name), 
                "complexity_wmc": r.wmc,
                "lack_of_cohesion_lcom": round(r.lcom, 2),
                "coupling": round(r.coupling_pressure, 2),
                "blast_radius": round(r.norm_blast_radius, 2)
            } 
            for r in risks if r.domain_archetype == "GOD_CLASS" or r.risk_level == "CRITICAL"
        ]
        
        phases.append({
            "phase_id": 3,
            "title": "Phase 3: Dismantling Architectural Chokepoints (God Classes)",
            "status": "PASSED" if not god_classes else "ACTION_REQUIRED",
            "executive_summary": ai_prose.get(3, "Structural chokepoints evaluated."),
            "evidence_tables": {
                "god_classes": sorted(god_classes, key=lambda x: x["coupling"], reverse=True)[:10]
            }
        })
            
        # Phase 4: Domain Extraction Sequence
        layer_service = LayerService(self.db)
        try:
            layers = layer_service.get_layered_analysis(run_id)
            bounded_contexts = layers.get("layer_3", {}).get("bounded_contexts", [])
        except Exception:
            bounded_contexts = []
        
        domains = []
        for ctx in bounded_contexts:
            name = ctx.get("name")
            if name in ["Global", "Vendor", "Unknown"]:
                continue
            
            num_files = ctx.get("file_count", 0)
            if num_files == 0:
                continue
                
            external = ctx.get("external_edges", 0)
            internal = ctx.get("internal_edges", 0)
            isolation_score = external / max(1, internal)
            
            domains.append({
                "domain_name": name,
                "file_count": num_files,
                "internal_cohesion": internal,
                "external_dependencies": external,
                "isolation_score": round(isolation_score, 2)
            })
            
        phases.append({
            "phase_id": 4,
            "title": "Phase 4: Domain Extraction Sequence (Strangler Fig)",
            "status": "PASSED" if len(domains) <= 1 else "ACTION_REQUIRED",
            "executive_summary": ai_prose.get(4, "Microservice extraction sequence evaluated."),
            "evidence_tables": {
                "extraction_backlog": sorted(domains, key=lambda x: x["isolation_score"])
            }
        })
            
        return {"phases": phases}
