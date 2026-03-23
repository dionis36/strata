import networkx as nx
from typing import List
from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType

EXTRACTABLE_TYPES = {"class", "file", "function", "script"}

class ConflictResolver:
    """
    Implements greedy non-overlapping cluster selection.
    Only emits fallback singletons if their Phase 3 risk is HIGH/CRITICAL.
    """
    def __init__(self, nx_graph: nx.DiGraph, original_risk_map: dict = None):
        self.original_risk_map = original_risk_map or {}
        
        # Expand scope to match ClusterBuilder
        self.extractable_nodes = set(
            n for n, d in nx_graph.nodes(data=True) 
            if d.get("type", "").lower() in EXTRACTABLE_TYPES
            or not d.get("type")
        )

    def resolve(self, candidate_clusters: List[ExtractionUnit]) -> List[ExtractionUnit]:
        sorted_candidates = sorted(candidate_clusters, key=lambda c: c.score, reverse=True)
        
        selected_units = []
        used_nodes = set()
        
        for cluster in sorted_candidates:
            if not any(node in used_nodes for node in cluster.nodes):
                selected_units.append(cluster)
                used_nodes.update(cluster.nodes)
                
        # Fallback: Only extract singletons if they are mathematically dangerous (e.g., Risk > ~0.4)
        remaining_nodes = self.extractable_nodes - used_nodes
        single_units = []
        for node in remaining_nodes:
            risk = self.original_risk_map.get(node, 0.0)
            if risk >= 0.4:
                short_name = node.split('\\')[-1].split('/')[-1]
                single_units.append(ExtractionUnit(
                    label=f"{short_name}_HighRisk",
                    type=ExtractionUnitType.SINGLE,
                    nodes=[node],
                    score=0.0
                ))
            
        return selected_units + single_units
