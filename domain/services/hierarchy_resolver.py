import networkx as nx
from typing import Dict, List, Set
from domain.models.edge import EdgeType

class HierarchyResolver:
    """
    Phase 2 Service: Resolves the global inheritance and implementation hierarchy.
    Ensures that for any class, we can retrieve its full lineage (parents, traits, interfaces).
    """

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        # Filter graph for hierarchy edges only
        self.hierarchy_types = {EdgeType.INHERITS, EdgeType.IMPLEMENTS, EdgeType.USES_TRAIT}
        self.hierarchy_graph = nx.DiGraph()
        
        for u, v, data in self.graph.edges(data=True):
            if data.get('type') in self.hierarchy_types:
                self.hierarchy_graph.add_edge(u, v, type=data.get('type'))

    def get_parents(self, node_id: str) -> List[str]:
        """Returns immediate parents of a node."""
        if not self.hierarchy_graph.has_node(node_id):
            return []
        return list(self.hierarchy_graph.successors(node_id))

    def get_all_ancestors(self, node_id: str) -> Set[str]:
        """Returns all ancestors (parents of parents) of a node."""
        if not self.hierarchy_graph.has_node(node_id):
            return set()
        return nx.descendants(self.hierarchy_graph, node_id)

    def get_lineage_report(self) -> Dict[str, List[str]]:
        """Returns a map of every class to its full FQN inheritance path."""
        report = {}
        for node in self.hierarchy_graph.nodes():
            report[node] = list(self.get_all_ancestors(node))
        return report

    def detect_cycles(self) -> List[List[str]]:
        """Identifies circular inheritance, which is an error in PHP."""
        try:
            return list(nx.simple_cycles(self.hierarchy_graph))
        except Exception:
            return []
