import sys
import os
import json

# Add project root to path
sys.path.append("/home/dio/Documents/strata")

from application.services.advisory_service import AdvisoryService

service = AdvisoryService(data_dir="/home/dio/Documents/strata/data")
run_id = 1 # Assuming WebGoat is Run 1 based on previous curls

print(f"Testing Strategic Advisory for Run {run_id}...")
try:
    roadmap = service.get_strategic_roadmap(run_id)
    print(f"KPIs: {json.dumps(roadmap['kpis'], indent=2)}")
    print(f"Number of recommendations: {len(roadmap['recommendations'])}")
    for r in roadmap['recommendations']:
        print(f" - Context: {r['Context']}, Strategy: {r['Recommended Strategy']}, ROI: {r['Modernization ROI']}")
except Exception as e:
    print(f"Error: {e}")
