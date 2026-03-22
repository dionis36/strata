import networkx as nx
from domain.extraction.extraction_model import ExtractionUnit


class GraphSimulator:
    """
    The core "what-if" engine. Simulates the systemic graph modifications 
    that occur when an extraction unit is removed and replaced by a remote proxy service.
    """
    def __init__(self, nx_graph: nx.DiGraph):
        self.original_graph = nx_graph

    def simulate_extraction(self, unit: ExtractionUnit) -> nx.DiGraph:
        """
        Clones the original graph, isolates the nodes in the extraction unit,
        replaces them with a single `_Service` proxy boundary node, and rewires
        all inbound and outbound edges to target the proxy.
        """
        g_sim = self.original_graph.copy()
        nodes_to_remove = set(unit.nodes)
        
        if not nodes_to_remove:
            return g_sim
            
        proxy_node = f"{unit.label}_Service"
        g_sim.add_node(proxy_node, type="service", simulated=True)
        
        edges_to_add = []
        
        for u in nodes_to_remove:
            # 1. Outbound edges from the cluster to the remaining system
            for v in self.original_graph.successors(u):
                if v not in nodes_to_remove:
                    edge_data = self.original_graph.edges[u, v]
                    edges_to_add.append((proxy_node, v, edge_data))
                    
            # 2. Inbound edges from the remaining system into the cluster
            for v in self.original_graph.predecessors(u):
                if v not in nodes_to_remove:
                    edge_data = self.original_graph.edges[v, u]
                    edges_to_add.append((v, proxy_node, edge_data))
                    
        # Apply the rewired edges mapping the system to the new proxy
        for u, v, data in edges_to_add:
            # Since networkx DiGraph overwrites edges, if multiple nodes inside
            # the cluster queried the same external table, the proxy will just
            # have a single edge to that table, representing the API boundary.
            if not g_sim.has_edge(u, v):
                g_sim.add_edge(u, v, **data)
                
        # Safely remove the original components that are now "extracted"
        g_sim.remove_nodes_from(nodes_to_remove)
        
        return g_sim
