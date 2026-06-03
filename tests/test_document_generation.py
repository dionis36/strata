import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application.services.publishing.document_generator import DocumentGenerator
from application.services.publishing.models import CanonicalModel, SystemContext, Finding, Evidence

def test_document_generator():
    print("Testing DocumentGenerator logic without hitting the LLM API...")
    
    # Mock SystemContext
    ctx = SystemContext(
        project_name="Test Monolith",
        framework="Custom PHP",
        php_era="Bespoke / Custom Era",
        total_files=7877,
        total_classes=5000,
        total_edges=25000,
        lines_of_code=1500000,
        avg_complexity=12.4,
        connectivity=15000,
        test_coverage="5.0%",
        overall_readiness=45.0
    )
    
    # Mock Findings
    f1 = Finding(
        id="1",
        component_name="core/GodClass.php",
        category="Architecture",
        observation="Massive God Class detected with 150 incoming dependencies.",
        impact="Changes to this class have a massive blast radius.",
        reasoning="LCOM is extremely high.",
        recommended_action="Decouple into separate domain services using the Strangler pattern.",
        priority="Critical",
        confidence="Confirmed",
        mermaid_diagram="graph TD;\n  A-->B;\n  A-->C;",
        evidence=[Evidence(type="file", target="core/GodClass.php", metric_name="in_degree", metric_value=150)]
    )
    
    # Mock Model
    class MockRun:
        ai_executive_summary_json = '{"current_state": "The system is a highly coupled monolith.", "critical_risks": "Database pressure is immense.", "strategic_roadmap": "1. Test\\n2. Decouple\\n3. Microservices"}'
        
    model = CanonicalModel(
        run_id=1,
        system_context=ctx,
        legacy_intelligence={},
        database_intelligence={},
        dependency_intelligence=[],
        global_state_intelligence={},
        strategic_advisory={},
        boundary_intelligence=None,
        legacy_posture=None,
        findings=[f1],
        full_risk_register=[f1]
    )
    
    generator = DocumentGenerator()
    md_content = generator.generate_technical_report(model)
    
    with open("test_output_report.md", "w") as f:
        f.write(md_content)
        
    print("SUCCESS: Document logic executed perfectly.")
    print("Output saved to 'test_output_report.md'")
    
def test_llm_connectivity():
    print("\nTesting LLM Connectivity (Checking API Tier Quota)...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("SKIP: GEMINI_API_KEY not found in environment.")
        return
        
    from google import genai
    client = genai.Client(api_key=api_key)
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Respond with exactly 'OK'"
        )
        print(f"LLM API SUCCESS: {res.text.strip()}")
    except Exception as e:
        print(f"LLM API FAILED: {e}")
        print("\nNOTE: The '429 RESOURCE_EXHAUSTED' error with 'GenerateRequestsPerDayPerProjectPerModel-FreeTier' means you have hit Google's hard daily limit (20 requests per day) for the newest gemini-2.5-flash model on the Free Tier.")

if __name__ == "__main__":
    test_document_generator()
    test_llm_connectivity()
