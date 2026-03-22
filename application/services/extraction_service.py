import logging
import networkx as nx
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ComponentRisk
from domain.explanation.evidence_builder import EvidenceBuilder

# Extraction Modules
from domain.extraction.cluster_builder import ClusterBuilder
from domain.extraction.cluster_scorer import ClusterScorer
from domain.extraction.conflict_resolver import ConflictResolver
from domain.simulation.graph_simulator import GraphSimulator
from domain.simulation.impact_analyzer import ImpactAnalyzer
from domain.decision.candidate_ranker import CandidateRanker

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Orchestrates Phase 5: Generates extraction candidates, simulates their removal,
    calculates architectural impact, and ranks them by feasibility.
    """
    def __init__(self, db: Session):
        self.db = db

    def analyze_extraction(self, run_id: int) -> list[dict]:
        # 1. Fetch original risk scores for the run
        risk_rows = self.db.query(ComponentRisk).filter(ComponentRisk.run_id == run_id).all()
        if not risk_rows:
            logger.warning(f"[ExtractionService] No risk rows for run_id={run_id}")
            return []
            
        original_risk_map = {row.component_name: row.final_risk for row in risk_rows}
        
        # 2. Fetch the graph JSON
        graph_data = EvidenceBuilder.load_graph(run_id)
        if not graph_data:
            logger.warning(f"[ExtractionService] Graph not found for run_id={run_id}")
            return []
            
        # 3. Build NetworkX DiGraph
        nx_graph = nx.DiGraph()
        for node_id, data in graph_data.get("nodes", {}).items():
            nx_graph.add_node(node_id, **data)
        for link in graph_data.get("links", []):
            nx_graph.add_edge(link["source"], link["target"], type=link.get("type", "CALLS"))
            
        # 4. Phase 5 Pipeline
        cluster_builder = ClusterBuilder(nx_graph)
        scorer = ClusterScorer(nx_graph)
        resolver = ConflictResolver(nx_graph)
        simulator = GraphSimulator(nx_graph)
        analyzer = ImpactAnalyzer(nx_graph, original_risk_map)
        ranker = CandidateRanker()
        
        # 4a. Candidates formulation
        raw_candidates = cluster_builder.build_all_candidate_clusters()
        for c in raw_candidates:
            scorer.score_cluster(c)
            
        # 4b. Conflict resolution (Greedy Selection)
        final_units = resolver.resolve(raw_candidates)
        
        # 4c. Simulation & Impact & Ranking
        results = []
        for unit in final_units:
            # Simulate removing the node/cluster into a distinct boundary
            g_sim = simulator.simulate_extraction(unit)
            
            # Measure strictly the impact of this change
            impact = analyzer.analyze(unit, g_sim)
            
            # Rank and formulate final response
            candidate = ranker.rank(unit, impact)
            results.append(candidate.model_dump(by_alias=True))
            
        # Optional: Sort results. Highest score first.
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
