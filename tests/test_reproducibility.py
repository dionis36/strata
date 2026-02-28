import urllib.request
import json
import time

url_analyze = "http://localhost:8000/analyze"
url_metrics = "http://localhost:8000/metrics/"
payload = json.dumps({"project_path": "/data/test_project_2", "project_name": "mvc_test"}).encode('utf-8')

results = []
print("Starting 5x reproducibility constraint test...")

for i in range(5):
    print(f"Executing Run {i+1}/5...")
    
    # 1. Analyze
    req = urllib.request.Request(url_analyze, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Analyze failed: {e}")
        exit(1)
        
    run_id = res_data["run_id"]
    
    # 2. Get Metrics
    req_m = urllib.request.Request(url_metrics + str(run_id))
    try:
        with urllib.request.urlopen(req_m) as response:
            met_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Metrics fetch failed: {e}")
        exit(1)
        
    metrics = met_data["components"]
    results.append(metrics)

# Validate Determinism
base = results[0]
for i in range(1, 5):
    if json.dumps(base, sort_keys=True) != json.dumps(results[i], sort_keys=True):
        print(f"💥 FATAL: Mismatch found at run {i+1}!")
        print("Run 1 Output:", json.dumps(base, indent=2))
        print(f"Run {i+1} Output:", json.dumps(results[i], indent=2))
        exit(1)

print("\nSUCCESS: All 5 runs yielded mathematically IDENTICAL structural intelligence metrics.")
print("The Centrality graph ordering is stable. You have achieved Genius-Level validation!")
