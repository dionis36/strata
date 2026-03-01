import networkx as nx
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from domain.models.edge import EdgeType
from domain.models.node import NodeType

# Performance constraints
MAX_NODES_FOR_BETWEENNESS = 2000
DEFAULT_TIMEOUT_SECONDS = 60


class MetricCalculator:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.total_nodes = max(graph.number_of_nodes(), 1)

    # ─────────────────────────────────────────────────────────────────────
    # Phase C: Subgraph Projection
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def project(
        graph: nx.DiGraph,
        node_types: Optional[List[NodeType]] = None,
        edge_types: Optional[List[EdgeType]] = None
    ) -> nx.DiGraph:
        """Return a subgraph filtered by node type and/or edge type.

        Arguments:
            graph: The full NetworkX DiGraph.
            node_types: If provided, only nodes whose 'type' attribute matches
                        one of the listed NodeType values are included.
            edge_types: If provided, only edges whose 'type' attribute matches
                        one of the listed EdgeType values are included.

        Returns:
            A new DiGraph containing only the matching nodes and edges.
        """
        edge_type_values = (
            {et.value for et in edge_types} if edge_types else None
        )
        node_type_values = (
            {nt.value for nt in node_types} if node_types else None
        )

        # Filter nodes first
        if node_type_values:
            keep_nodes = [
                n for n, d in graph.nodes(data=True)
                if d.get('type') in node_type_values
            ]
        else:
            keep_nodes = list(graph.nodes())

        # Build subgraph on kept nodes
        sub = graph.subgraph(keep_nodes).copy()

        # Filter edges by type if requested
        if edge_type_values:
            edges_to_remove = [
                (u, v) for u, v, d in sub.edges(data=True)
                if d.get('type') not in edge_type_values
            ]
            sub.remove_edges_from(edges_to_remove)

        return sub

    # ─────────────────────────────────────────────────────────────────────
    # Metric Computation
    # ─────────────────────────────────────────────────────────────────────

    def calculate_all_metrics(
        self,
        timeout: int = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, dict]:
        """Runs all mathematical metrics deterministically.

        Args:
            timeout: Max seconds to allow; raises RuntimeError if exceeded.
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._compute)
            try:
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                raise RuntimeError(
                    f"Metric computation exceeded {timeout}s timeout. "
                    "Graph may be too large. Consider reducing scope."
                )

    def _compute(self) -> Dict[str, dict]:
        nodes = list(self.graph.nodes())
        metrics_store = {n: {} for n in nodes}

        # 1. Degree Metrics
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        weighted_in = dict(self.graph.in_degree(weight='weight'))
        weighted_out = dict(self.graph.out_degree(weight='weight'))

        # 2. Betweenness Centrality — skip if graph is too large
        if self.graph.number_of_nodes() <= MAX_NODES_FOR_BETWEENNESS:
            betweenness = nx.betweenness_centrality(
                self.graph, normalized=True, weight=None
            )
        else:
            betweenness = {n: -1.0 for n in nodes}  # Signal: skipped

        closeness = nx.closeness_centrality(self.graph)

        # 3. SCC Clusters
        sccs = list(nx.strongly_connected_components(self.graph))
        scc_map = {}
        for scc_id, component in enumerate(sorted(sccs, key=lambda s: min(s))):
            scc_size = len(component)
            for node in component:
                scc_map[node] = {"id": scc_id, "size": scc_size}

        # 4. Blast Radius (Reachability via directed DFS)
        for node in nodes:
            reachable = len(nx.descendants(self.graph, node))
            metrics_store[node]['blast_radius'] = reachable
            metrics_store[node]['reachability_ratio'] = reachable / self.total_nodes

        # 5. Compile the Matrix
        for node in nodes:
            metrics_store[node]['in_degree'] = in_degrees.get(node, 0)
            metrics_store[node]['out_degree'] = out_degrees.get(node, 0)
            metrics_store[node]['total_degree'] = (
                in_degrees.get(node, 0) + out_degrees.get(node, 0)
            )
            metrics_store[node]['weighted_in'] = weighted_in.get(node, 0)
            metrics_store[node]['weighted_out'] = weighted_out.get(node, 0)
            metrics_store[node]['betweenness'] = betweenness.get(node, 0.0)
            metrics_store[node]['closeness'] = closeness.get(node, 0.0)
            metrics_store[node]['scc_id'] = scc_map[node]['id']
            metrics_store[node]['scc_size'] = scc_map[node]['size']
            metrics_store[node]['fan_in_ratio'] = in_degrees.get(node, 0) / self.total_nodes
            metrics_store[node]['fan_out_ratio'] = out_degrees.get(node, 0) / self.total_nodes
            metrics_store[node]['scc_density'] = scc_map[node]['size'] / self.total_nodes

        return metrics_store
