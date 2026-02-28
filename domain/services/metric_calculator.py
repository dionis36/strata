import networkx as nx
from typing import Dict, Any

class MetricCalculator:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.total_nodes = max(graph.number_of_nodes(), 1)  # Prevent div-by-zero

    def calculate_all_metrics(self) -> Dict[str, dict]:
        """Runs all mathematical metrics deterministically over the entire graph."""
        nodes = list(self.graph.nodes())
        
        # In-Memory dict to hold all node metrics keyed by node_id
        metrics_store = {n: {} for n in nodes}

        # 1. Degree Metrics
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        weighted_in = dict(self.graph.in_degree(weight='weight'))
        weighted_out = dict(self.graph.out_degree(weight='weight'))

        # 2. Centrality (Deterministic shortest path execution)
        # Using weight=None configures Betweenness to treat all paths equally in terms of distance step logic, 
        # which focuses strictly on topological architecture chokepoints.
        betweenness = nx.betweenness_centrality(self.graph, normalized=True, weight=None)
        closeness = nx.closeness_centrality(self.graph)

        # 3. SCC Clusters
        sccs = list(nx.strongly_connected_components(self.graph))
        scc_map = {}
        for scc_id, component in enumerate(sccs):
            scc_size = len(component)
            for node in component:
                scc_map[node] = {"id": scc_id, "size": scc_size}

        # 4. Blast Radius (Reachability via directed DFS)
        # Precompute blast radius efficiently
        for node in nodes:
            reachable = len(nx.descendants(self.graph, node))
            metrics_store[node]['blast_radius'] = reachable
            metrics_store[node]['reachability_ratio'] = reachable / self.total_nodes

        # 5. Compile the Matrix
        for node in nodes:
            metrics_store[node]['in_degree'] = in_degrees.get(node, 0)
            metrics_store[node]['out_degree'] = out_degrees.get(node, 0)
            metrics_store[node]['total_degree'] = in_degrees.get(node, 0) + out_degrees.get(node, 0)
            metrics_store[node]['weighted_in'] = weighted_in.get(node, 0)
            metrics_store[node]['weighted_out'] = weighted_out.get(node, 0)

            metrics_store[node]['betweenness'] = betweenness.get(node, 0.0)
            metrics_store[node]['closeness'] = closeness.get(node, 0.0)

            metrics_store[node]['scc_id'] = scc_map[node]['id']
            metrics_store[node]['scc_size'] = scc_map[node]['size']

            # Derived Ratios
            metrics_store[node]['fan_in_ratio'] = in_degrees.get(node, 0) / self.total_nodes
            metrics_store[node]['fan_out_ratio'] = out_degrees.get(node, 0) / self.total_nodes
            metrics_store[node]['scc_density'] = scc_map[node]['size'] / self.total_nodes

        return metrics_store
