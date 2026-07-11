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
        Requirement 19: Generate Executive Migration Roadmap and System Context.
        """
        legacy = self.db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).order_by(ComponentRisk.final_risk.desc()).limit(10).all()
        
        if not legacy:
            return {"error": "Legacy metrics not found for this run."}
            
        rec = RecommendationEngine.recommend(legacy.total_modernization_score, {
            "db_layer": legacy.db_layer,
            "auth_layer": legacy.auth_layer
        })
        
        top_risks = [f"- **{r.component_name}** (Risk Level: {r.risk_level}, Score: {round(r.risk_score, 2)})" for r in risks]
        
        md_roadmap = f"""# Executive Modernization Roadmap
## System Context
- **Era Classification:** {legacy.php_era}
- **Architecture Type:** {legacy.detected_framework}
- **Scale:** {run.total_files} Files | {run.total_classes} Classes
- **Database Access:** {legacy.db_layer}
- **Auth Pattern:** {legacy.auth_layer}
- **Overall Modernization Readiness:** {round(legacy.total_modernization_score, 2)} / 100

## Recommended Strategy: {rec['strategy']}
{rec['description']}

### Tactical Advice
"""
        for advice in rec["tactical_advice"]:
            md_roadmap += f"- {advice}\n"
            
        md_roadmap += f"""
## Phase 1: High-Risk Extraction Targets
The following components exhibit the highest coupling pressure and criticality. They should be prioritized for isolation:
"""
        md_roadmap += "\n".join(top_risks)
        
        return {
            "markdown": md_roadmap,
            "recommendation": rec
        }
