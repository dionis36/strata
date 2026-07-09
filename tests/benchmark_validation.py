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
            "expected_safe_units": [
                "jFormInputEmail",
                "jFormInputDate",
                "webgoat\\ContestUsers",
                "webgoat\\WorkshopUsers"
            ],
            "expected_blocked_units": [
                "User",
                "UserRepository",
                "Xuser",
                "webgoat\\BaseLesson",
                "jFormCaptcha"
            ]
        }
    }
    
    print(" Initializing Strata Accuracy Benchmark...")
    results = {}
    
    for project_path, targets in ground_truth.items():
        print(f"\n Benchmarking Project: {project_path}")
        
        # 1. Run Analysis
        res = analysis_service.run_analysis(1, project_path)
        run_id = res["run_id"]
        
        # 2. Get Extraction Candidates
        candidates = extraction_service.analyze_extraction(run_id)
        
        # 3. Calculate Metrics
        tp = 0
        fp = 0
        fn = 0
        tn = 0
        
        for c in candidates:
            # Safely handle Enum comparison
            rec_val = c["recommendation"].value if hasattr(c["recommendation"], "value") else c["recommendation"]
            
            # Extract all FQNs and names present in this candidate
            candidate_names = set()
            for detail in c.get("node_details", []):
                if detail.get("fqn"):
                    candidate_names.add(detail["fqn"])
                if detail.get("name"):
                    candidate_names.add(detail["name"])
                    
            # Check if this candidate contains any expected safe unit
            has_safe = any(u in candidate_names for u in targets["expected_safe_units"])
            # Check if this candidate contains any expected blocked unit
            has_blocked = any(u in candidate_names for u in targets["expected_blocked_units"])
            
            if has_safe:
                # SAFE_TO_EXTRACT and EXTRACT_WITH_CAUTION are extractable categories
                if rec_val in ["SAFE_TO_EXTRACT", "EXTRACT_WITH_CAUTION"]:
                    tp += 1
                elif rec_val in ["DO_NOT_EXTRACT", "REQUIRES_REFACTOR_FIRST"]:
                    fn += 1
                    
            if has_blocked:
                if rec_val in ["SAFE_TO_EXTRACT", "EXTRACT_WITH_CAUTION"]:
                    fp += 1
                elif rec_val in ["DO_NOT_EXTRACT", "REQUIRES_REFACTOR_FIRST"]:
                    tn += 1
                    
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print(f"  True Positives (TP): {tp}")
        print(f"  False Positives (FP): {fp}")
        print(f"  False Negatives (FN): {fn}")
        print(f"  True Negatives (TN): {tn}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1-Score: {f1:.3f}")
        
        results[project_path] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
        
        if f1 >= 0.80:
            print(" **BENCHMARK SUCCESS**: Intelligence Engine is generating modernization candidates with high accuracy.")
        else:
            print(" **BENCHMARK WARNING**: Accuracy metrics are below expectations. Review topological density.")
            
    return results

if __name__ == "__main__":
    run_benchmark()

