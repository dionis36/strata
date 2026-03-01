import urllib.request
import json

# ── Integration test: 5x reproducibility across the live API ──────────────
# This is intentionally a script-style test, not a unit test.
# Run it standalone: python3 tests/test_reproducibility.py
# Use pytest -k "not reproducibility" to exclude from pytest suite.

def run_reproducibility_check():
    url_analyze = "http://localhost:8000/analyze"
    url_metrics = "http://localhost:8000/metrics/"
    payload = json.dumps(
        {"project_path": "/data/test_project_2", "project_name": "mvc_test"}
    ).encode('utf-8')

    results = []
    print("Starting 5x reproducibility constraint test...")

    for i in range(5):
        print(f"Executing Run {i+1}/5...")
        req = urllib.request.Request(
            url_analyze, data=payload, headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode())
        except Exception as e:
            print(f"Analyze failed: {e}")
            return False

        run_id = res_data["run_id"]
        req_m = urllib.request.Request(url_metrics + str(run_id))
        try:
            with urllib.request.urlopen(req_m) as response:
                met_data = json.loads(response.read().decode())
        except Exception as e:
            print(f"Metrics fetch failed: {e}")
            return False

        metrics = met_data["components"]
        results.append(metrics)

    base = results[0]
    for i in range(1, 5):
        if json.dumps(base, sort_keys=True) != json.dumps(results[i], sort_keys=True):
            print(f"FATAL: Mismatch found at run {i+1}!")
            return False

    print("\nSUCCESS: All 5 runs yielded mathematically IDENTICAL structural intelligence metrics.")
    return True


if __name__ == "__main__":
    import sys
    ok = run_reproducibility_check()
    sys.exit(0 if ok else 1)
