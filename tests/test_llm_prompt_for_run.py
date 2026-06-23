import os
import sys
import argparse
import json

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import AnalysisRun, ComponentRisk, LegacyMetrics, ComponentBehavior, Project
from application.services.publishing.ai_advisory_service import AIAdvisoryService
from application.services.layer_service import LayerService
from application.services.advisory_service import AdvisoryService

def get_run_prompt_data(run_id: int):
    """Extracts exactly the data that background_synthesize_intelligence does."""
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            print(f"Run ID {run_id} not found in database.")
            sys.exit(1)
            
        project_name = "Strata Analysis Monolith"
        project_description = "No project description available."
        
        if run.project_id:
            proj = db.query(Project).filter(Project.id == run.project_id).first()
            if proj:
                project_name = proj.name
                if proj.root_path and os.path.exists(proj.root_path):
                    readme_path = os.path.join(proj.root_path, "README.md")
                    if not os.path.exists(readme_path):
                        readme_path = os.path.join(proj.root_path, "readme.md")
                    if os.path.exists(readme_path):
                        try:
                            with open(readme_path, "r", encoding="utf-8") as f:
                                project_description = f.read(2000)
                        except Exception:
                            pass

        class ProjectContext:
            def __init__(self, name, description, total_files, loc):
                self.project_name = name
                self.project_description = description
                self.total_files = total_files
                self.lines_of_code = loc
                self.framework = "Unknown"
                self.php_era = "Unknown"
                self.overall_readiness = 50.0
                self.architectural_footprint = {}
                
        ctx = ProjectContext(project_name, project_description, run.total_files, run.total_loc)
        legacy = db.query(LegacyMetrics).filter(LegacyMetrics.run_id == run_id).first()
        
        if legacy:
            ctx.framework = legacy.detected_framework or "Unknown"
            ctx.php_era = legacy.php_era or "Unknown"
            ctx.overall_readiness = legacy.total_modernization_score * 10 if legacy.total_modernization_score else 0.0
            
        try:
            layer_service = LayerService(db)
            l_data = layer_service.get_layered_analysis(run_id)
            dirs = l_data.get("layer_1", {}).get("directories", {})
            models = controllers = views = 0
            for info in dirs.values():
                for f in info.get("files", []):
                    role = f.get("role", "file") if isinstance(f, dict) else "file"
                    if role == "model": models += 1
                    elif role == "controller": controllers += 1
                    elif role == "view": views += 1
            ctx.architectural_footprint = {
                "Models": models,
                "Controllers": controllers,
                "Views": views
            }
        except Exception as e:
            print(f"Warning: Layer analysis failed: {e}")
            
        hotspots_data = []
        try:
            high_risk_objs = db.query(ComponentRisk).filter(
                ComponentRisk.run_id == run_id
            ).order_by(ComponentRisk.final_risk.desc()).limit(3).all()
            for hr in high_risk_objs:
                behav = db.query(ComponentBehavior).filter(
                    ComponentBehavior.run_id == run_id,
                    ComponentBehavior.component_name == hr.component_name
                ).first()
                hotspots_data.append({
                    "file_path": hr.component_name,
                    "risk_score": hr.final_risk,
                    "lcom": hr.lcom,
                    "wmc": hr.wmc,
                    "instability": hr.instability,
                    "coverage": hr.test_coverage if hr.test_coverage is not None else 0.0,
                    "write_intensity": behav.write_intensity if behav else 0.0
                })
        except Exception as e:
            print(f"Warning: Failed to fetch hotspots: {e}")

        recs = []
        try:
            adv_service = AdvisoryService()
            advisory_data = adv_service.get_strategic_roadmap(run_id)
            recs = advisory_data.get("recommendations", [])
        except Exception as e:
            print(f"Warning: Failed to fetch advisory roadmap: {e}")

        from application.services.boundary_intelligence_service import BoundaryIntelligenceService
        try:
            bd = BoundaryIntelligenceService(db).get_boundary_intelligence(run_id)
            boundary_data = {
                "kpis": bd.get("kpis", {}),
                "presentation_coupling_count": len(bd.get("presentation_coupling", [])),
                "api_surface_count": len(bd.get("api_surface", [])),
                "vendor_intelligence_count": len(bd.get("vendor_intelligence", [])),
                "top_presentation_coupling": bd.get("presentation_coupling", [])[:5]
            } if bd else None
        except Exception:
            boundary_data = None
            
        from application.services.database_intelligence_service import DatabaseIntelligenceService
        try:
            dbd = DatabaseIntelligenceService(db).get_db_intelligence(run_id)
            database_data = {
                "total_models": len(dbd.get("taxonomy", [])),
                "top_active_models": sorted(dbd.get("taxonomy", []), key=lambda x: x.get("Writes", 0) + x.get("Reads", 0), reverse=True)[:5]
            } if dbd else None
        except Exception:
            database_data = None
            
        try:
            l_data = layer_service.get_layered_analysis(run_id)
            architecture_data = {
                "bounded_contexts": l_data.get("layer_3", {}).get("bounded_contexts", [])
            } if l_data else None
        except Exception:
            architecture_data = None
            
        from application.services.global_state_service import GlobalStateService
        try:
            gsd = GlobalStateService(db).get_global_state_intelligence(run_id)
            global_state_data = {
                "superglobal_usage": gsd.get("superglobals", {}),
                "singleton_count": len(gsd.get("singletons", []))
            } if gsd else None
        except Exception:
            global_state_data = None

        return ctx, legacy, recs, hotspots_data, boundary_data, database_data, architecture_data, global_state_data
    finally:
        db.close()

def save_summary_to_db(run_id: int, summary: dict):
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.ai_executive_summary_json = json.dumps(summary)
            run.error_message = None
            run.status = "intelligence_ready"
            db.commit()
            print(f"✅ Successfully saved AI Intelligence to database for Run ID {run_id}!")
    except Exception as e:
        print(f"❌ Failed to save to database: {e}")
    finally:
        db.close()

def check_run_status(run_id: int) -> bool:
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        return run is not None and run.status == "intelligence_ready"
    finally:
        db.close()

def ping_llm(ai_service):
    """Sends a minimal 1-token prompt to verify the LLM API is alive."""
    import requests
    print("Pinging LLM API to check connectivity and rate limits...")
    
    if ai_service.openrouter_key:
        print(f"Pinging OpenRouter (Model: {ai_service.openrouter_model})...")
        headers = {
            "Authorization": f"Bearer {ai_service.openrouter_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": ai_service.openrouter_model,
            "messages": [{"role": "user", "content": "Ping."}],
            "max_tokens": 5
        }
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            res.raise_for_status()
            print("✅ OpenRouter Ping Successful!")
            return True
        except Exception as e:
            print(f"❌ OpenRouter Ping Failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            if not getattr(ai_service, 'client', None):
                return False
            print("Falling back to Gemini Ping...")
            
    if getattr(ai_service, 'client', None):
        print("Pinging Native Gemini (gemini-1.5-flash)...")
        try:
            ai_service.client.models.generate_content(
                model='gemini-1.5-flash',
                contents="Ping."
            )
            print("✅ Native Gemini Ping Successful!")
            return True
        except Exception as e:
            print(f"❌ Native Gemini Ping Failed: {e}")
            return False
            
    return False

def main():
    parser = argparse.ArgumentParser(description="Test LLM Prompt for a specific Run ID")
    parser.add_argument("--run-id", type=int, default=1, help="Analysis Run ID to extract context for")
    parser.add_argument("--invoke", action="store_true", help="Actually invoke the AI Advisory Service")
    parser.add_argument("--print-prompt", action="store_true", help="Print the generated prompt string")
    parser.add_argument("--save", action="store_true", help="Save the generated JSON to the database, updating the frontend state")
    parser.add_argument("--force", action="store_true", help="Force overwrite if AI data already exists")
    
    args = parser.parse_args()
    
    if (args.invoke or args.save) and check_run_status(args.run_id) and not args.force:
        print(f"⚠️  Run ID {args.run_id} already has AI Intelligence generated (status: intelligence_ready).")
        print("Use --force to overwrite the existing data in the database.")
        sys.exit(0)
        
    ai_service = AIAdvisoryService()
    
    if args.invoke:
        is_online = ping_llm(ai_service)
        if not is_online:
            print("\n⛔ Aborting full payload prompt because LLM ping failed (Rate limit, Auth error, or Overload).")
            sys.exit(1)
            
    print(f"\nExtracting context for Run ID {args.run_id}...")
    ctx, legacy, recs, hotspots_data, boundary_data, database_data, architecture_data, global_state_data = get_run_prompt_data(args.run_id)
    
    # We can reconstruct the prompt just to print it using the exact same logic as AIAdvisoryService
    if args.print_prompt or not args.invoke:
        recs_str = "\n".join([
            f"- Module '{r.get('Context')}': Recommend {r.get('Recommended Strategy')} (ROI: {r.get('Modernization ROI')}%, Effort: {r.get('Migration Effort')}). Rationale: {r.get('Rationale')}. Primary Blocker: {r.get('Primary Blocker')}."
            for r in recs
        ]) if recs else "No specific module-level recommendations calculated."

        hotspots_str = "\n".join([
            f"- File '{h['file_path']}': Risk Score: {h['risk_score']:.1f}/100, WMC (Complexity): {h['wmc']}, LCOM (Lack of Cohesion): {h['lcom']:.2f}, Instability: {h['instability']:.2f}, Test Coverage: {h['coverage']*100:.1f}%, DB Write Intensity: {h['write_intensity']:.2f}."
            for hr, h in zip(range(len(hotspots_data)), hotspots_data)
        ]) if hotspots_data else "No specific code hotspots or risk items isolated."
        
        boundary_str = str(boundary_data) if boundary_data else "None"
        database_str = str(database_data) if database_data else "None"
        architecture_str = str(architecture_data) if architecture_data else "None"
        global_state_str = str(global_state_data) if global_state_data else "None"

        prompt = f"""
        You are a Principal PHP Modernization Architect consulting for a C-level executive.
        
        Analyze the overall health and structure of this legacy system:
        System Context:
        - Project: {ctx.project_name}
        - Project Description / Documentation (README Excerpt): {getattr(ctx, 'project_description', 'No description available.')}
        - Total Files: {ctx.total_files}
        - Lines of Code: {ctx.lines_of_code}
        - Framework: {ctx.framework} ({ctx.php_era})
        - Overall Readiness: {ctx.overall_readiness}%
        - Architectural Footprint: {ctx.architectural_footprint}
        
        Legacy Posture Scores (0.0 to 10.0 scale, where 10 is modern):
        - Version Score: {legacy.version_score if legacy else 'N/A'}
        - Namespace Score: {legacy.namespace_score if legacy else 'N/A'}
        - Database Layer Score: {legacy.db_layer_score if legacy else 'N/A'}
        - Security Score: {legacy.security_score if legacy else 'N/A'}
        - Testability Score: {legacy.testability_score if legacy else 'N/A'}
        - Coupling Score: {legacy.coupling_score if legacy else 'N/A'}
        
        Detailed Backend Recommendations calculated per cluster:
        {recs_str}
        
        Identified Hotspots & Code-Level Risks:
        {hotspots_str}
        
        Boundary Intelligence:
        {boundary_str}
        
        Database Intelligence:
        {database_str}
        
        Architecture Data:
        {architecture_str}
        
        Global State Data:
        {global_state_str}
        """
        print("\n" + "="*50)
        print("=== LLM PROMPT PAYLOAD ===")
        print("="*50)
        print(prompt.strip())
        print("="*50)
        print(f"Approximate Character Count: {len(prompt)}")
        print("="*50 + "\n")

    if args.invoke:
        import threading
        import sys
        import time

        spinner_running = True
        def spinner_task():
            spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            idx = 0
            while spinner_running:
                sys.stdout.write(f"\rWaiting for AI response... {spinners[idx]} ")
                sys.stdout.flush()
                idx = (idx + 1) % len(spinners)
                time.sleep(0.1)

        print("\n")
        spinner_thread = threading.Thread(target=spinner_task)
        spinner_thread.start()
        
        try:
            summary = ai_service.synthesize_executive_summary(
                ctx, legacy, recs, hotspots_data,
                boundary_data=boundary_data,
                database_data=database_data,
                architecture_data=architecture_data,
                global_state_data=global_state_data
            )
            spinner_running = False
            spinner_thread.join()
            sys.stdout.write("\r" + " "*60 + "\r✅ AI response received!\n")
            
            print("\n=== AI RESPONSE ===")
            print(json.dumps(summary, indent=2))
            
            if args.save:
                print("\nSaving to database...")
                save_summary_to_db(args.run_id, summary)
            else:
                print("\n(Dry run: Use --save to write this to the database and update the frontend UI)")
                
        except Exception as e:
            spinner_running = False
            spinner_thread.join()
            sys.stdout.write("\r" + " "*60 + "\r❌ Request failed!\n")
            print(f"\n❌ AI Synthesis Failed: {e}")
    else:
        print("Run with --invoke to actually hit the LLM API.")

if __name__ == "__main__":
    main()
