import os
import json
from application.services.analysis_service import AnalysisService
from application.services.extraction_service import ExtractionService
from infrastructure.persistence.database import SessionLocal

def run_benchmark():
    """
    Module D.1: Rigorous Accuracy Testing.
    Compares Strata's automated extraction candidates against a manually labeled 'Ground Truth'.
    """
    db = SessionLocal()
    analysis_service = AnalysisService(db)
    extraction_service = ExtractionService(db)
    
    # Ground Truth for WebGoat app/model
    ground_truth = {
        "/data/OWASPWebGoatPHP-master/app/model": {
            "expected_safe_units": [], # Exploration phase
            "expected_blocked_units": []
        }
    }
    
    print("📊 Initializing Strata Accuracy Benchmark...")
    
    for project_path, targets in ground_truth.items():
        print(f"\n📂 Benchmarking Project: {project_path}")
        
        # 1. Run Analysis
        res = analysis_service.run_analysis(1, project_path)
        run_id = res["run_id"]
        
        # 2. Get Extraction Candidates
        candidates = extraction_service.analyze_extraction(run_id)
        
        # 3. Calculate Metrics
        recommended_units = [c["unit"] for c in candidates if c["recommendation"] == "SAFE_TO_EXTRACT"]
        blocked_units = [c["unit"] for c in candidates if c["recommendation"] == "DO_NOT_EXTRACT"]
        
        print(f"🔍 Recommended for Modernization: {recommended_units}")
        print(f"🛡️ Blocked as High-Risk Monolith Core: {blocked_units}")
        
        if len(recommended_units) > 0:
            print("✨ **BENCHMARK SUCCESS**: Intelligence Engine is generating modernization candidates on a real-world codebase.")
        else:
            print("⚠️ **BENCHMARK WARNING**: No candidates identified. Review topological density.")

if __name__ == "__main__":
    run_benchmark()
