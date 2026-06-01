from application.services.publishing.models import CanonicalModel, Finding

class DocumentGenerator:
    """Pass 3 & 5: Section Drafting and Final Assembly."""
    
    def generate_executive_report(self, model: CanonicalModel) -> str:
        """Generates a high-level, decisive report from the Canonical Model."""
        
        ctx = model.system_context
        # Ensure readiness is a proper percentage
        if ctx.overall_readiness > 1.0:
            readiness_pct = round(min(ctx.overall_readiness, 100.0), 1)
        else:
            readiness_pct = round(ctx.overall_readiness * 100, 1)
            
        top_findings = [f for f in model.findings if f.priority in ["Critical", "High"]][:5]
        
        lines = [
            f"# Executive Modernization Assessment: {ctx.project_name}",
            "",
            "## 1. System Scope & Context",
            f"- **Scale:** {ctx.total_files} Files | {ctx.total_classes} Classes",
            f"- **Architecture/Era:** {ctx.framework} ({ctx.php_era})",
            f"- **Modernization Readiness:** {readiness_pct}%",
            "",
            "## 2. Strategic Assessment",
        ]
        
        if readiness_pct >= 70:
            lines.append("The system is structurally sound. Proceed with incremental in-place upgrades.")
        elif readiness_pct >= 40:
            lines.append("The system contains mixed legacy patterns. A Strangler Fig facade is recommended to isolate stable modules from legacy technical debt.")
        else:
            lines.append("The system exhibits critical architectural decay. Feature development should be frozen while core domains are extracted or rewritten.")
            
        lines.append("")
        lines.append("## 3. Top Modernization Blockers")
        
        if not top_findings:
            lines.append("*No Critical or High priority blockers identified in this scan.*")
        else:
            for f in top_findings:
                lines.append(f"### [{f.priority}] {f.observation}")
                # Evidence extraction
                ev_targets = ", ".join([e.target for e in f.evidence if e.type == "file"])
                lines.append(f"- **Evidence:** `{ev_targets}`")
                lines.append(f"- **Impact:** {f.impact}")
                lines.append(f"- **Recommendation:** {f.recommended_action} *(Confidence: {f.confidence})*")
                if f.mermaid_diagram:
                    lines.append("")
                    lines.append("```mermaid")
                    lines.append(f.mermaid_diagram)
                    lines.append("```")
                lines.append("")
                
        return "\n".join(lines)

    def generate_technical_report(self, model: CanonicalModel) -> str:
        """Generates a detailed engineering assessment."""
        # A full markdown document spanning modules and all findings
        lines = [
            f"# Technical Assessment Report: {model.system_context.project_name}",
            ""
        ]
        
        lines.append("## Identified Bounded Contexts (Modules)")
        for m in model.modules:
            lines.append(f"- **{m.name}** ({len(m.files)} files) - Boundary Confidence: {m.boundary_confidence}")
            
        lines.append("")
        lines.append("## Dependency Intelligence (Hotspots)")
        for d in model.dependency_intelligence:
            if d.is_hotspot:
                lines.append(f"- **{d.component_name}** | In: {d.in_degree} | Out: {d.out_degree} | SCC Size: {d.scc_size}")
                
        lines.append("")
        lines.append("## Global State Intelligence")
        for g in model.global_state_intelligence:
            lines.append(f"- **{g.variable_name}** | Mutations: {g.mutation_count} | Reads: {g.read_count}")

        lines.append("")
        lines.append("## Full Risk Register")
        # Ensure we use full_risk_register instead of findings (which is top 5)
        for f in model.full_risk_register:
            lines.append(f"### [{f.priority}] {f.observation}")
            lines.append(f"**Category:** {f.category} | **Confidence:** {f.confidence}")
            lines.append(f"**Reasoning:** {f.reasoning}")
            evs = [f"*{e.type}* {e.target}" + (f" ({e.metric_value})" if e.metric_value else "") for e in f.evidence]
            lines.append("**Evidence Signals:** " + ", ".join(evs))
            lines.append(f"**Action:** {f.recommended_action}")
            if f.mermaid_diagram:
                lines.append("")
                lines.append("```mermaid")
                lines.append(f.mermaid_diagram)
                lines.append("```")
            lines.append("---")
            
        return "\n".join(lines)
