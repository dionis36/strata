import json
from sqlalchemy.orm import Session
from infrastructure.persistence.models import (
    ComponentDependency,
    ComponentRisk,
    ComponentMetric,
    AnalysisRun,
    LegacyMetrics
)
from domain.decision.recommendation_engine import RecommendationEngine

class ReportService:
    def __init__(self, db: Session):
        self.db = db


    def generate_roadmap(self, run_id: int) -> dict:
        """
        Dynamically constructs a deterministic extraction roadmap based on AST metrics.
        """
        legacy = self.db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        
        roadmap = {
            "phase_0": None,
            "phase_1": None,
            "phase_2": None
        }
        
        if not legacy:
            return roadmap

        # Phase 0: Base Abstraction (Global State & Direct DB Calls)
        stateful_files = [
            {"name": r.component_name, "type": "Global State", "pressure": round(r.coupling_pressure, 2)} 
            for r in risks if r.is_stateful
        ]
        db_layer_direct = legacy.db_layer in ["Direct SQL", "Legacy Pattern", "None Detected"]
        
        has_phase_0 = len(stateful_files) > 0 or db_layer_direct
        if has_phase_0:
            roadmap["phase_0"] = {
                "has_global_state": len(stateful_files) > 0,
                "has_direct_sql": db_layer_direct,
                "stateful_files": sorted(stateful_files, key=lambda x: x["pressure"], reverse=True)
            }
            
        # Phase 1: Structural Decomposition
        god_classes = [
            {
                "name": r.component_name, 
                "risk_level": r.risk_level,
                "complexity": r.wmc,
                "lcom": round(r.lcom, 2),
                "coupling": round(r.coupling_pressure, 2)
            } 
            for r in risks if r.domain_archetype == "GOD_CLASS" or r.risk_level == "CRITICAL"
        ]
        if god_classes:
            roadmap["phase_1"] = {
                "god_classes": sorted(god_classes, key=lambda x: x["coupling"], reverse=True)
            }
            
        # Phase 2: Extraction Sequence
        from application.services.layer_service import LayerService
        layer_service = LayerService(self.db)
        layers = layer_service.get_layered_analysis(run_id)
        bounded_contexts = layers.get("layer_3", {}).get("bounded_contexts", [])
        
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
            # Isolation Score: fewer external edges relative to internal edges = better isolation
            isolation_score = external / max(1, internal)
            
            domains.append({
                "name": name,
                "files": num_files,
                "internal_coupling": internal,
                "external_coupling": external,
                "isolation_score": round(isolation_score, 2)
            })
            
        if domains:
            roadmap["phase_2"] = {
                "domains": sorted(domains, key=lambda x: x["isolation_score"])
            }
            
        return roadmap
