import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.services.publishing.evidence_builder import EvidenceBuilder
from application.services.publishing.renderers.html_renderer import HtmlRenderer

def main():
    db_path = "data/app.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Run ID 2 (or 1)
    run_id = 2
    print(f"Building CanonicalModel for Run ID {run_id}...")
    try:
        builder = EvidenceBuilder(session)
        model = builder.build(run_id)
        
        # Verify system topology nodes and edges count
        nodes_count = len(model.layered_architecture.system_topology.get("nodes", [])) if model.layered_architecture else 0
        edges_count = len(model.layered_architecture.system_topology.get("edges", [])) if model.layered_architecture else 0
        print(f"CanonicalModel built successfully.")
        print(f"System Topology Nodes count: {nodes_count}")
        print(f"System Topology Edges count: {edges_count}")
        
        print("Rendering HTML report...")
        renderer = HtmlRenderer()
        html_content = renderer.render(model, run_id)
        
        output_file = "Master_Intelligence_Report_2_updated.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report successfully rendered and saved to '{output_file}'!")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
