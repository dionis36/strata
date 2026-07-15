import os
import sys
import json
from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import AnalysisRun
from application.services.artifact_service import ArtifactService

def main():
    db = SessionLocal()
    try:
        latest_run = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).first()
        if not latest_run:
            print("No analysis runs found.")
            sys.exit(1)
            
        print(f"Generating SARIF for run_id: {latest_run.id}")
        
        service = ArtifactService(db)
        sarif_data = service.generate_sarif(latest_run.id)
        
        output_path = "/home/dio/Documents/strata/results.sarif"
        with open(output_path, "w") as f:
            json.dump(sarif_data, f, indent=2)
            
        print(f"Successfully generated SARIF to {output_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
