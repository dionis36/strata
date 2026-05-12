import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.database import Base
from application.services.analysis_service import AnalysisService
from infrastructure.persistence.repositories import ProjectRepository, LegacyRepository

# Setup in-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

def test_legacy_chaos():
    project_path = os.path.abspath("tests/fixtures/legacy_chaos")
    project_repo = ProjectRepository(db)
    project = project_repo.get_or_create("Legacy Chaos Test")
    
    service = AnalysisService(db)
    print(f"--- Running Analysis on {project_path} ---")
    result = service.run_analysis(project.id, project_path)
    
    print("\n--- Analysis Result Summary ---")
    print(f"Run ID: {result['run_id']}")
    print(f"Files Found: {result['files']}")
    print(f"Classes Found: {result['classes']}")
    print(f"Edges Found: {result['edges']}")
    
    legacy_insights = result.get('legacy_insights', {})
    print("\n--- Legacy Insights (Requirement 1, 8, 9) ---")
    print(f"Era: {legacy_insights.get('php_era')}")
    print(f"Framework: {legacy_insights.get('detected_framework')}")
    print(f"DB Layer: {legacy_insights.get('db_layer')}")
    print(f"Auth Layer: {legacy_insights.get('auth_layer')}")
    print(f"Template Layer: {legacy_insights.get('template_layer')}")
    print(f"Modernization Score: {legacy_insights.get('total_modernization_score')}")
    
    # Check DB for Legacy Metrics
    legacy_repo = LegacyRepository(db)
    metrics = legacy_repo.get_legacy_metrics(result['run_id'])
    
    if metrics:
        print(f"Persisted Era: {metrics.php_era}")
        print(f"Security Score: {metrics.security_score}")
    else:
        print("Error: Legacy metrics not persisted!")

    # Basic assertions
    assert result['files'] >= 5, f"Expected at least 5 files, got {result['files']}"
    # In legacy chaos, we don't have classes, mostly procedural.
    
    print("\n✅ Legacy Extraction Test Completed Successfully!")

if __name__ == "__main__":
    try:
        test_legacy_chaos()
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
