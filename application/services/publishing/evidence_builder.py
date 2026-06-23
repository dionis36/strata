from typing import List, Dict
from sqlalchemy.orm import Session
from infrastructure.persistence.models import ComponentRisk, LegacyMetrics, ComponentMetric, AnalysisRun, Project
from application.services.publishing.models import CanonicalModel, SystemContext, Module, Finding, Evidence, BoundaryIntelligence, LayeredArchitecture, PresentationCoupling, ApiEndpoint, VendorDependency, BoundedContext

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
        
        # Load dynamic project identity and business domain documentation
        import os
        import json
        project_description = "No project description available."
        if project and project.root_path and os.path.exists(project.root_path):
            readme_path = os.path.join(project.root_path, "README.md")
            if not os.path.exists(readme_path):
                readme_path = os.path.join(project.root_path, "readme.md")
            
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        project_description = f.read(2000)
                except Exception:
                    pass
            else:
                composer_path = os.path.join(project.root_path, "composer.json")
                if os.path.exists(composer_path):
                    try:
                        with open(composer_path, "r", encoding="utf-8") as f:
                            composer_data = json.load(f)
                            project_description = composer_data.get("description", "No description in composer.json")
                    except Exception:
                        pass

        # 1. Hydrate System Context
        from application.services.layer_service import LayerService
        layer_service = LayerService(self.db)
        footprint = {}
        try:
            l_data = layer_service.get_layered_analysis(run_id)
            dirs = l_data.get("layer_1", {}).get("directories", {})
            models = controllers = jobs = schemas = views = vendor = 0
            for info in dirs.values():
                for f in info.get("files", []):
                    role = f.get("role", "file") if isinstance(f, dict) else "file"
                    if role == "model": models += 1
                    elif role == "controller": controllers += 1
                    elif role == "job": jobs += 1
                    elif role == "schema": schemas += 1
                    elif role == "view": views += 1
                    elif role == "vendor": vendor += 1
            footprint = {
                "Models": models,
                "Controllers": controllers,
                "CLI_Scripts": jobs,
                "Schemas": schemas,
                "Views": views,
                "Vendor_Files": vendor
            }
        except Exception:
            pass

        ctx = SystemContext(
            project_name=project.name if project else "Unknown Project",
            project_description=project_description,
            total_files=run.total_files or 0,
            total_classes=run.total_classes or 0,
            lines_of_code=run.total_loc or 0,
            avg_complexity=round(run.avg_complexity, 2) if run.avg_complexity else 0.0,
            connectivity=run.total_edges or 0,
            test_coverage="N/A",  # Extracted in Phase 8
            php_era=legacy.php_era if legacy else "Unknown",
            framework=legacy.detected_framework if legacy else "Custom/None",
            overall_readiness=legacy.total_modernization_score if legacy else 0.0,
            architectural_footprint=footprint,
            root_path=project.root_path if project else None
        )
        
        # 2. Hydrate Database Intelligence
        db_intel = self._extract_database_intelligence(run_id)
        
        # 3. Hydrate Legacy Intelligence
        legacy_intel = self._extract_legacy_intelligence(run_id)

        # 4. Hydrate Modules (Inferred from metrics for now)
        modules = self._infer_modules(run_id)
        
        # 5. Hydrate Findings (From Risks)
        findings = self._extract_findings(run_id)
        
        # 6. Hydrate Extended Intelligence
        dep_intel = self._extract_dependency_intelligence(run_id)
        state_intel = self._extract_global_state_intelligence(run_id)
        full_risk_register = self._extract_full_risk_register(run_id)
        
        # 7. Hydrate Boundary Intelligence & Layered Architecture
        boundary_intel = self._extract_boundary_intelligence(run_id)
        layered_arch = self._extract_layered_architecture(run_id)
        
        # 8. AI Executive Summary & Strategic Advisory
        import json
        
        from application.services.advisory_service import AdvisoryService
        strategic_advisory = {}
        try:
            adv_service = AdvisoryService()
            strategic_advisory = adv_service.get_strategic_roadmap(run_id)
        except Exception as e:
            pass
        
        ai_exec_summary = {}
        if run and run.ai_executive_summary_json:
            try:
                ai_exec_summary = json.loads(run.ai_executive_summary_json)
            except Exception:
                pass
        
        return CanonicalModel(
            system_context=ctx,
            legacy_intelligence=legacy_intel,
            database_intelligence=db_intel,
            dependency_intelligence=dep_intel,
            global_state_intelligence=state_intel,
            boundary_intelligence=boundary_intel,
            layered_architecture=layered_arch,
            strategic_advisory=strategic_advisory,
            modules=modules,
            findings=findings,
            full_risk_register=full_risk_register,
            ai_executive_summary=ai_exec_summary
        )

    def _extract_database_intelligence(self, run_id: int):
        from application.services.database_intelligence_service import DatabaseIntelligenceService
        try:
            service = DatabaseIntelligenceService(self.db)
            return service.get_db_intelligence(run_id)
        except Exception as e:
            return {}

    def _extract_legacy_intelligence(self, run_id: int):
        from application.services.legacy_intelligence_service import LegacyIntelligenceService
        try:
            service = LegacyIntelligenceService(self.db)
            return service.get_legacy_intelligence(run_id)
        except Exception as e:
            return {}

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
        risks = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).order_by(ComponentRisk.final_risk.desc()).limit(50).all()
        findings = []
        
        top_risks = [r for r in risks if r.risk_score >= 0.3]
        if not top_risks:
            return findings
            
        # Deterministic Risk Dictionary
        risk_dictionary = {
            "GOD_CLASS": {
                "impact": "Massive blast radius. Modifications to this component are highly likely to cause regression failures across unrelated modules.",
                "reasoning": "High structural coupling pressure and extreme Weighted Method Count indicates a severe lack of cohesion.",
                "action": "Extract cohesive behaviors into dedicated service classes. Implement strict interfaces for external callers."
            },
            "FAT_VIEW": {
                "impact": "High architectural blast radius. Procedural database logic in the presentation layer exposes the application to SQL injection and blocks automated version upgrades.",
                "reasoning": "Presentation files tightly entangled with database queries violate MVC principles.",
                "action": "Isolate logic into a dedicated Controller/Repository context. Rewrite legacy queries using PDO abstractions."
            },
            "HIGH_COUPLING": {
                "impact": "Tight coupling prevents modular extraction and makes automated testing virtually impossible.",
                "reasoning": "High fan-in and fan-out metrics indicate the component is deeply entangled.",
                "action": "Isolate dependencies behind an interface. Write characterization tests before attempting extraction."
            }
        }
        
        for r in top_risks:
            evidence = [
                Evidence(type="file", target=r.component_name),
                Evidence(type="metric", target="risk_score", metric_value=r.risk_score),
                Evidence(type="metric", target="coupling_pressure", metric_value=r.coupling_pressure)
            ]
            
            # Determine best matched risk dictionary item
            archetype = r.semantic_archetype if hasattr(r, 'semantic_archetype') and r.semantic_archetype else ""
            if "GOD_CLASS" in archetype.upper():
                risk_profile = risk_dictionary["GOD_CLASS"]
            elif "VIEW" in archetype.upper() or r.component_name.endswith(".phtml") or r.component_name.endswith(".blade.php"):
                risk_profile = risk_dictionary["FAT_VIEW"]
            else:
                risk_profile = risk_dictionary["HIGH_COUPLING"]
            
            mermaid_safe_name = r.component_name.split('/')[-1].replace('.', '_')
            f = Finding(
                id=f"FND-{r.id}",
                category="Architecture",
                observation=f"Critical Architectural Bottleneck in {r.component_name}",
                evidence=evidence,
                impact=risk_profile["impact"],
                reasoning=risk_profile["reasoning"],
                recommended_action=risk_profile["action"],
                priority="Critical" if r.risk_score > 0.8 else "High",
                confidence="Confirmed" if r.risk_score > 0.8 else "Probable",
                mermaid_diagram=f"graph TD\n  {mermaid_safe_name} --> LegacyDependencies\n  style {mermaid_safe_name} fill:#f9f,stroke:#333,stroke-width:4px"
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
        from application.services.global_state_service import GlobalStateService
        try:
            service = GlobalStateService(self.db)
            return service.get_global_state_intelligence(run_id)
        except Exception as e:
            return {}

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

    def _extract_boundary_intelligence(self, run_id: int):
        from application.services.boundary_intelligence_service import BoundaryIntelligenceService
        boundary_service = BoundaryIntelligenceService(self.db)
        b_data = boundary_service.get_boundary_intelligence(run_id)
        if not b_data:
            return None
            
        presentation_coupling = []
        for p in b_data.get("presentation_coupling", []):
            # Parse entanglement ratio back to float for the model
            ratio_str = p.get("Entanglement Ratio", "0%")
            ratio_float = float(ratio_str.replace('%', '')) if '%' in ratio_str else 0.0
            presentation_coupling.append(PresentationCoupling(
                file_path=p.get("File", ""),
                ui_entanglement_ratio=ratio_float,
                is_fat_view="CRITICAL" in p.get("Severity", ""),
                db_queries=p.get("DB Operations", 0)
            ))
            
        api_surface = []
        for a in b_data.get("api_surface", []):
            api_surface.append(ApiEndpoint(
                path=a.get("Entry Point", ""),
                type=a.get("Type", "Unknown"),
                methods=[]
            ))
            
        vendor_inventory = []
        for v in b_data.get("vendor_intelligence", []):
            vendor_inventory.append(VendorDependency(
                file_path=v.get("File", ""),
                vendor_type=v.get("Vendor Type", "Unknown"),
                status=v.get("Status", "Unknown")
            ))
            
        return BoundaryIntelligence(
            presentation_coupling=presentation_coupling,
            api_surface=api_surface,
            vendor_inventory=vendor_inventory,
            kpis=b_data.get("kpis", {})
        )

    def _extract_layered_architecture(self, run_id: int):
        from application.services.layer_service import LayerService
        layer_service = LayerService(self.db)
        l_data = layer_service.get_layered_analysis(run_id)
        if not l_data:
            return None
            
        l1 = l_data.get("layer_1", {})
        dirs = l1.get("directories", {})
        
        # Calculate presentation ratio
        role_counts = {}
        total_files = 0
        for info in dirs.values():
            for f in info.get("files", []):
                total_files += 1
                role = f.get("role", "file") if isinstance(f, dict) else "file"
                role_counts[role] = role_counts.get(role, 0) + 1
        
        presentation_roles = ["view", "controller", "asset"]
        presentation_count = sum(role_counts.get(r, 0) for r in presentation_roles)
        presentation_ratio = (presentation_count / total_files * 100) if total_files > 0 else 0.0
        
        # Extract bounded contexts
        contexts = []
        l3 = l_data.get("layer_3", {})
        for c in l3.get("bounded_contexts", []):
            contexts.append(BoundedContext(
                name=c.get("name", "Unknown"),
                file_count=c.get("file_count", 0),
                internal_calls=c.get("internal_calls", 0),
                external_calls=c.get("external_calls", 0),
                coupling_ratio=c.get("coupling_ratio", 0.0),
                db_access=c.get("db_access", False),
                auth_access=c.get("auth_access", False)
            ))
            
        # Build hierarchical tree for frontend rendering
        tree = {}
        for path, info in sorted(dirs.items()):
            parts = [p for p in path.split('/') if p]
            if not parts:
                parts = ["root"]
            current = tree
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_info": None, "_children": {}}
                if i == len(parts) - 1:
                    current[part]["_info"] = info
                current = current[part]["_children"]

        # Parse and downsample System Topology Graph for browser-safe Vis.js rendering
        import os
        import json
        topology = {"nodes": [], "edges": []}
        
        # Try local data directory and fallback paths
        graph_paths = [
            f"data/graph_{run_id}.json",
            f"/data/graph_{run_id}.json"
        ]
        graph_data = None
        for gp in graph_paths:
            if os.path.exists(gp):
                try:
                    with open(gp, "r", encoding="utf-8") as f:
                        graph_data = json.load(f)
                    break
                except Exception:
                    pass
                    
        if graph_data:
            try:
                links = graph_data.get("links", [])
                nodes = graph_data.get("nodes", [])
                
                node_degree = {}
                for l in links:
                    s = l.get("source")
                    t = l.get("target")
                    if s: node_degree[s] = node_degree.get(s, 0) + 1
                    if t: node_degree[t] = node_degree.get(t, 0) + 1
                    
                selected_types = {"class", "entry_point", "controller", "view", "job", "vendor"}
                filtered_nodes = [n for n in nodes if n.get("type") in selected_types]
                sorted_nodes = sorted(filtered_nodes, key=lambda n: node_degree.get(n["id"], 0), reverse=True)
                top_nodes = sorted_nodes[:150]  # Downsample to top 150 nodes to avoid bloating HTML size and freezing browser Vis.js
                top_node_ids = {n["id"] for n in top_nodes}
                
                role_colors = {
                    "entry_point": "#ff4b4b", "controller": "#00d4ff", "view": "#00cc96",
                    "config": "#f9a825", "bootstrap": "#ab47bc", "vendor": "#757575",
                    "file": "#90a4ae", "class": "#5c6bc0", "job": "#ff1744"
                }
                
                mapped_nodes = []
                for n in top_nodes:
                    ntype = n.get("type", "file")
                    color = role_colors.get(ntype, "#90a4ae")
                    deg = node_degree.get(n["id"], 1)
                    size = 15 + (deg * 2) if deg > 5 else 15
                    
                    if n.get("domain_archetype") == "GOD_CLASS":
                        color = "#ff1744"
                        size += 10
                        
                    mapped_nodes.append({
                        "id": n["id"],
                        "label": n.get("name") or n["id"],
                        "color": color,
                        "size": min(size, 45)
                    })
                    
                mapped_edges = []
                for l in links:
                    s = l.get("source")
                    t = l.get("target")
                    if s in top_node_ids and t in top_node_ids:
                        mapped_edges.append({
                            "source": s,
                            "target": t
                        })
                
                topology = {"nodes": mapped_nodes, "edges": mapped_edges}
            except Exception:
                pass

        return LayeredArchitecture(
            presentation_ratio=presentation_ratio,
            bounded_contexts=contexts,
            directory_tree=tree,
            file_type_distribution=l1.get("file_types", {}),
            system_topology=topology
        )
