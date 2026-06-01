import json
import csv
import io
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from infrastructure.persistence.models import (
    ComponentRisk, 
    LegacyMetrics, 
    ComponentMetric, 
    AnalysisRun, 
    ComponentDependency,
    GraphNode
)
from application.services.layer_service import LayerService
from application.services.report_service import ReportService
from application.services.advisory_service import AdvisoryService

class ArtifactService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sarif(self, run_id: int) -> Dict[str, Any]:
        """Generates a SARIF v2.1.0 compliant JSON output for GitHub Code Scanning."""
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        
        results = []
        for r in risks:
            if r.risk_level in ["CRITICAL", "HIGH"]:
                level = "error" if r.risk_level == "CRITICAL" else "warning"
                
                # Try to resolve a file path from GraphNode
                node = self.db.query(GraphNode).filter(GraphNode.run_id == run_id, GraphNode.name == r.component_name).first()
                uri = node.file_path if node and node.file_path else f"{r.component_name}.php"
                
                results.append({
                    "ruleId": f"STRATA-RISK-{r.risk_level}",
                    "level": level,
                    "message": {
                        "text": f"Component '{r.component_name}' exhibits {r.risk_level} structural risk (Score: {round(r.risk_score, 2)}). Coupling Pressure: {round(r.coupling_pressure, 2)}."
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": uri.lstrip('/')
                                }
                            }
                        }
                    ]
                })

        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Strata Modernization Intelligence",
                            "informationUri": "https://github.com/dionis36/strata",
                            "rules": [
                                {
                                    "id": "STRATA-RISK-CRITICAL",
                                    "name": "CriticalStructuralRisk",
                                    "shortDescription": {"text": "Critical architectural or security risk."}
                                },
                                {
                                    "id": "STRATA-RISK-HIGH",
                                    "name": "HighStructuralRisk",
                                    "shortDescription": {"text": "High architectural or security risk."}
                                }
                            ]
                        }
                    },
                    "results": results
                }
            ]
        }
        return sarif

    def generate_rector_config(self, run_id: int) -> str:
        """Generates a rector.php configuration file string using Gemini."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.ai_advisory_service import AIAdvisoryService
        
        # Build canonical model for context
        model = EvidenceBuilder(self.db).build(run_id)
        
        # We need a summary of the worst AST issues
        ast_summary = " | ".join([f.observation for f in model.findings[:10]])
        
        ai_service = AIAdvisoryService()
        rector_artifact = ai_service.synthesize_rector_config(
            system_framework=model.system_context.framework,
            php_era=model.system_context.php_era,
            ast_metrics=ast_summary
        )
        
        return rector_artifact.rector_php_code

    def generate_deptrac_yaml(self, run_id: int) -> str:
        """Generates a deptrac.yaml configuration file based on LayerService outputs."""
        layer_service = LayerService(self.db)
        layer_data = layer_service.get_layered_analysis(run_id)
        
        yaml_lines = [
            "parameters:",
            "  paths:",
            "    - ./src",
            "    - ./app",
            "  layers:"
        ]
        
        l1 = layer_data.get("layer_1", {})
        dirs = l1.get("directories", {})
        
        unique_roles = set()
        for dname, dinfo in dirs.items():
            role = dinfo.get("type", "file")
            unique_roles.add(role)
            
        for role in unique_roles:
            yaml_lines.append(f"    - name: {role.capitalize()}")
            yaml_lines.append(f"      collectors:")
            
            # Find directories matching this role
            role_dirs = [d for d, info in dirs.items() if info.get("type") == role]
            for d in role_dirs:
                # Basic regex for directory
                regex_path = d.replace("/", "\\/") + ".*"
                yaml_lines.append(f"        - type: directory")
                yaml_lines.append(f"          regex: {regex_path}")
                
        yaml_lines.append("  ruleset:")
        if "Controller" in [r.capitalize() for r in unique_roles]:
            yaml_lines.append("    Controller:")
            yaml_lines.append("      - Service")
            yaml_lines.append("      - Model")
        if "Service" in [r.capitalize() for r in unique_roles]:
            yaml_lines.append("    Service:")
            yaml_lines.append("      - Repository")
            yaml_lines.append("      - Model")
            
        return "\n".join(yaml_lines)

    def generate_machine_json(self, run_id: int) -> str:
        """Generates a strict JSON dump of all analysis findings."""
        run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        metrics = self.db.query(ComponentMetric).filter(ComponentMetric.run_id == run_id).all()
        
        data = {
            "run_id": run_id,
            "project_id": run.project_id if run else None,
            "status": run.status if run else "unknown",
            "components": []
        }
        
        risk_map = {r.component_name: r for r in risks}
        
        for m in metrics:
            comp_data = {
                "name": m.component_name,
                "type": m.component_type,
                "metrics": {
                    "in_degree": m.in_degree,
                    "out_degree": m.out_degree,
                    "betweenness": m.betweenness,
                    "scc_size": m.scc_size
                },
                "risk": None
            }
            if m.component_name in risk_map:
                r = risk_map[m.component_name]
                comp_data["risk"] = {
                    "level": r.risk_level,
                    "score": r.risk_score,
                    "instability": r.instability,
                    "coupling_pressure": r.coupling_pressure
                }
            data["components"].append(comp_data)
            
        return json.dumps(data, indent=2)

    def generate_csv_export(self, run_id: int) -> str:
        """Generates a CSV of the ComponentRisk table for BI tools."""
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Component Name", "Type", "Risk Level", "Risk Score", 
            "Criticality Index", "Instability", "Coupling Pressure"
        ])
        
        for r in risks:
            writer.writerow([
                r.component_name, r.component_type, r.risk_level, round(r.risk_score, 2),
                round(r.criticality_index, 3), round(r.instability, 3), round(r.coupling_pressure, 3)
            ])
            
        return output.getvalue()

    def generate_human_report(self, run_id: int) -> str:
        """Generates an Executive Report directly from the Canonical Model with premium HTML/CSS."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.quality_gate import QualityGate
        from application.services.publishing.ai_advisory_service import AIAdvisoryService
        import json
        
        model = EvidenceBuilder(self.db).build(run_id)
        if not QualityGate().validate(model):
            return "<html><body><h1>Error: Quality Gate Failed</h1></body></html>"
            
        ctx = model.system_context
        readiness_pct = min(ctx.overall_readiness, 100.0) if ctx.overall_readiness > 1.0 else (ctx.overall_readiness * 100)
        
        # Phase 2: Get LLM Executive Summary
        ai_service = AIAdvisoryService()
        exec_summary = ai_service.synthesize_executive_summary(ctx, model.legacy_posture)
        
        html = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>Executive Modernization Assessment</title>",
            "    <script src='https://cdn.tailwindcss.com'></script>",
            "    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>",
            "    <script type='module'>",
            "        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';",
            "        mermaid.initialize({ startOnLoad: true, theme: 'dark' });",
            "    </script>",
            "    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap' rel='stylesheet'>",
            "    <style>",
            "        body { font-family: 'Inter', sans-serif; background-color: #0f111a; color: #e2e8f0; }",
            "        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }",
            "        .metric-value { font-size: 2rem; font-weight: 700; color: #38bdf8; }",
            "        .priority-Critical { color: #f87171; background: rgba(248, 113, 113, 0.1); border: 1px solid rgba(248, 113, 113, 0.2); }",
            "        .priority-High { color: #fbbf24; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.2); }",
            "        @media print { body { background: #fff; color: #000; } .glass-card { background: none; border: 1px solid #ccc; break-inside: avoid; } .metric-value { color: #000; } .print-hide { display: none !important; } }",
            "    </style>",
            "</head>",
            "<body class='p-8 md:p-16 max-w-6xl mx-auto'>",
            f"    <header class='mb-12 flex justify-between items-center'>",
            f"        <div>",
            f"            <h1 class='text-4xl font-bold text-white mb-2'>Strategic Modernization Assessment</h1>",
            f"            <p class='text-slate-400 text-lg'>Target System: <span class='text-sky-400 font-semibold'>{ctx.project_name}</span></p>",
            f"        </div>",
            f"        <button onclick='window.print()' class='px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-lg font-medium transition-colors print-hide'>Export to PDF</button>",
            f"    </header>",
            "",
            "    <!-- Section 1: Executive Summary -->",
            "    <div class='glass-card p-8 mb-8 grid grid-cols-1 md:grid-cols-2 gap-8'>",
            "        <div>",
            "            <h2 class='text-2xl font-semibold mb-4 text-white border-b border-slate-700 pb-2'>Executive Summary</h2>",
            f"           <h3 class='text-lg font-medium text-sky-300 mb-2'>Current State</h3>",
            f"           <p class='text-slate-300 mb-4'>{exec_summary.get('current_state', '')}</p>",
            f"           <h3 class='text-lg font-medium text-red-400 mb-2'>Critical Risks</h3>",
            f"           <p class='text-slate-300 mb-4'>{exec_summary.get('critical_risks', '')}</p>",
            f"           <h3 class='text-lg font-medium text-emerald-400 mb-2'>Strategic Roadmap</h3>",
            f"           <p class='text-slate-300'>{exec_summary.get('strategic_roadmap', '').replace(chr(10), '<br>')}</p>",
            "        </div>",
            "        <div class='flex flex-col items-center justify-center'>",
            "            <div class='text-center mb-4'>",
            "                <div class='text-5xl font-bold text-emerald-400'>{0:.1f}%</div>".format(readiness_pct),
            "                <div class='text-sm text-slate-400 uppercase tracking-wider mt-1'>Modernization Readiness</div>",
            "            </div>",
            "            <div class='w-full max-w-xs'>",
            "                <canvas id='radarChart'></canvas>",
            "            </div>",
            "        </div>",
            "    </div>",
            "",
            "    <!-- System Vitality Grid -->",
            "    <h3 class='text-xl font-semibold mb-4 border-b border-slate-700 pb-2'>System Vitality</h3>",
            "    <div class='grid grid-cols-2 md:grid-cols-5 gap-4 mb-12'>",
            f"        <div class='glass-card p-6'><p class='text-xs text-slate-400 uppercase tracking-wider mb-1'>Lines of Code</p><p class='metric-value'>{ctx.lines_of_code:,}</p></div>",
            f"        <div class='glass-card p-6'><p class='text-xs text-slate-400 uppercase tracking-wider mb-1'>Total Classes</p><p class='metric-value'>{ctx.total_classes:,}</p></div>",
            f"        <div class='glass-card p-6'><p class='text-xs text-slate-400 uppercase tracking-wider mb-1'>Avg Complexity</p><p class='metric-value'>{ctx.avg_complexity:.2f}</p></div>",
            f"        <div class='glass-card p-6'><p class='text-xs text-slate-400 uppercase tracking-wider mb-1'>Connectivity</p><p class='metric-value'>{ctx.connectivity:,}</p></div>",
            f"        <div class='glass-card p-6'><p class='text-xs text-slate-400 uppercase tracking-wider mb-1'>Test Coverage</p><p class='metric-value'>{ctx.test_coverage}</p></div>",
            "    </div>",
            "",
            "    <!-- Database Intelligence -->",
            "    <h3 class='text-xl font-semibold mb-4 border-b border-slate-700 pb-2'>Database & State Intelligence</h3>",
            "    <div class='glass-card p-6 mb-12 overflow-x-auto'>",
            "        <table class='w-full text-left text-sm text-slate-300'>",
            "            <thead class='text-xs text-slate-400 uppercase bg-slate-800/50'>",
            "                <tr>",
            "                    <th class='px-4 py-3 rounded-tl-lg'>Database Table / Stateful Component</th>",
            "                    <th class='px-4 py-3'>Write Intensity</th>",
            "                    <th class='px-4 py-3 rounded-tr-lg'>Shared Table Pressure</th>",
            "                </tr>",
            "            </thead>",
            "            <tbody>",
        ]
        
        for db in model.database_intelligence:
            html.append("                <tr class='border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors'>")
            html.append(f"                    <td class='px-4 py-3 font-medium text-sky-300'>{db.table_name}</td>")
            html.append(f"                    <td class='px-4 py-3'>{db.write_intensity:.2f}</td>")
            html.append(f"                    <td class='px-4 py-3 text-red-300 font-bold'>{db.shared_table_pressure:.2f}</td>")
            html.append("                </tr>")
            
        if not model.database_intelligence:
            html.append("                <tr><td colspan='3' class='px-4 py-3 text-center text-slate-500 italic'>No high-pressure database tables detected.</td></tr>")
            
        html.append("            </tbody>")
        html.append("        </table>")
        html.append("    </div>")
        
        html.append("    <!-- Risk Register -->")
        html.append("    <h3 class='text-xl font-semibold mb-4 border-b border-slate-700 pb-2'>Top Modernization Blockers</h3>")
        
        top_findings = [f for f in model.findings if f.priority in ["Critical", "High"]][:5]
        if not top_findings:
            html.append("    <p class='text-slate-400 italic'>No Critical or High priority blockers identified in this scan.</p>")
        else:
            for f in top_findings:
                html.append(f"    <div class='glass-card p-6 mb-6'>")
                html.append(f"        <div class='flex items-center gap-3 mb-4'>")
                html.append(f"            <span class='px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider priority-{f.priority}'>{f.priority}</span>")
                html.append(f"            <h4 class='text-lg font-semibold text-white'>{f.observation}</h4>")
                html.append(f"        </div>")
                html.append(f"        <div class='grid grid-cols-1 md:grid-cols-2 gap-6 mb-4 text-sm text-slate-300'>")
                html.append(f"            <div><span class='block text-slate-500 mb-1 uppercase tracking-wider text-xs'>Business Impact</span>{f.impact}</div>")
                html.append(f"            <div><span class='block text-slate-500 mb-1 uppercase tracking-wider text-xs'>Strategic Action</span>{f.recommended_action}</div>")
                html.append(f"        </div>")
                
                # Mermaid Diagram
                if f.mermaid_diagram:
                    html.append(f"        <div class='mt-6 p-4 bg-slate-900/50 rounded-lg'>")
                    html.append(f"            <p class='text-xs text-slate-500 uppercase tracking-wider mb-2'>Architecture Topology</p>")
                    html.append(f"            <pre class='mermaid flex justify-center'>\n{f.mermaid_diagram}\n            </pre>")
                    html.append(f"        </div>")
                html.append(f"    </div>")
                
        # Chart.js initialization script
        if model.legacy_posture:
            labels = ["Version", "Namespaces", "DB Layer", "Security", "Testability", "Coupling"]
            data = [
                model.legacy_posture.version_score * 10,
                model.legacy_posture.namespace_score * 10,
                model.legacy_posture.db_layer_score * 10,
                model.legacy_posture.security_score * 10,
                model.legacy_posture.testability_score * 10,
                model.legacy_posture.coupling_score * 10
            ]
            
            html.append("    <script>")
            html.append("    document.addEventListener('DOMContentLoaded', function() {")
            html.append("        var ctx = document.getElementById('radarChart').getContext('2d');")
            html.append("        new Chart(ctx, {")
            html.append("            type: 'radar',")
            html.append("            data: {")
            html.append(f"                labels: {json.dumps(labels)},")
            html.append("                datasets: [{")
            html.append("                    label: 'Modernization Posture (0-10)',")
            html.append(f"                    data: {json.dumps(data)},")
            html.append("                    backgroundColor: 'rgba(56, 189, 248, 0.2)',")
            html.append("                    borderColor: 'rgba(56, 189, 248, 1)',")
            html.append("                    pointBackgroundColor: 'rgba(56, 189, 248, 1)',")
            html.append("                    pointBorderColor: '#fff',")
            html.append("                    pointHoverBackgroundColor: '#fff',")
            html.append("                    pointHoverBorderColor: 'rgba(56, 189, 248, 1)'")
            html.append("                }]")
            html.append("            },")
            html.append("            options: {")
            html.append("                scales: {")
            html.append("                    r: {")
            html.append("                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },")
            html.append("                        grid: { color: 'rgba(255, 255, 255, 0.1)' },")
            html.append("                        pointLabels: { color: '#94a3b8', font: { family: 'Inter' } },")
            html.append("                        ticks: { display: false, min: 0, max: 10 }")
            html.append("                    }")
            html.append("                },")
            html.append("                plugins: {")
            html.append("                    legend: { display: false }")
            html.append("                }")
            html.append("            }")
            html.append("        });")
            html.append("    });")
            html.append("    </script>")
            
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)

    def generate_workspace_bundle(
        self, run_id: int, 
        html: bool = True, md: bool = True, csv: bool = True,
        sarif: bool = True, rector: bool = True, deptrac: bool = True,
        pdf: bool = True, docx: bool = True
    ) -> bytes:
        """Generates an in-memory ZIP archive of selected artifacts."""
        import zipfile
        import io
        import json
        import tempfile
        import os
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
            if html:
                zf.writestr("reports/executive_report.html", self.generate_human_report(run_id))
            if md:
                zf.writestr("reports/technical_assessment.md", self.generate_technical_report(run_id))
            if csv:
                zf.writestr("reports/risks.csv", self.generate_csv_export(run_id))
            if sarif:
                zf.writestr("machine/results.sarif", json.dumps(self.generate_sarif(run_id), indent=2))
            if rector:
                zf.writestr("machine/rector.php", self.generate_rector_config(run_id))
            if deptrac:
                zf.writestr("machine/deptrac.yaml", self.generate_deptrac_yaml(run_id))
            
            with tempfile.TemporaryDirectory() as tmpdirname:
                if pdf:
                    pdf_path = os.path.join(tmpdirname, "technical_assessment.pdf")
                    if self.generate_pdf_report(run_id, pdf_path):
                        with open(pdf_path, "rb") as f:
                            zf.writestr("reports/technical_assessment.pdf", f.read())
                
                if docx:
                    docx_path = os.path.join(tmpdirname, "technical_assessment.docx")
                    if self.generate_docx_report(run_id, docx_path):
                        with open(docx_path, "rb") as f:
                            zf.writestr("reports/technical_assessment.docx", f.read())
                
        return zip_buffer.getvalue()

    def generate_pdf_report(self, run_id: int, output_path: str) -> str:
        """Generates a PDF report using WeasyPrint."""
        md_content = self.generate_technical_report(run_id)
        from application.services.publishing.renderers.pdf_renderer import PdfRenderer
        return PdfRenderer().render(md_content, output_path)

    def generate_docx_report(self, run_id: int, output_path: str) -> str:
        """Generates a DOCX report using python-docx."""
        md_content = self.generate_technical_report(run_id)
        from application.services.publishing.renderers.docx_renderer import DocxRenderer
        return DocxRenderer().render(md_content, output_path)

    def generate_technical_report(self, run_id: int) -> str:
        """Generates a deep Technical Assessment Report."""
        from application.services.publishing.pipeline import PublishingPipeline
        
        pipeline = PublishingPipeline(self.db)
        return pipeline.publish_technical_report(run_id)
