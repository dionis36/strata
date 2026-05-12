import sys
import argparse
import requests
import json
import time

def main():
    parser = argparse.ArgumentParser(description="Strata CLI: Enterprise Modernization Intelligence")
    parser.add_argument("--path", required=True, help="Path to the monolith source code")
    parser.add_argument("--name", default="cli_project", help="Name of the project")
    parser.add_argument("--api", default="http://localhost:8000", help="Strata API URL")
    
    args = parser.parse_args()
    
    print(f"🚀 Initializing Strata Analysis for: {args.path}")
    
    try:
        # 1. Trigger Analysis
        payload = {"project_path": args.path, "project_name": args.name}
        res = requests.post(f"{args.api}/analyze", json=payload)
        res.raise_for_status()
        run_data = res.json()
        run_id = run_data["run_id"]
        
        print(f"✅ Analysis Started (Run ID: {run_id})")
        
        # 2. Poll for results (Simplified for CLI)
        # In a more advanced CLI, we'd wait for completion. 
        # For now, we'll fetch the risk summary immediately.
        time.sleep(2) # Give it a moment to stabilize
        
        risk_res = requests.get(f"{args.api}/risk/{run_id}")
        if risk_res.status_code == 200:
            data = risk_res.json()
            print("\n📊 Modernization Risk Summary:")
            print(f"- Total Components: {len(data['components'])}")
            
            # Show top 5 high risk components
            high_risk = sorted(data['components'], key=lambda x: x['final_risk'], reverse=True)[:5]
            for c in high_risk:
                print(f"  [!] {c['name']} - Risk: {c['final_risk']:.2f} ({c['risk_level']})")
                
        print(f"\n✨ Analysis complete. View full Topological Manifest at: {args.api.replace('8000', '8501')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
