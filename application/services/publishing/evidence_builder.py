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
            lines_of_code=run.total_loc or 0,
            avg_complexity=round(run.avg_complexity, 2) if run.avg_complexity else 0.0,
            connectivity=run.total_edges or 0,
            test_coverage="N/A",  # Extracted in Phase 8
            php_era=legacy.php_era if legacy else "Unknown",
            framework=legacy.detected_framework if legacy else "Custom/None",
            overall_readiness=legacy.total_modernization_score if legacy else 0.0
        )
        
        # 2. Hydrate Database Intelligence
        db_intel = self._extract_database_intelligence(run_id)
        
        # 3. Hydrate Legacy Posture
        legacy_posture = self._extract_legacy_posture(legacy)

        # 4. Hydrate Modules (Inferred from metrics for now)
        modules = self._infer_modules(run_id)
        
        # 5. Hydrate Findings (From Risks)
        findings = self._extract_findings(run_id)
        
        # 6. Hydrate Extended Intelligence
        dep_intel = self._extract_dependency_intelligence(run_id)
        state_intel = self._extract_global_state_intelligence(run_id)
        full_risk_register = self._extract_full_risk_register(run_id)
        
        return CanonicalModel(
            system_context=ctx,
            legacy_posture=legacy_posture,
            database_intelligence=db_intel,
            dependency_intelligence=dep_intel,
            global_state_intelligence=state_intel,
            modules=modules,
            findings=findings,
            full_risk_register=full_risk_register
        )

    def _extract_database_intelligence(self, run_id: int):
        from infrastructure.persistence.models import ComponentBehavior
        from application.services.publishing.models import DatabaseIntelligence
        behaviors = self.db.query(ComponentBehavior).filter(
            ComponentBehavior.run_id == run_id,
            ComponentBehavior.shared_table_pressure > 0
        ).order_by(ComponentBehavior.shared_table_pressure.desc()).limit(10).all()
        
        return [DatabaseIntelligence(
            table_name=b.component_name,
            write_intensity=b.write_intensity,
            shared_table_pressure=b.shared_table_pressure
        ) for b in behaviors]

    def _extract_legacy_posture(self, legacy):
        from application.services.publishing.models import LegacyPosture
        if not legacy:
            return None
        return LegacyPosture(
            version_score=legacy.version_score,
            namespace_score=legacy.namespace_score,
            db_layer_score=legacy.db_layer_score,
            security_score=legacy.security_score,
            testability_score=legacy.testability_score,
            coupling_score=legacy.coupling_score,
            total_score=legacy.total_modernization_score
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
        import json
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).order_by(ComponentRisk.final_risk.desc()).limit(50).all()
        findings = []
        
        top_risks = [r for r in risks if r.risk_score >= 0.3][:5]
        if not top_risks:
            return findings
            
        ai_findings = []
        if run and run.ai_findings_json:
            try:
                ai_data = json.loads(run.ai_findings_json)
                from application.services.publishing.ai_advisory_service import GeminiFindingResponse
                ai_findings = [GeminiFindingResponse(**f) for f in ai_data]
            except Exception:
                pass
                
        ai_map = {f.component_name: f for f in ai_findings}
        
        for r in top_risks:
            ai_f = ai_map.get(r.component_name)
            
            evidence = [
                Evidence(type="file", target=r.component_name),
                Evidence(type="metric", target="risk_score", metric_value=r.risk_score),
                Evidence(type="metric", target="coupling_pressure", metric_value=r.coupling_pressure)
            ]
            
            if ai_f:
                # Map cached LLM response to our canonical schema
                f = Finding(
                    id=f"FND-{r.id}",
                    category=ai_f.category,
                    observation=ai_f.observation,
                    evidence=evidence,
                    impact=ai_f.impact,
                    reasoning=ai_f.reasoning,
                    recommended_action=ai_f.recommended_action,
                    priority=ai_f.priority,
                    confidence=ai_f.confidence,
                    mermaid_diagram=ai_f.mermaid_diagram
                )
            else:
                # Fallback if cache is empty or AI failed
                f = Finding(
                    id=f"FND-{r.id}",
                    category="Architecture",
                    observation=f"[AI SYNTHESIS UNAVAILABLE - SHOWING BASE METRICS] High Risk Component '{r.component_name}'",
                    evidence=evidence,
                    impact="[AI SYNTHESIS UNAVAILABLE]",
                    reasoning=f"High structural coupling pressure ({r.coupling_pressure:.2f}) and Risk Score ({r.risk_score:.2f}).",
                    recommended_action="[AI SYNTHESIS UNAVAILABLE]",
                    priority="Critical" if r.risk_score > 0.8 else "High",
                    confidence="Confirmed" if r.risk_score > 0.8 else "Probable",
                    mermaid_diagram=None
                )
            findings.append(f)
            
        return findings

    def _extract_dependency_intelligence(self, run_id: int):
        from application.services.publishing.models import DependencyIntelligence
        metrics = self.db.query(ComponentMetric).filter(
            ComponentMetric.run_id == run_id
        ).order_by(ComponentMetric.betweenness.desc()).limit(20).all()
        
        return [DependencyIntelligence(
            component_name=m.component_name,
            in_degree=m.in_degree,
            out_degree=m.out_degree,
            scc_size=m.scc_size,
            is_hotspot=m.betweenness > 0.1
        ) for m in metrics]

    def _extract_global_state_intelligence(self, run_id: int):
        from application.services.publishing.models import GlobalStateIntelligence
        # Currently a placeholder until GlobalState extractor is fully implemented in the db schema.
        # We simulate it for now.
        return [GlobalStateIntelligence(
            variable_name="*Placeholder Global State*",
            mutation_count=0,
            read_count=0
        )]

    def _extract_full_risk_register(self, run_id: int) -> List[Finding]:
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).order_by(ComponentRisk.final_risk.desc()).all()
        findings = []
        for r in risks:
            evidence = [
                Evidence(type="file", target=r.component_name),
                Evidence(type="metric", target="risk_score", metric_value=r.risk_score),
                Evidence(type="metric", target="coupling_pressure", metric_value=r.coupling_pressure)
            ]
            f = Finding(
                id=f"FND-{r.id}",
                category="Architecture",
                observation=f"Structural risk detected in {r.component_name}",
                evidence=evidence,
                impact="Potential architectural bottleneck and high blast radius.",
                reasoning=f"High coupling ({r.coupling_pressure:.2f}) and instability ({r.instability:.2f}).",
                recommended_action="Isolate and refactor.",
                priority=r.risk_level.capitalize(),
                confidence="Confirmed",
                mermaid_diagram=None
            )
            findings.append(f)
        return findings
