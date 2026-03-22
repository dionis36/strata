import networkx as nx
from typing import List, Dict, Set
from collections import defaultdict

from domain.extraction.extraction_model import ExtractionUnit, ExtractionUnitType
from domain.models.node import NodeType
from domain.models.edge import EdgeType


class ClusterBuilder:
    """
    Generates hybrid candidate clusters (SCC, Table-Coupled, Density-Based)
    from the raw system graph.
    """
    def __init__(self, nx_graph: nx.DiGraph):
        self.G = nx_graph
        self.class_nodes = [
            n for n, d in self.G.nodes(data=True) 
            if d.get("type") == NodeType.CLASS.value
        ]

    def build_scc_clusters(self) -> List[ExtractionUnit]:
        """Extract strongly connected components as clusters (cycles)."""
        sccs = list(nx.strongly_connected_components(self.G))
        clusters = []
        for scc in sccs:
            # We only care about cycles among classes
            classes_in_scc = [n for n in scc if self.G.nodes[n].get("type") == NodeType.CLASS.value]
            if len(classes_in_scc) > 1:
                short_name = classes_in_scc[0].split('\\')[-1]
                label = f"{short_name}_SCCLogic"
                clusters.append(ExtractionUnit(
                    label=label,
                    type=ExtractionUnitType.CLUSTER,
                    nodes=classes_in_scc
                ))
        return clusters

    def build_table_coupled_clusters(self) -> List[ExtractionUnit]:
        """Extract clusters of classes that write to the same table."""
        table_writers = defaultdict(list)
        for u, v, data in self.G.edges(data=True):
            if data.get("type") == EdgeType.WRITES.value:
                # u is class, v is table
                if self.G.nodes[u].get("type") == NodeType.CLASS.value:
                    table_writers[v].append(u)
                    
        clusters = []
        for table, writers in table_writers.items():
            unique_writers = list(set(writers))
            if len(unique_writers) >= 2:
                # Table name is likely the node id or its suffix
                table_name = table.split('\\')[-1].capitalize()
                label = f"{table_name}DataModule"
                clusters.append(ExtractionUnit(
                    label=label,
                    type=ExtractionUnitType.CLUSTER,
                    nodes=unique_writers
                ))
        return clusters

    def build_density_clusters(self, density_threshold: float = 0.6) -> List[ExtractionUnit]:
        """Extract tight clusters where internal edges are high compared to possible edges."""
        clusters = []
        visited_dense_sets = set()
        
        # We only look at class nodes subgraph for logic density
        subgraph = self.G.subgraph(self.class_nodes)
        
        for node in self.class_nodes:
            # 1-hop neighborhood (undirected sense to capture tightly knit groups)
            # We include predecessors and successors
            neighbors = set(subgraph.predecessors(node)) | set(subgraph.successors(node))
            neighborhood = list({node} | neighbors)
            
            if len(neighborhood) < 2:
                continue
                
            n_nodes = len(neighborhood)
            possible_edges = n_nodes * (n_nodes - 1)
            if possible_edges == 0:
                continue
                
            # Number of actual edges between these nodes
            sub_g = subgraph.subgraph(neighborhood)
            actual_edges = sub_g.number_of_edges()
            
            density = actual_edges / possible_edges
            if density >= density_threshold:
                frozen_set = frozenset(neighborhood)
                if frozen_set not in visited_dense_sets:
                    visited_dense_sets.add(frozen_set)
                    short_name = node.split('\\')[-1]
                    label = f"{short_name}_DenseModule"
                    clusters.append(ExtractionUnit(
                        label=label,
                        type=ExtractionUnitType.CLUSTER,
                        nodes=neighborhood
                    ))
        return clusters

    def build_all_candidate_clusters(self) -> List[ExtractionUnit]:
        """Returns all SCC, Table, and Density clusters combined. May contain overlaps."""
        scc = self.build_scc_clusters()
        table = self.build_table_coupled_clusters()
        density = self.build_density_clusters(density_threshold=0.6)
        return scc + table + density
