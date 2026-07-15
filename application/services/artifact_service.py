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
        import hashlib
        
        # 1. Fetch CRITICAL and HIGH risks
        critical_high_risks = self.db.query(ComponentRisk).filter(
            ComponentRisk.run_id == run_id,
            ComponentRisk.risk_level.in_(["CRITICAL", "HIGH"])
        ).all()
        
        # 2. Fetch Top 15 MEDIUM risks (Strategic Blast Radius inclusion)
        medium_risks = self.db.query(ComponentRisk).filter(
            ComponentRisk.run_id == run_id,
            ComponentRisk.risk_level == "MEDIUM"
        ).order_by(ComponentRisk.risk_score.desc()).limit(15).all()
        
        risks = critical_high_risks + medium_risks
        
        # 3. Define Rules (Sanitized of personal URLs, richer descriptions)
        rules = [
            {
                "id": "STRATA-HIGH-COUPLING",
                "name": "HighCoupling",
                "shortDescription": {"text": "Component exhibits dangerous coupling pressure."},
                "fullDescription": {"text": "This component is tightly coupled to many other parts of the system, making changes highly risky and prone to cascading failures. Decouple by extracting responsibilities or introducing interfaces."},
                "defaultConfiguration": {"level": "error"}
            },
            {
                "id": "STRATA-STATEFUL-BOTTLENECK",
                "name": "StatefulBottleneck",
                "shortDescription": {"text": "Component maintains excessive state and acts as a bottleneck."},
                "fullDescription": {"text": "This component manages global or shared state, causing tight contention and making it difficult to scale or test in isolation. Consider stateless architectural patterns or dependency injection."},
                "defaultConfiguration": {"level": "error"}
            },
            {
                "id": "STRATA-STRUCTURAL-RISK",
                "name": "StructuralRisk",
                "shortDescription": {"text": "Component exhibits high structural risk."},
                "fullDescription": {"text": "This component has significant architectural issues such as high complexity or blast radius, requiring immediate remediation. Consider breaking it down into smaller, more focused modules."},
                "defaultConfiguration": {"level": "warning"}
            }
        ]

        results = []
        for r in risks:
            # Map risk level to SARIF severity level
            if r.risk_level == "CRITICAL":
                level = "error"
            elif r.risk_level == "HIGH":
                level = "warning"
            else:
                level = "note"
                
            if r.coupling_pressure and r.coupling_pressure > 0.4:
                rule_id = "STRATA-HIGH-COUPLING"
            elif r.is_stateful:
                rule_id = "STRATA-STATEFUL-BOTTLENECK"
            else:
                rule_id = "STRATA-STRUCTURAL-RISK"
                
            # Try to resolve a file path from GraphNode
            node = self.db.query(GraphNode).filter(GraphNode.run_id == run_id, GraphNode.name == r.component_name).first()
            uri = node.file_path if node and node.file_path else f"{r.component_name}.php"
            uri = uri.lstrip('/')
            
            # Ensure no phantom classes in file path
            if '::' in uri:
                uri = uri.replace('::', '/')
                
            # Extract line numbers from AST metadata if available
            start_line = 1
            end_line = None
            if node and node.metadata_json:
                try:
                    meta = json.loads(node.metadata_json)
                    start_line = int(meta.get("start_line", meta.get("startLine", 1)))
                    if "end_line" in meta or "endLine" in meta:
                        end_line = int(meta.get("end_line", meta.get("endLine")))
                except Exception:
                    pass
                    
            region = {"startLine": start_line}
            if end_line:
                region["endLine"] = end_line
                
            # Generate deterministic fingerprint for deduplication across commits
            fingerprint_hash = hashlib.md5(f"{r.component_name}_{rule_id}".encode('utf-8')).hexdigest()
            
            result = {
                "ruleId": rule_id,
                "level": level,
                "message": {
                    "text": f"Component '{r.component_name}' exhibits structural risk. Review the attached properties and code flows for details."
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": uri,
                                "uriBaseId": "%SRCROOT%"
                            },
                            "region": region
                        }
                    }
                ],
                "properties": {
                    "risk_score": round(r.risk_score, 2) if r.risk_score else 0.0,
                    "coupling_pressure": round(r.coupling_pressure, 2) if r.coupling_pressure else 0.0,
                    "criticality_index": round(r.criticality_index, 3) if r.criticality_index else 0.0,
                    "instability": round(r.instability, 3) if r.instability else 0.0
                },
                "partialFingerprints": {
                    "primaryLocationLineHash": fingerprint_hash
                }
            }
            
            # Build CodeFlows for Highly Coupled components to visually map dependencies
            if rule_id == "STRATA-HIGH-COUPLING":
                deps = self.db.query(ComponentDependency).filter(
                    ComponentDependency.run_id == run_id,
                    (ComponentDependency.source_id == r.component_name) | (ComponentDependency.target_id == r.component_name)
                ).limit(3).all()
                
                if deps:
                    locations = []
                    step_num = 1
                    for dep in deps:
                        dep_target = dep.target_id if dep.source_id == r.component_name else dep.source_id
                        dep_node = self.db.query(GraphNode).filter(GraphNode.run_id == run_id, GraphNode.name == dep_target).first()
                        dep_uri = dep_node.file_path.lstrip('/') if dep_node and dep_node.file_path else f"{dep_target}.php".replace('::', '/')
                        
                        dep_start = 1
                        if dep_node and dep_node.metadata_json:
                            try:
                                dmeta = json.loads(dep_node.metadata_json)
                                dep_start = int(dmeta.get("start_line", dmeta.get("startLine", 1)))
                            except Exception:
                                pass
                                
                        edge_action = "invokes" if dep.source_id == r.component_name else "is invoked by"
                        comp_type = node.node_type if node else "component"
                        dep_type = dep_node.node_type if dep_node else "component"
                        
                        locations.append({
                            "location": {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": dep_uri,
                                        "uriBaseId": "%SRCROOT%"
                                    },
                                    "region": {
                                        "startLine": dep_start
                                    }
                                },
                                "message": {
                                    "text": f"Step {step_num}: The '{r.component_name}' {comp_type} {edge_action} the '{dep_target}' {dep_type} ({dep.edge_type}), creating a tight dependency chain."
                                }
                            }
                        })
                        step_num += 1
                        
                    if locations:
                        result["codeFlows"] = [{"threadFlows": [{"locations": locations}]}]

            results.append(result)

        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Strata Modernization Intelligence",
                            "rules": rules
                        }
                    },
                    "results": results
                }
            ]
        }
        return sarif

    def generate_rector_config(self, run_id: int) -> str:
        """Deterministically generates rector.php configuration."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.renderers.rector_generator import RectorGenerator
        model = EvidenceBuilder(self.db).build(run_id)
        return RectorGenerator().generate(model)

    def generate_deptrac_yaml(self, run_id: int) -> str:
        """Deterministically generates deptrac.yaml configuration."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.renderers.deptrac_generator import DeptracGenerator
        model = EvidenceBuilder(self.db).build(run_id)
        return DeptracGenerator().generate(model)

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
        """Generates the comprehensive Navigatable HTML Application."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.renderers.html_renderer import HtmlRenderer
        
        model = EvidenceBuilder(self.db).build(run_id)
        renderer = HtmlRenderer()
        return renderer.render(model, run_id)

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
        from application.services.publishing.evidence_builder import EvidenceBuilder
        
        data_dir = os.environ.get("DATA_DIR", "/data")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
            if html:
                zf.writestr("index.html", self.generate_human_report(run_id))
            if md:
                zf.writestr("reports/Master_Intelligence_Report.md", self.generate_technical_report(run_id))
            if csv:
                zf.writestr("data_exports/complete_risk_inventory.csv", self.generate_csv_export(run_id))
            if sarif:
                zf.writestr("machine_readable/strata_results.sarif", json.dumps(self.generate_sarif(run_id), indent=2))
            if rector:
                zf.writestr("machine_readable/rector_playbook.php", self.generate_rector_config(run_id))
            if deptrac:
                zf.writestr("machine_readable/deptrac_boundaries.yaml", self.generate_deptrac_yaml(run_id))
                
            # Embed Raw Data Assets for transparency and 3rd-party consumption
            graph_path = os.path.join(data_dir, f"graph_{run_id}.json")
            if os.path.exists(graph_path):
                with open(graph_path, "r") as gf:
                    zf.writestr(f"raw_data/graph_{run_id}.json", gf.read())
                    
            try:
                model = EvidenceBuilder(self.db).build(run_id)
                zf.writestr("raw_data/canonical_model.json", model.model_dump_json(indent=2))
            except Exception as e:
                pass
            
            with tempfile.TemporaryDirectory() as tmpdirname:
                if pdf:
                    pdf_path = os.path.join(tmpdirname, "Master_Intelligence_Report.pdf")
                    if self.generate_pdf_report(run_id, pdf_path):
                        with open(pdf_path, "rb") as f:
                            zf.writestr("reports/Master_Intelligence_Report.pdf", f.read())
                
                if docx:
                    docx_path = os.path.join(tmpdirname, "Master_Intelligence_Report.docx")
                    if self.generate_docx_report(run_id, docx_path):
                        with open(docx_path, "rb") as f:
                            zf.writestr("reports/Master_Intelligence_Report.docx", f.read())
                
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
        """Generates a deep Technical Assessment Report using Markdown."""
        from application.services.publishing.evidence_builder import EvidenceBuilder
        from application.services.publishing.renderers.markdown_renderer import MarkdownRenderer
        
        model = EvidenceBuilder(self.db).build(run_id)
        renderer = MarkdownRenderer()
        return renderer.render(model, run_id)
