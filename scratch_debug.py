import json
import os
from collections import defaultdict

run_id = 1
# Check which graph is legacy_chaos
for i in range(1, 10):
    p = f"data/graph_{i}.json"
    if os.path.exists(p):
        with open(p) as f:
            d = json.load(f)
            if any("legacy_chaos" in n.get("fqn","") for n in d.get("nodes", [])):
                run_id = i
                break

graph_path = f"data/graph_{run_id}.json"
with open(graph_path, "r") as f:
    graph = json.load(f)
    
nodes = graph.get("nodes", [])
edges = graph.get("edges", [])

def get_context(fqn):
    if not fqn: return "Global"
    base_fqn = fqn.split("::")[0]
    if "\\" in base_fqn:
        parts = base_fqn.split("\\")
        return parts[0] if parts[0] else "Global"
    elif "/" in base_fqn:
        parts = base_fqn.strip("/").split("/")
        if len(parts) >= 2:
            return parts[-2]
    return "Global"

node_to_context = {}
for n in nodes:
    fqn = n.get("fqn", "")
    if "vendor" in fqn.lower() or "plugin" in fqn.lower(): continue
    ctx = get_context(fqn)
    node_to_context[n["id"]] = ctx
    print(f"Node: {n.get('name')}, Type: {n.get('type')}, FQN: {fqn}, Context: {ctx}")

internal = 0
external = 0
missing = 0
for e in edges:
    src_ctx = node_to_context.get(e["source_id"])
    tgt_ctx = node_to_context.get(e["target_id"])
    if src_ctx and tgt_ctx:
        if src_ctx == tgt_ctx: internal += 1
        else: external += 1
    else:
        missing += 1
        print(f"Missing context: src={src_ctx}, tgt={tgt_ctx} for edge {e['source_id']} -> {e['target_id']}")

print(f"Total Internal: {internal}, External: {external}, Missing: {missing}")
