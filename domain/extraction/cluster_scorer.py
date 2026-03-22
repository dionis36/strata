import networkx as nx
from collections import defaultdict
from domain.extraction.extraction_model import ExtractionUnit
from domain.models.node import NodeType
from domain.models.edge import EdgeType


class ClusterScorer:
    """
    Evaluates the structural and behavioral quality of a candidate cluster.
    Implements the Option B scoring formula.
    """
    def __init__(self, nx_graph: nx.DiGraph):
        self.G = nx_graph
        self.class_nodes = set(
            n for n, d in self.G.nodes(data=True) 
            if d.get("type") == NodeType.CLASS.value
        )

    def score_cluster(self, unit: ExtractionUnit) -> float:
        nodes = set(unit.nodes)
        if not nodes:
            return 0.0

        internal_edges = 0
        external_edges = 0
        boundary_edges = 0
        table_writes = defaultdict(int)

        for u in nodes:
            # Outbound edges
            for v in self.G.successors(u):
                edge_data = self.G.edges[u, v]
                if edge_data.get("type") == EdgeType.WRITES.value:
                    table_writes[v] += 1
                elif v in nodes:
                    internal_edges += 1
                elif v in self.class_nodes:
                    external_edges += 1
                    boundary_edges += 1
            
            # Inbound edges
            for v in self.G.predecessors(u):
                if v in self.class_nodes and v not in nodes:
                    external_edges += 1
                    boundary_edges += 1

        total_cluster_edges = internal_edges + external_edges

        # 1. Cohesion (Internal Density)
        cohesion = internal_edges / total_cluster_edges if total_cluster_edges > 0 else 0.0

        # 2. Coupling Penalty (Normalized to 1.0 = highly coupled)
        # Assuming ~10 external edges is the threshold for max coupling penalty
        coupling = min(1.0, external_edges / 10.0)

        # 3. Size Balance (Optimal size: 2 to 8 nodes)
        size = len(nodes)
        if 2 <= size <= 8:
            size_score = 1.0
        else:
            size_score = max(0.0, 1.0 - abs(size - 5) / 10.0)

        # 4. Behavioral Coherence
        max_table_writers = max(table_writes.values()) if table_writes else 0
        behavioral_coherence = max_table_writers / size

        # 5. Structural Isolation
        boundary_ratio = min(1.0, boundary_edges / internal_edges) if internal_edges > 0 else 1.0

        score = (
            0.35 * cohesion +
            0.20 * (1.0 - coupling) +
            0.15 * size_score +
            0.15 * behavioral_coherence +
            0.15 * (1.0 - boundary_ratio)
        )

        unit.score = round(score, 3)
        return unit.score
