import networkx as nx
from domain.extraction.extraction_model import ExtractionUnit, ImpactMetrics


class ImpactAnalyzer:
    """
    Measures the architectural and topological consequences of a simulated extraction.
    """
    def __init__(self, original_graph: nx.DiGraph, original_risk_map: dict):
        self.G = original_graph
        self.original_risk_map = original_risk_map
        self.original_total_risk = sum(original_risk_map.values()) if original_risk_map else 0.0

    def analyze(self, unit: ExtractionUnit, g_sim: nx.DiGraph) -> ImpactMetrics:
        """
        Calculates interface complexity, data isolation difficulty, 
        and the estimated shift in overall system risk. 
        """
        nodes = set(unit.nodes)
        
        # 1. Dependency Breaks (how many coupling edges are severed)
        dependency_breaks = 0
        for u in nodes:
            # Outbound broke
            dependency_breaks += len([v for v in self.G.successors(u) if v not in nodes])
            # Inbound broke
            dependency_breaks += len([v for v in self.G.predecessors(u) if v not in nodes])
            
        proxy_node = f"{unit.label}_Service"
        interface_complexity = 0
        data_isolation = 0
        
        if proxy_node in g_sim:
            # 2. Interface Complexity (Edges passing through the new service boundary)
            interface_complexity = g_sim.in_degree(proxy_node) + g_sim.out_degree(proxy_node)
            
            # 3. Data Isolation Difficulty (Number of shared tables cross-boundary)
            for v in g_sim.successors(proxy_node):
                if g_sim.edges[proxy_node, v].get("type", "").upper() == "WRITES":
                    data_isolation += 1
                    
        # 4. Risk Change Estimation
        # Real risk recalculation would hit the DB. For fast simulation, we estimate:
        # The new system total risk is the original total minus the risk of the 
        # extracted nodes, plus the new risk introduced by the proxy boundary.
        extracted_risk = sum(self.original_risk_map.get(n, 0.0) for n in nodes)
        
        # Proxy risk penalty: steep cost for high interface complexity and data sharing
        proxy_risk = min(1.0, (interface_complexity * 0.05) + (data_isolation * 0.15))
        
        # Negative means reduction in risk (good)
        new_total_risk = self.original_total_risk - extracted_risk + proxy_risk
        risk_change = new_total_risk - self.original_total_risk
        
        return ImpactMetrics(
            dependency_breaks=dependency_breaks,
            interface_complexity=interface_complexity,
            data_isolation_difficulty=data_isolation,
            risk_change=round(risk_change, 3)
        )
