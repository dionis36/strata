import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from infrastructure.persistence.models import ComponentRisk, ComponentMetric, ComponentBehavior

class KnowledgeSynthesisService:
    """
    Phase 5 Service: Synthesizes the CSOT into a high-density intelligence report.
    Optimized for LLM context windows and automated decision engines.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_project_intelligence(self, run_id: int) -> Dict[str, Any]:
        """
        Produces a 'Project Intelligence Manifest'.
        Combines structural, behavioral, and risk data into a single semantic JSON.
        """
        # 1. Fetch data
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        metrics = self.db.query(ComponentMetric).filter(ComponentMetric.run_id == run_id).all()
        behavior = self.db.query(ComponentBehavior).filter(ComponentBehavior.run_id == run_id).all()

        # 2. Map indices
        risk_map = {r.component_name: r for r in risks}
        metric_map = {m.component_name: m for m in metrics}
        behavior_map = {b.component_name: b for b in behavior}

        # 3. Identify Top Hotspots (Highest Final Risk)
        sorted_risks = sorted(risks, key=lambda x: x.final_risk, reverse=True)
        hotspots = []
        for r in sorted_risks[:10]:
            m = metric_map.get(r.component_name)
            hotspots.append({
                "component": r.component_name,
                "role": r.component_type,
                "risk": r.final_risk,
                "blast_radius": m.blast_radius if m else 0,
                "coupling": "High" if r.coupling_pressure > 0.7 else "Normal"
            })

        # 4. Synthesize Summary
        return {
            "run_id": run_id,
            "architecture_overview": {
                "total_components": len(risks),
                "hotspot_count": len([r for r in risks if r.final_risk > 0.8]),
                "top_hotspots": hotspots
            },
            "behavioral_summary": {
                "high_write_intensity": [
                    b.component_name for b in behavior if b.write_intensity > 0.7
                ]
            },
            "recommendation_engine": {
                "strategy": "Target high-risk components with high blast radius for extraction."
            }
        }

    def serialize_for_system(self, run_id: int) -> str:
        """Returns the intelligence manifest as a minified JSON string."""
        intel = self.generate_project_intelligence(run_id)
        return json.dumps(intel)
