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
        NOTE: Limits output to prevent browser crashes.
        """
        edges = self.db.query(ComponentDependency).filter(ComponentDependency.run_id == run_id).limit(2000).all()
        
        dot_lines = ["digraph Architecture {"]
        dot_lines.append("  rankdir=LR;")
        dot_lines.append("  node [shape=box, style=filled, color=\"#1f2937\", fillcolor=\"#374151\", fontcolor=white, fontsize=10];")
        dot_lines.append("  edge [color=\"#9ca3af\", arrowsize=0.5];")
        
        added_edges = set()
        for e in edges:
            source = e.source_id.split("/")[-1]
            target = e.target_id.split("/")[-1]
            
            source = source.replace('"', '').replace('.', '_').replace('-', '_')
            target = target.replace('"', '').replace('.', '_').replace('-', '_')
            
            sig = f'"{source}" -> "{target}"'
            if sig not in added_edges:
                dot_lines.append(f'  {sig};')
                added_edges.add(sig)
                
        dot_lines.append("}")
        return "\n".join(dot_lines)

    def generate_summary_graphviz(self, run_id: int) -> str:
        """
        Generates a high-level directory-to-directory dependency graph.
        Perfect for executive overview without UI lag.
        """
        edges = self.db.query(ComponentDependency).filter(ComponentDependency.run_id == run_id).all()
        
        summary_edges = set()
        for e in edges:
            # Extract parent directory as the node
            s_parts = e.source_id.split("/")
            t_parts = e.target_id.split("/")
            
            if len(s_parts) > 3 and len(t_parts) > 3:
                s_dir = s_parts[2] # data/Project/DIR
                t_dir = t_parts[2]
                if s_dir != t_dir:
                    summary_edges.add((s_dir, t_dir))
        
        dot_lines = ["digraph Summary {"]
        dot_lines.append("  rankdir=TD; node [shape=component, style=filled, fillcolor=\"#1e293b\", color=\"#38bdf8\", fontcolor=white];")
        for s, t in summary_edges:
            dot_lines.append(f'  "{s}" -> "{t}";')
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
