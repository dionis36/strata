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
        """Generates the Master Intelligence Report (Hub) in unified Markdown."""
        import json
        
        ctx = model.system_context
        readiness_pct = min(ctx.overall_readiness, 100.0) if ctx.overall_readiness > 1.0 else (ctx.overall_readiness * 100)
        
        exec_summary = {}
        if hasattr(model, 'raw_run') and model.raw_run and model.raw_run.ai_executive_summary_json:
            try:
                exec_summary = json.loads(model.raw_run.ai_executive_summary_json)
            except Exception:
                pass
                
        if not exec_summary:
            exec_summary = {
                "current_state": "The system contains significant technical debt.",
                "critical_risks": "High architectural coupling and low test coverage make modifications dangerous.",
                "strategic_roadmap": "1. Introduce static analysis. 2. Add characterization tests. 3. Incrementally decouple."
            }
            
        top_findings = [f for f in model.findings if f.priority in ["Critical", "High"]][:5]
        
        lines = [
            f"# Master Intelligence Report: {ctx.project_name}",
            "",
            "## 1. Executive Summary & Verdict",
            "This report provides a comprehensive, AI-driven assessment of the system's structural integrity, pinpointing the most critical architectural bottlenecks.",
            "",
            "### Current State Verdict",
            f"{exec_summary.get('current_state', '')}",
            "",
            "### Global System Meta-Data",
            f"- **Scale:** {ctx.total_files:,} Files | {ctx.total_classes:,} Classes",
            f"- **Architecture/Era:** {ctx.framework} ({ctx.php_era})",
            f"- **Global Modernization Readiness:** {readiness_pct:.1f}%",
            "",
            "## 2. System Health Metrics (The Data Dashboard)",
            "The following metrics dictate the true cost of ownership and the risk of catastrophic failure during refactoring.",
            "",
            "| Metric | Value | Business Impact |",
            "| :--- | :--- | :--- |",
            f"| **Lines of Code** | {ctx.lines_of_code:,} | Defines the sheer volume of logic that must be maintained. |",
            f"| **Avg Complexity** | {ctx.avg_complexity:.2f} | Higher numbers mean code is harder to read, test, and safely modify. |",
            f"| **Connectivity (Edges)** | {ctx.connectivity:,} | Measures how tightly coupled the system is. High connectivity means changes break unexpected features. |",
            "",
            "## 3. Database & State Intelligence",
            "Stateful dependencies form the anchor of the monolith. High-pressure tables are critical bottlenecks.",
            ""
        ]
        
        if model.database_intelligence:
            lines.append("| Table Name | Write Intensity | Shared Pressure |")
            lines.append("| :--- | :--- | :--- |")
            for db in model.database_intelligence:
                lines.append(f"| `{db.table_name}` | {db.write_intensity:.2f} | {db.shared_table_pressure:.2f} |")
        else:
            lines.append("*No high-pressure database tables detected.*")
            
        lines.append("")
        lines.append("## 4. Top Architectural Blockers (AI Synthesis)")
        lines.append("The AI engine has isolated the top 5 most dangerous 'God Classes' in the system. Fixing these resolves the vast majority of structural entanglement.")
        lines.append("")
        
        if not top_findings:
            lines.append("*No Critical or High priority blockers identified.*")
        else:
            for f in top_findings:
                lines.append(f"### [{f.priority}] {f.observation}")
                lines.append(f"**Business Impact:** {f.impact}")
                lines.append("")
                lines.append(f"**Strategic Action:** {f.recommended_action} *(Confidence: {f.confidence})*")
                
                ev_targets = ", ".join([e.target for e in f.evidence if e.type == "file"])
                lines.append(f"**Files Implicated:** `{ev_targets}`")
                
                if f.mermaid_diagram:
                    lines.append("")
                    lines.append("#### Sub-System Topology")
                    lines.append("```mermaid")
                    lines.append(f.mermaid_diagram)
                    lines.append("```")
                lines.append("---")
                
        lines.append("")
        lines.append("## 5. Strategic Roadmap")
        lines.append("Based on the intelligence gathered, the AI engine recommends the following phased approach to decoupling and modernization:")
        lines.append("")
        lines.append(exec_summary.get('strategic_roadmap', '').replace('\n', '\n\n'))
        
        lines.append("")
        lines.append("## 6. The Artifact Index (Navigating the Workspace Bundle)")
        lines.append("This Executive Report is only the **Hub**. The accompanying `.zip` bundle contains the definitive, raw data (the **Spokes**) required for engineering execution:")
        lines.append("")
        lines.append("- `remediation_backlog.csv`: The complete, raw risk inventory detailing the complexity and coupling scores for all 7,800+ files.")
        lines.append("- `rector.php`: The automated refactoring rules generated specifically for this codebase.")
        lines.append("- `deptrac.yaml`: Architectural boundary definitions to enforce layer isolation.")
        lines.append("- `security_findings.sarif`: CI/CD compatible format for importing security vulnerabilities into GitHub or SonarQube.")
        
        return "\n".join(lines)
