#!/usr/bin/env python3
"""
run_comparison.py

Universal interactive validator for Strata vs PhpMetrics.
This script bridges the output of `generate_phpmetrics.py` with Strata's analysis runs.

Usage:
    python3 evaluation/runners/run_comparison.py
"""
import json
import os
import sqlite3
import sys

# Paths
# Resolves to /home/dio/Documents/strata
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_DIR = os.path.join(BASE_DIR, "AUDIT")
DB_PATH = os.path.join(BASE_DIR, "data", "app.db")

TOLERANCE = 5.0

def check(label, strata_val, pm_val, tolerance=TOLERANCE, unit=""):
    try:
        s = float(strata_val or 0)
        p = float(pm_val or 0)
        if p == 0:
            diff = 0.0 if s == 0 else float("inf")
        else:
            diff = abs(s - p) / abs(p) * 100
    except (TypeError, ValueError):
        diff = float("inf")

    if diff <= tolerance:
        status, icon = "PASS", "✅"
    elif diff <= 20:
        status, icon = "WARN", "⚠️ "
    else:
        status, icon = "FAIL", "❌"

    res = f"  {icon} [{status}] {label:<38} Strata={strata_val!r:<10} PhpMetrics={pm_val!r:<10} Δ={diff:.1f}%{unit}"
    print(res)
    return status, diff, res

def get_strata_data(run_id):
    """Fetch aggregated metrics and component metrics from SQLite for a specific run_id."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM analysis_run WHERE id = ?", (run_id,))
    run = cursor.fetchone()
    if not run:
        conn.close()
        return None

    run_dict = dict(run)
    summary = {
        "run_id": run_id,
        "total_files": run_dict.get("total_files") or 0,
        "total_loc": run_dict.get("total_loc") or 0,
        "total_classes": run_dict.get("total_classes") or 0,
        "total_methods": run_dict.get("total_methods") or 0,
        "avg_complexity": round(run_dict.get("avg_complexity") or 0, 4),
        "avg_maintainability": round(run_dict.get("avg_maintainability") or 0, 4),
    }

    cursor.execute("SELECT * FROM component_metrics WHERE run_id = ?", (run_id,))
    components = []
    for row in cursor.fetchall():
        m = dict(row)
        components.append({
            "name": m.get("component_name"),
            "type": m.get("component_type"),
            "in_degree": m.get("in_degree", 0),
            "out_degree": m.get("out_degree", 0),
            "wmc": m.get("wmc", 0),
            "lcom": round(m.get("lcom") or 0, 6),
        })

    conn.close()
    return {"summary": summary, "components": components}

def get_phpmetrics_baselines():
    if not os.path.exists(AUDIT_DIR):
        return []
    return [d for d in os.listdir(AUDIT_DIR) 
            if os.path.isdir(os.path.join(AUDIT_DIR, d)) and d.startswith("phpmetrics_")]

def main():
    print("=" * 60)
    print("  STRATA × PHPMETRICS INTERACTIVE VALIDATOR")
    print("=" * 60)
    
    baselines = get_phpmetrics_baselines()
    if not baselines:
        print("\nNo PhpMetrics baselines found in /AUDIT.")
        print("Run `python3 evaluation/runners/generate_phpmetrics.py` first.")
        return

    print("\nAvailable PhpMetrics Baselines:")
    for i, b in enumerate(baselines, 1):
        print(f"  [{i}] {b}")

    choice = int(input("\nSelect a baseline by number: "))
    if choice < 1 or choice > len(baselines):
        print("Invalid selection.")
        return

    selected_baseline = baselines[choice - 1]
    pm_json_path = os.path.join(AUDIT_DIR, selected_baseline, "report.json")
    
    if not os.path.exists(pm_json_path):
        print(f"\nERROR: report.json not found in {selected_baseline}")
        return

    run_id = int(input("\nEnter the Strata Run ID to validate against (e.g., 1): "))

    print(f"\n[+] Loading Strata Data for Run ID: {run_id}...")
    strata = get_strata_data(run_id)
    if not strata:
        print(f"ERROR: Run ID {run_id} not found in the Strata database.")
        return

    print(f"[+] Loading PhpMetrics Data from: {pm_json_path}...")
    with open(pm_json_path) as f:
        pm = json.load(f)

    # Begin Comparison
    s_sum = strata["summary"]

    print("\n" + "=" * 80)
    print("  STRATA × PhpMetrics — DEEP VALIDATION REPORT")
    print("=" * 80)

    print("\n[1] PROJECT-LEVEL KPIs (Global Metrics)\n")
    
    pm_classes = []
    pm_map = {}
    for key, val in pm.items():
        if isinstance(val, dict) and val.get("_type") == "Hal\\Metric\\ClassMetric":
            pm_classes.append(val)
            cname = val.get("name", "")
            pm_map[cname.split("\\")[-1]] = val
            pm_map[cname] = val

    pm_loc = sum(c.get("loc", 0) for c in pm_classes)
    pm_nb_classes = len(pm_classes)
    pm_methods = sum(c.get("nbMethods", 0) for c in pm_classes)
    pm_cc = sum(c.get("ccn", 0) for c in pm_classes) / pm_nb_classes if pm_nb_classes else 0
    pm_mi = sum(c.get("mi", 0) for c in pm_classes) / pm_nb_classes if pm_nb_classes else 0

    check("Total LOC (Class sum)", s_sum["total_loc"], pm_loc, tolerance=25)
    check("Total Classes", s_sum["total_classes"], pm_nb_classes, tolerance=10)
    check("Total Methods", s_sum["total_methods"], pm_methods, tolerance=15)
    check("Avg Cyclomatic Complexity", round(s_sum["avg_complexity"],2), round(float(pm_cc), 2), tolerance=20)
    check("Avg Maintainability Index", round(s_sum["avg_maintainability"],2), round(float(pm_mi),2), tolerance=20)

    print("\n[2] IDENTIFIED SHORTCOMINGS & DIFFERENCES\n")

    matched = 0
    shortcomings = {
        "missing_in_strata": [],
        "wmc_diff": [],
        "lcom_diff": [],
        "coupling_diff": []
    }

    pm_names = set(pm_map.keys())
    strata_names = set([c["name"].split("\\")[-1] for c in strata["components"] if str(c.get("type")).lower() == "class"])
    
    for cname in pm_names:
        if "\\" not in cname and cname not in strata_names:
            if "Exception" not in cname: 
                shortcomings["missing_in_strata"].append(cname)

    for comp in strata["components"]:
        if str(comp.get("type", "")).lower() not in ("class",):
            continue
        fqn = comp["name"]
        short = fqn.split("\\")[-1]

        pm_comp = pm_map.get(fqn) or pm_map.get(short)
        if not pm_comp:
            continue

        matched += 1
        
        pm_wmc = pm_comp.get("wmc", pm_comp.get("weightedMethodsPerClass", 0))
        pm_lcom = pm_comp.get("lcom", 0)
        pm_ca = pm_comp.get("afferentCoupling", pm_comp.get("ca", 0))
        pm_ce = pm_comp.get("efferentCoupling", pm_comp.get("ce", 0))

        s_wmc, s_lcom = comp.get("wmc", 0), round(comp.get("lcom", 0), 3)
        s_ca, s_ce = comp.get("in_degree", 0), comp.get("out_degree", 0)
            
        if s_wmc != pm_wmc and pm_wmc > 0:
            if abs(s_wmc - pm_wmc)/pm_wmc > 0.2:
                shortcomings["wmc_diff"].append((short, s_wmc, pm_wmc))
                
        if abs(s_lcom - float(pm_lcom)) > 0.3:
            shortcomings["lcom_diff"].append((short, s_lcom, pm_lcom))

        if abs(s_ca - pm_ca) > 2 or abs(s_ce - pm_ce) > 2:
            shortcomings["coupling_diff"].append((short, f"In:{s_ca}/{pm_ca}", f"Out:{s_ce}/{pm_ce}"))

    print(f"Matched {matched} total classes for comparison.")

    print("\n>> 2.1 Unparsed or Missing Classes")
    if shortcomings["missing_in_strata"]:
        print(f"PhpMetrics found {len(shortcomings['missing_in_strata'])} classes that Strata missed.")
        print(f"Sample: {shortcomings['missing_in_strata'][:10]}")
    else:
        print("Excellent! Strata found all classes PhpMetrics found.")

    print("\n>> 2.2 WMC (Weighted Method Complexity) Divergence")
    if shortcomings["wmc_diff"]:
        print(f"{len(shortcomings['wmc_diff'])} classes have >20% WMC deviation.")
        print(f"Sample: {shortcomings['wmc_diff'][:5]}")
    else:
        print("WMC aligns closely.")

    print("\n>> 2.3 LCOM (Cohesion) Divergence")
    if shortcomings["lcom_diff"]:
        print(f"{len(shortcomings['lcom_diff'])} classes have a large LCOM delta (>0.3).")
        print(f"Sample: {shortcomings['lcom_diff'][:5]}")
    else:
        print("LCOM aligns closely.")

    print("\n>> 2.4 Coupling Divergence (In/Out Degree vs Ca/Ce)")
    if shortcomings["coupling_diff"]:
        print(f"{len(shortcomings['coupling_diff'])} classes have coupling mismatches.")
        print(f"Sample: {shortcomings['coupling_diff'][:5]}")
    else:
        print("Coupling aligns closely.")

    print("\n" + "=" * 80)
    print("  [CONCLUSION]")
    print("=" * 80)
    print("Deviations are expected: Strata uses Henderson-Sellers LCOM and measures dynamic ")
    print("runtime coupling (Injections/Instantiations) rather than purely static imports.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user. Exiting cleanly...")
        sys.exit(0)
    except ValueError:
        print("\n[!] Please enter a valid number.")
        sys.exit(1)
