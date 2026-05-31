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
        """Generates an Executive Report using the Publishing Pipeline."""
        from application.services.publishing.pipeline import PublishingPipeline
        
        pipeline = PublishingPipeline(self.db)
        markdown_content = pipeline.publish_executive_report(run_id)
        
        # Simple Markdown to HTML converter to avoid external dependencies
        import re
        html_body = markdown_content
        html_body = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^- (.*?)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
        html_body = re.sub(r'`(.*?)`', r'<code>\1</code>', html_body)
        
        # Format Mermaid blocks for HTML rendering
        html_body = re.sub(r'```mermaid\n(.*?)\n```', r'<pre class="mermaid">\n\1\n</pre>', html_body, flags=re.DOTALL)
        
        html_body = html_body.replace('\n\n', '<br><br>')
        
        html = [
            "<html><head>",
            "<script type=\"module\">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs'; mermaid.initialize({ startOnLoad: true, theme: 'dark' });</script>",
            "<style>",
            "body { font-family: 'Inter', sans-serif; background-color: #0e1117; color: #e0e0e0; padding: 40px; }",
            "h1, h2, h3 { color: #58a6ff; }",
            "p, li { line-height: 1.6; }",
            "code { background-color: #1f2937; padding: 2px 4px; border-radius: 4px; }",
            "</style></head><body>",
            html_body,
            "</body></html>"
        ]
        return "\n".join(html)

    def generate_workspace_bundle(
        self, run_id: int, 
        html: bool = True, md: bool = True, csv: bool = True,
        sarif: bool = True, rector: bool = True, deptrac: bool = True
    ) -> bytes:
        """Generates an in-memory ZIP archive of selected artifacts."""
        import zipfile
        import io
        import json
        
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
                zf.writestr("machine/deptrac.yaml", self.generate_deptrac_config(run_id))
                
        return zip_buffer.getvalue()

    def generate_technical_report(self, run_id: int) -> str:
        """Generates a deep Technical Assessment Report."""
        from application.services.publishing.pipeline import PublishingPipeline
        
        pipeline = PublishingPipeline(self.db)
        return pipeline.publish_technical_report(run_id)
