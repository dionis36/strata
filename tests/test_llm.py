import os
import sys
from sqlalchemy.orm import Session
from infrastructure.persistence.database import SessionLocal
from application.services.artifact_service import ArtifactService

def test_llm_report_generation():
    print("Testing LLM Pipeline and HTML generation...")
    db: Session = SessionLocal()
    try:
        # Assuming run_id 1 exists. Adjust as necessary.
        run_id = 1
        print(f"Generating human report for run_id={run_id}...")
        
        service = ArtifactService(db)
        html_report = service.generate_human_report(run_id)
        
        output_file = "test_executive_report.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_report)
            
        print(f"✅ Success! Report saved to {output_file}")
        print("Open this file in your browser to verify the Mermaid rendering and new Tailwind CSS layout.")
        
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure environment variables are loaded if using python directly instead of docker
    # Usually running inside docker: docker exec -it strata-api-1 python tests/test_llm.py
    test_llm_report_generation()
