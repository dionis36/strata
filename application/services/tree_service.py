from sqlalchemy.orm import Session
from infrastructure.persistence.models import ComponentDependency, ComponentMetric

class TreeService:
    def __init__(self, db: Session):
        self.db = db

    def get_bootstrap_analysis(self, run_id: int) -> dict:
        edges = self.db.query(ComponentDependency).filter(ComponentDependency.run_id == run_id).all()
        
        # 1. Identify File-to-File Includes
        # An include is when both source and target are FILES.
        adjacency = {}
        in_degrees = {}
        all_files = set()
        
        for e in edges:
            src = e.source_id.split("::")[-1] if "::" in e.source_id else e.source_id.split("/")[-1].split("\\")[-1]
            tgt = e.target_id.split("::")[-1] if "::" in e.target_id else e.target_id.split("/")[-1].split("\\")[-1]
            
            # Crude but effective heuristic: if it has .php, it's a file
            if ".php" in src and ".php" in tgt:
                if src not in adjacency: adjacency[src] = []
                adjacency[src].append(tgt)
                
                if tgt not in in_degrees: in_degrees[tgt] = 0
                in_degrees[tgt] += 1
                
                if src not in in_degrees: in_degrees[src] = 0
                
                all_files.add(src)
                all_files.add(tgt)
        
        # 2. Dead Includes (Orphaned Files)
        # Files that have in_degree == 0, and aren't typical entry points
        dead_includes = []
        entry_points = ['index.php', 'main.php', 'app.php', 'bootstrap.php']
        for f in all_files:
            if in_degrees.get(f, 0) == 0 and not any(f.endswith(ep) for ep in entry_points):
                dead_includes.append(f)
                
        # 3. Circular Includes
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    # To prevent duplicate cycles of the same nodes in different orders
                    if sorted(cycle_path) not in [sorted(c) for c in cycles]:
                        cycles.append(cycle_path)
            
            rec_stack.remove(node)
            path.pop()

        for node in all_files:
            if node not in visited:
                dfs(node, [])
                
        return {
            "bootstrap_chain": adjacency,
            "dead_includes": dead_includes,
            "circular_includes": [" ➔ ".join(c) for c in cycles]
        }
