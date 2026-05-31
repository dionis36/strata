from typing import List, Dict
from sqlalchemy.orm import Session
from infrastructure.persistence.models import ComponentRisk, LegacyMetrics, ComponentMetric, AnalysisRun, Project
from application.services.publishing.models import CanonicalModel, SystemContext, Module, Finding, Evidence

class EvidenceBuilder:
    """Pass 1: Evidence Selection & Hydration. Builds the Canonical Model from SQLite."""
    
    def __init__(self, db: Session):
        self.db = db

    def build(self, run_id: int) -> CanonicalModel:
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found.")
            
        project = self.db.query(Project).filter(Project.id == run.project_id).first()
        legacy = self.db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        
        # 1. Hydrate System Context
        ctx = SystemContext(
            project_name=project.name if project else "Unknown Project",
            total_files=run.total_files or 0,
            total_classes=run.total_classes or 0,
            php_era=legacy.php_era if legacy else "Unknown",
            framework=legacy.detected_framework if legacy else "Custom/None",
            overall_readiness=legacy.total_modernization_score if legacy else 0.0
        )
        
        # 2. Hydrate Modules (Inferred from metrics for now)
        # Note: A true module clustering algorithm would go here.
        # For MVP of the pipeline, we map top-level directories as modules.
        modules = self._infer_modules(run_id)
        
        # 3. Hydrate Findings (From Risks)
        findings = self._extract_findings(run_id)
        
        return CanonicalModel(
            system_context=ctx,
            modules=modules,
            findings=findings
        )

    def _infer_modules(self, run_id: int) -> List[Module]:
        metrics = self.db.query(ComponentMetric).filter(ComponentMetric.run_id == run_id).all()
        # Group by top-level directory roughly
        groups = {}
        for m in metrics:
            parts = m.component_name.strip("/").split("/")
            if len(parts) > 1:
                ctx_name = parts[0]
            else:
                ctx_name = "Core"
            if ctx_name not in groups:
                groups[ctx_name] = []
            groups[ctx_name].append(m.component_name)
            
        mods = []
        for name, files in groups.items():
            mods.append(Module(
                id=f"mod_{name}",
                name=name,
                boundary_confidence="Probable",
                files=files,
                dependencies=[],
                entry_points=[]
            ))
        return mods

    def _extract_findings(self, run_id: int) -> List[Finding]:
        from application.services.publishing.ai_advisory_service import AIAdvisoryService
        
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).order_by(ComponentRisk.final_risk.desc()).limit(50).all()
        findings = []
        
        top_risks = [r for r in risks if r.risk_score >= 0.3][:5]
        if not top_risks:
            return findings
            
        from infrastructure.persistence.models import GraphNode, GraphEdge
        import json
        
        risk_data = []
        for r in top_risks:
            node = self.db.query(GraphNode).filter(
                GraphNode.run_id == run_id, 
                GraphNode.fqn == r.component_name
            ).first()
            
            ast_metadata = {}
            if node and node.metadata_json:
                try:
                    ast_metadata = json.loads(node.metadata_json)
                except:
                    pass
                    
            dependencies = []
            if node:
                edges = self.db.query(GraphEdge).filter(
                    GraphEdge.run_id == run_id,
                    GraphEdge.source_id == node.id
                ).all()
                for e in edges:
                    target = self.db.query(GraphNode).filter(
                        GraphNode.run_id == run_id,
                        GraphNode.id == e.target_id
                    ).first()
                    if target:
                        dependencies.append(f"{e.edge_type} -> {target.node_type}:{target.name}")
                        
            risk_data.append({
                "component_name": r.component_name,
                "risk_score": r.risk_score,
                "coupling_pressure": r.coupling_pressure,
                "blast_radius": r.norm_blast_radius,
                "ast_metadata": ast_metadata,
                "dependency_edges": dependencies
            })
        
        ai_service = AIAdvisoryService()
        ai_findings = ai_service.synthesize_batch_findings(risk_data)
        ai_map = {f.component_name: f for f in ai_findings}
        
        for r in top_risks:
            ai_f = ai_map.get(r.component_name)
            if not ai_f:
                continue
                
            evidence = [
                Evidence(type="file", target=r.component_name),
                Evidence(type="metric", target="risk_score", metric_value=r.risk_score),
                Evidence(type="metric", target="coupling_pressure", metric_value=r.coupling_pressure)
            ]
            
            # Map strict LLM response to our canonical schema
            f = Finding(
                id=f"FND-{r.id}",
                category=ai_f.category,
                observation=ai_f.observation,
                evidence=evidence,
                impact=ai_f.impact,
                reasoning=ai_f.reasoning,
                recommended_action=ai_f.recommended_action,
                priority=ai_f.priority,
                confidence=ai_f.confidence
            )
            findings.append(f)
            
        return findings
