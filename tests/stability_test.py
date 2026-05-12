import hashlib
import json
import os
from application.services.analysis_service import AnalysisService
from infrastructure.persistence.database import SessionLocal

def calculate_json_hash(json_data):
    # Sort keys for deterministic JSON hashing
    encoded = json.dumps(json_data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

def test_determinism(project_path="/data/OWASPWebGoatPHP-master/app/model", iterations=5):
    """
    Module D.2: Verification of Determinism.
    Ensures that multiple runs on the same codebase yield identical results.
    """
    print(f"🔬 Starting Determinism Stress Test on REAL CODE ({iterations} iterations)...")
    db = SessionLocal()
    service = AnalysisService(db)
    
    past_hash = None
    
    for i in range(iterations):
        print(f"  - Iteration {i+1}...")
        res = service.run_analysis(1, project_path)
        run_id = res["run_id"]
        
        # Load the generated graph JSON
        graph_path = f"/data/graph_{run_id}.json"
        with open(graph_path, "r") as f:
            graph_data = json.load(f)
            
        current_hash = calculate_json_hash(graph_data)
        
        if past_hash and current_hash != past_hash:
            print(f"❌ **DETERMINISM FAILED** at iteration {i+1}. Signatures do not match.")
            return False
            
        past_hash = current_hash
        
    print(f"✅ **DETERMINISM VERIFIED**: All {iterations} runs on WebGoat produced bit-identical topological signatures.")
    return True

if __name__ == "__main__":
    test_determinism()
