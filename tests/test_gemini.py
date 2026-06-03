import os
import sys

# Set up path to import from application
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from application.services.publishing.ai_advisory_service import AIAdvisoryService

class DummyCtx:
    project_name = "Strata Analysis"
    total_files = 1500
    lines_of_code = 120000
    framework = "Custom Legacy"
    php_era = "PHP 5.6"
    overall_readiness = 25.0
    architectural_footprint = {
        "Models": 50,
        "Controllers": 30,
        "Views": 200
    }

class DummyLegacy:
    version_score = 3.0
    namespace_score = 4.0
    db_layer_score = 2.0
    security_score = 5.0
    testability_score = 1.0
    coupling_score = 2.0

def test():
    service = AIAdvisoryService()
    print(f"API Key present: {bool(service.gemini_key or service.openrouter_key)}")
    ctx = DummyCtx()
    legacy = DummyLegacy()
    
    try:
        print("Invoking Gemini...")
        summary = service.synthesize_executive_summary(ctx, legacy)
        print("Success!")
        print(summary)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test()
