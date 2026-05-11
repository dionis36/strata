import networkx as nx
from typing import List, Dict, Set
from collections import defaultdict

from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType

EXTRACTABLE_TYPES = {"class", "file", "function", "script"}

class ClusterBuilder:
    """
    Generates hybrid candidate clusters (SCC, Table-Coupled, Density-Based, Risk-Targeted)
    from the raw system graph. Bridged with Phase 3 Risk metrics to pinpoint hotspots.
    """
    def __init__(self, nx_graph: nx.DiGraph, original_risk_map: dict = None):
        self.G = nx_graph
        self.original_risk_map = original_risk_map or {}
        
        # FIXED: Capture EVERYTHING that executes logic (classes, files, functions)
        # Avoid non-code architectural boundaries like "table", "external", "infra"
        self.extractable_nodes = [
            n for n, d in self.G.nodes(data=True) 
            if d.get("type", "").lower() in EXTRACTABLE_TYPES
            or not d.get("type")  # Unclassified nodes are treated as code by default
        ]

    def build_scc_clusters(self) -> List[ExtractionUnit]:
        sccs = list(nx.strongly_connected_components(self.G))
        clusters = []
        for scc in sccs:
            code_in_scc = [n for n in scc if n in self.extractable_nodes]
            if len(code_in_scc) > 1:
                short_name = code_in_scc[0].split('\\')[-1].split('/')[-1]
                label = f"{short_name}_SCCLogic"
                clusters.append(ExtractionUnit(
                    label=label,
                    type=ExtractionUnitType.CLUSTER,
                    nodes=code_in_scc
                ))
        return clusters

    def build_table_coupled_clusters(self) -> List[ExtractionUnit]:
        table_writers = defaultdict(list)
        for u, v, data in self.G.edges(data=True):

            if data.get("type", "").upper() == "WRITES_TO":
                if u in self.extractable_nodes:
                    table_writers[v].append(u)
                    
        clusters = []
        for table, writers in table_writers.items():
            unique_writers = list(set(writers))
            if len(unique_writers) >= 2:
                table_name = table.split('\\')[-1].split('/')[-1].capitalize()
                label = f"{table_name}DataModule"
                clusters.append(ExtractionUnit(
                    label=label,
                    type=ExtractionUnitType.CLUSTER,
                    nodes=unique_writers
                ))
        return clusters

    def build_density_clusters(self, density_threshold: float = 0.25) -> List[ExtractionUnit]:
        clusters = []
        visited_dense_sets = set()
        subgraph = self.G.subgraph(self.extractable_nodes)
        
        for node in self.extractable_nodes:
            neighbors = set(subgraph.predecessors(node)) | set(subgraph.successors(node))
            neighborhood = list({node} | neighbors)
            
            if len(neighborhood) < 2:
                continue
                
            n_nodes = len(neighborhood)
            possible_edges = n_nodes * (n_nodes - 1)
            if possible_edges == 0:
                continue
                
            sub_g = subgraph.subgraph(neighborhood)
            actual_edges = sub_g.number_of_edges()
            
            density = actual_edges / possible_edges
            if density >= density_threshold:
                frozen_set = frozenset(neighborhood)
                if frozen_set not in visited_dense_sets:
                    visited_dense_sets.add(frozen_set)
                    short_name = node.split('\\')[-1].split('/')[-1]
                    label = f"{short_name}_DenseModule"
                    clusters.append(ExtractionUnit(
                        label=label,
                        type=ExtractionUnitType.CLUSTER,
                        nodes=neighborhood
                    ))
        return clusters

    def build_risk_targeted_clusters(self) -> List[ExtractionUnit]:
        clusters = []
        if not self.original_risk_map:
            return clusters
            
        sorted_risk = sorted(self.original_risk_map.items(), key=lambda x: x[1], reverse=True)
        top_nodes = [node for node, risk in sorted_risk[:15] if node in self.extractable_nodes]
        
        visited_heavy_sets = set()
        for bottleneck in top_nodes:
            consumers = set(self.G.predecessors(bottleneck))
            code_consumers = {c for c in consumers if c in self.extractable_nodes}
            
            neighborhood = list({bottleneck} | code_consumers)
            if len(neighborhood) >= 2:
                frozen = frozenset(neighborhood)
                if frozen not in visited_heavy_sets:
                    visited_heavy_sets.add(frozen)
                    short_name = bottleneck.split('\\')[-1].split('/')[-1]
                    clusters.append(ExtractionUnit(
                        label=f"{short_name}_RiskIsolation",
                        type=ExtractionUnitType.CLUSTER,
                        nodes=neighborhood
                    ))
        return clusters

    def build_all_candidate_clusters(self) -> List[ExtractionUnit]:
        scc = self.build_scc_clusters()
        table = self.build_table_coupled_clusters()
        density = self.build_density_clusters(density_threshold=0.25)
        risk = self.build_risk_targeted_clusters()
        return scc + table + density + risk
