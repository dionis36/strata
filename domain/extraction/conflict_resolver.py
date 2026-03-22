import networkx as nx
from typing import List
from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType
from domain.models.node import NodeType


class ConflictResolver:
    """
    Implements a greedy selection algorithm to choose the highest-scoring
    non-overlapping extraction clusters, and wraps remaining singleton nodes.
    """
    def __init__(self, nx_graph: nx.DiGraph):
        self.class_nodes = set(
            n for n, d in nx_graph.nodes(data=True) 
            if d.get("type") == NodeType.CLASS.value
        )

    def resolve(self, candidate_clusters: List[ExtractionUnit]) -> List[ExtractionUnit]:
        # 1. Sort clusters by quality score descending
        sorted_candidates = sorted(candidate_clusters, key=lambda c: c.score, reverse=True)
        
        selected_units = []
        used_nodes = set()
        
        # 2. Greedy selection for clusters
        for cluster in sorted_candidates:
            # If no node in this cluster has been claimed yet
            if not any(node in used_nodes for node in cluster.nodes):
                selected_units.append(cluster)
                used_nodes.update(cluster.nodes)
                
        # 3. Fallback to single-node extraction units for the remainder
        remaining_nodes = self.class_nodes - used_nodes
        single_units = []
        for node in remaining_nodes:
            short_name = node.split('\\')[-1]
            single_units.append(ExtractionUnit(
                label=f"{short_name}_Single",
                type=ExtractionUnitType.SINGLE,
                nodes=[node],
                score=0.0  # Singeltons don't benefit from cluster quality
            ))
            
        return selected_units + single_units
