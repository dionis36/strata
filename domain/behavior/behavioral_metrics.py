"""
Phase 4: Behavioral Metrics Calculator
Computes database mutation activity metrics from the graph's WRITES edges.
"""
from collections import defaultdict
from typing import List, Dict

from domain.models.graph_model import GraphModel
from domain.models.node import NodeType
from domain.models.edge import EdgeType

class BehavioralMetricsCalculator:
    def __init__(self, graph: GraphModel):
        self.graph = graph.graph


    def calculate_metrics(self) -> List[dict]:
        """Calculates behavioral metrics for all class nodes in the graph based on WRITES_TO edges."""
        results = []
        
        # 1. Map tables to the classes that write to them
        table_writers = defaultdict(set)
        for u, v, data in self.graph.edges(data=True):
            if data.get("type") == EdgeType.WRITES_TO.value:
                # u is class, v is table
                table_writers[v].add(u)

        # 2. Compute metrics per class
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == NodeType.CLASS.value:
                # Find all tables this class writes to
                written_tables = [
                    v for _, v, edge_data in self.graph.edges(node_id, data=True)
                    if edge_data.get("type") == EdgeType.WRITES_TO.value
                ]
                
                # We use simple count of WRITES edges. In future phases, 
                # write_intensity could sum edge weights (e.g. number of SQL queries).
                write_intensity = float(len(written_tables))
                table_dependencies = len(written_tables)
                
                # Shared table pressure: sum of writers referencing the same table
                # (A class pushing to a table that 10 other classes push to is under high shared pressure)
                shared_pressure = 0.0
                for table in written_tables:
                    # We subtract 1 so a table written ONLY by this class adds 0 shared pressure
                    shared_pressure += float(len(table_writers[table]) - 1)
                    
                results.append({
                    "component_name": data.get("fqn", node_id),
                    "write_intensity": write_intensity,
                    "table_dependencies": table_dependencies,
                    "shared_table_pressure": shared_pressure
                })

        return results
