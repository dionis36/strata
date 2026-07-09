"""
Phase 4.5: Explanation Service
Orchestrates the full explainability pipeline for a completed analysis run.

Pipeline:
  1. Query ComponentRisk + ComponentBehavior → merged component_data dict
  2. Load graph JSON from disk (once, shared across all components)
  3. For each component: RiskReasoner → explanations, EvidenceBuilder → evidence
  4. Return sorted list of ComponentExplanation (by final_risk DESC)

This service is stateless and read-only no DB writes, no new tables.
"""
import logging
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ComponentRisk
from infrastructure.persistence.repositories import BehaviorRepository, RiskRepository
from domain.explanation.reasoner import RiskReasoner
from domain.explanation.evidence_builder import EvidenceBuilder
from domain.explanation.explanation_model import ComponentExplanation

logger = logging.getLogger(__name__)


class ExplanationService:
    """Generates on-the-fly explanations for all components in a run."""

    def __init__(self, db: Session):
        self.db = db
        self._reasoner = RiskReasoner()  # Uses canonical RULES from rules.py

    def explain_run(self, run_id: int) -> list[dict]:
        """Generate and return explanations for every component in a run.

        Args:
            run_id: ID of a completed AnalysisRun.

        Returns:
            List of ComponentExplanation dicts, sorted by final_risk DESC.
            Returns [] if no risk data exists for the run.
        """
        # 1. Load Phase 3/4 risk rows
        risk_rows = (
            self.db.query(ComponentRisk)
            .filter(ComponentRisk.run_id == run_id)
            .all()
        )
        if not risk_rows:
            logger.warning(f"[ExplanationService] No risk rows for run_id={run_id}")
            return []

        # 2. Load behavioral rows and index by component name
        b_repo = BehaviorRepository(self.db)
        behavior_map = {
            b.component_name: b
            for b in b_repo.get_behavior_by_run(run_id)
        }

        # 3. Load graph JSON once for the run
        graph = EvidenceBuilder.load_graph(run_id)
        if not graph:
            logger.warning(
                f"[ExplanationService] Graph not found for run_id={run_id}. "
                "Evidence will be partial (no graph context)."
            )

        # 4. Process each component
        results = []
        for row in risk_rows:
            b_row = behavior_map.get(row.component_name)

            # Merge Phase 3 + Phase 4 metrics into one flat dict for the reasoner
            component_data = {
                "component_name":   row.component_name,
                "criticality_index": row.criticality_index,
                "instability":       row.instability,
                "cycle_flag":        row.cycle_flag,
                "scc_size":          0,  # pulled from graph below if available
                "coupling_pressure": row.coupling_pressure,
                "blast_radius":      row.norm_blast_radius,  # normalised version for context
                "write_intensity":   b_row.write_intensity   if b_row else 0.0,
                "table_dependencies": b_row.table_dependencies if b_row else 0,
                "behavioral_factor": row.behavioral_factor,
                "final_risk":        row.final_risk,
            }

            # Enrich scc_size from graph if available (O(1) with pre-indexed nodes)
            if graph:
                node_data = graph.get("nodes", {}).get(row.component_name, {})
                component_data["scc_size"] = node_data.get("scc_size", 0)

            # 5. Run the reasoner
            explanations = self._reasoner.explain(component_data)

            # 6. Build evidence payload
            evidence = EvidenceBuilder.build(row.component_name, component_data, graph)

            results.append(
                ComponentExplanation(
                    component_name=row.component_name,
                    risk_level=row.risk_level,
                    final_risk=row.final_risk,
                    explanations=explanations,
                    evidence=evidence,
                ).model_dump()
            )

        # Sort by final_risk descending
        return sorted(results, key=lambda r: r["final_risk"], reverse=True)
