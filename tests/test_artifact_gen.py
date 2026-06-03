from infrastructure.persistence.database import SessionLocal
from application.services.artifact_service import ArtifactService

db = SessionLocal()
service = ArtifactService(db)
# Find the latest run_id
from infrastructure.persistence.models import AnalysisRun
run = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).first()

if run:
    print(f"Found Run ID: {run.id}. Generating bundle...")
    try:
        bundle_bytes = service.generate_workspace_bundle(run.id)
        with open("test_bundle.zip", "wb") as f:
            f.write(bundle_bytes)
        print("Success! Wrote test_bundle.zip")
    except Exception as e:
        import traceback
        print("Failed to generate bundle:")
        traceback.print_exc()
else:
    print("No runs found in the database to test with.")
