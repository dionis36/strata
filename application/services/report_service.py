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

    def generate_graphviz(self, run_id: int) -> str:
        """
        Requirement 18: Generate Graphviz (.dot) format for deep reachability analysis.
        """
        edges = self.db.query(ComponentDependency).filter(ComponentDependency.run_id == run_id).all()
        
        dot_lines = ["digraph Architecture {"]
        dot_lines.append("  node [shape=box, style=filled, color=\"#1f2937\", fillcolor=\"#374151\", fontcolor=white];")
        dot_lines.append("  edge [color=\"#9ca3af\"];")
        
        added_edges = set()
        for e in edges:
            source = e.source_id.split("::")[-1] if "::" in e.source_id else e.source_id.split("/")[-1].split("\\")[-1]
            target = e.target_id.split("::")[-1] if "::" in e.target_id else e.target_id.split("/")[-1].split("\\")[-1]
            
            # Clean up names for dot syntax
            source = source.replace('"', '').replace('.', '_').replace('-', '_')
            target = target.replace('"', '').replace('.', '_').replace('-', '_')
            
            sig = f'"{source}" -> "{target}"'
            if sig not in added_edges:
                dot_lines.append(f'  {sig};')
                added_edges.add(sig)
                
        dot_lines.append("}")
        return "\n".join(dot_lines)

    def generate_neo4j_cypher(self, run_id: int) -> str:
        """
        Requirement 18: Generate Neo4j Cypher queries for knowledge graph injection.
        """
        edges = self.db.query(ComponentDependency).filter(ComponentDependency.run_id == run_id).all()
        
        cypher_lines = []
        for e in edges:
            source_id = e.source_id.replace("'", "")
            target_id = e.target_id.replace("'", "")
            rel_type = e.edge_type.upper() if e.edge_type else "DEPENDS_ON"
            
            cypher_lines.append(f"MERGE (s:Component {{id: '{source_id}'}})")
            cypher_lines.append(f"MERGE (t:Component {{id: '{target_id}'}})")
            cypher_lines.append(f"MERGE (s)-[:{rel_type}]->(t);")
            
        return "\n".join(cypher_lines)

    def generate_ai_chunks(self, run_id: int) -> list:
        """
        Requirement 23: Generate embeddings-ready metadata for AI-assisted analysis and interpretation.
        """
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        
        chunks = []
        for r in risks:
            chunk = {
                "id": r.component_name,
                "type": r.component_type,
                "embedding_text": f"Component '{r.component_name}' is a {r.component_type} with a risk level of {r.risk_level}. "
                                  f"It has a high coupling pressure of {r.coupling_pressure} and instability of {r.instability}. "
                                  f"Blast radius is {r.norm_blast_radius}. This component is a high-risk node in the system topology.",
                "metadata": {
                    "risk_score": r.risk_score,
                    "criticality": r.criticality_index
                }
            }
            chunks.append(chunk)
            
        return chunks

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
