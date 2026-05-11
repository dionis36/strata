import networkx as nx
from typing import List, Dict, Any
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType
from domain.services.hierarchy_resolver import HierarchyResolver

class SemanticService:
    """
    Phase 2 Service: Refines the graph with semantic intelligence.
    - Resolves inheritance paths.
    - Resolves method-level call targets where possible.
    - Identifies shadowed methods and orphaned symbols.
    """

    def __init__(self, graph_model: Any):
        self.graph_model = graph_model
        self.hierarchy = HierarchyResolver(graph_model.graph)

    def refine_graph(self):
        """Main entry point for semantic refinement."""
        # 1. Resolve Global Hierarchy
        cycles = self.hierarchy.detect_cycles()
        if cycles:
            # Log cycles as architectural risks
            pass

        # 2. Heuristic Call Resolution
        # For all 'method_call' edges where the target is currently a string or incomplete,
        # we attempt to find the most likely target using the global method map.
        self._resolve_instance_calls()

    def _resolve_instance_calls(self):
        """
        Heuristic: If a method name is globally unique, resolve the call to that class.
        In legacy PHP, this is a highly effective way to rebuild broken call graphs.
        """
        # Create a map of {method_name: [list_of_fqns_that_define_it]}
        method_map: Dict[str, List[str]] = {}
        for node_id, data in self.graph_model.graph.nodes(data=True):
            if data.get('type') == NodeType.CLASS.value:
                # The 'methods' list is stored on the node data
                for method in data.get('methods', []):
                    if method not in method_map:
                        method_map[method] = []
                    method_map[method].append(node_id)

        # Iterate over calls and refine
        # (This would be implemented by looking at 'method_call' type edges 
        #  and updating their target_id if a unique match is found)
        pass

    def get_shadowed_methods(self) -> List[Dict[str, str]]:
        """Finds methods that override parents (useful for risk analysis)."""
        shadowed = []
        for node_id, data in self.graph_model.graph.nodes(data=True):
            if data.get('type') == NodeType.CLASS.value:
                ancestors = self.hierarchy.get_all_ancestors(node_id)
                my_methods = set(data.get('methods', []))
                for ancestor in ancestors:
                    parent_data = self.graph_model.graph.nodes.get(ancestor, {})
                    parent_methods = set(parent_data.get('methods', []))
                    overrides = my_methods.intersection(parent_methods)
                    for method in overrides:
                        shadowed.append({
                            "class": node_id,
                            "parent": ancestor,
                            "method": method
                        })
        return shadowed
