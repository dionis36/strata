"""
Phase 3: Risk Service
Orchestrates the 4-step risk computation pipeline for a given run_id.
Reads Phase 2 ComponentMetric data, produces and persists ComponentRisk rows.
"""
import logging
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ComponentMetric
from infrastructure.persistence.repositories import RiskRepository, BehaviorRepository
from domain.scoring.feature_normalizer import FeatureNormalizer
from domain.scoring.structural_features import engineer_features
from domain.scoring.risk_model import RiskModel
from domain.scoring.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)


class RiskService:
    """Runs the Phase 3 structural risk pipeline for a completed analysis run."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RiskRepository(db)

    def compute_risk(
        self,
        run_id: int,
        weight_overrides: dict = None,
        threshold_overrides: dict = None,
    ) -> list[dict]:
        """Compute and persist risk scores for all components in a run.

        Args:
            run_id: ID of the completed AnalysisRun.
            weight_overrides: Optional custom weights (Phase 6 ablation).
            threshold_overrides: Optional custom classification thresholds (Phase 6).

        Returns:
            List of risk result dicts (one per component), sorted by risk_score desc.
        """
        # 1. Load Phase 2 ComponentMetric rows for this run
        raw_rows = (
            self.db.query(ComponentMetric)
            .filter(ComponentMetric.run_id == run_id)
            .all()
        )

        b_repo = BehaviorRepository(self.db)
        behavior_rows = b_repo.get_behavior_by_run(run_id)
        behavior_map = {b.component_name: b for b in behavior_rows}

        if not raw_rows:
            logger.warning(f"No component metrics found for run_id={run_id}. Skipping risk computation.")
            return []

        # Convert ORM rows → plain dicts for the normalizer
        metrics_list = []
        for row in raw_rows:
            b_row = behavior_map.get(row.component_name)
            metrics_list.append({
                "component_name":  row.component_name,
                "component_type":  row.component_type,
                "betweenness":     row.betweenness,
                "blast_radius":    row.blast_radius,
                "in_degree":       row.in_degree,
                "out_degree":      row.out_degree,
                "scc_size":        row.scc_size,
                "write_intensity": b_row.write_intensity if b_row else 0.0,
                "table_dependencies": b_row.table_dependencies if b_row else 0.0,
                # Semantic fields (Phase 5)
                "domain_archetype": row.domain_archetype,
                "is_stateful":     row.is_stateful,
                "lcom":            row.lcom,
                "wmc":             row.wmc,
            })


        # 2. Fit the per-run normalizer
        normalizer = FeatureNormalizer().fit(metrics_list)

        # 3. Instantiate model and classifier (supports Phase 6 overrides)
        model = RiskModel(weight_overrides=weight_overrides)
        classifier = RiskClassifier(threshold_overrides=threshold_overrides)

        # 4. Compute risk for each component
        results = []
        for metric in metrics_list:
            normalized   = normalizer.normalize(metric)
            features     = engineer_features(normalized, metric)
            risk_score   = model.score(features)
            risk_level   = classifier.classify(risk_score)

            # Phase 4: Behavioral Amplification
            behavioral_factor = 0.0
            if "norm_write_intensity" in normalized:
                behavioral_factor = (
                    0.5 * normalized["norm_write_intensity"] +
                    0.5 * normalized["norm_table_dependencies"]
                )
                behavioral_factor = min(1.0, behavioral_factor)
                
            # Phase 5: Semantic Multiplier
            semantic_multiplier = 1.0
            archetype = metric.get("domain_archetype", "UNKNOWN")
            
            # The Utility Rule
            if archetype == "UTILITY" and not metric.get("is_stateful"):
                semantic_multiplier = 0.2
            # The Controller Rule
            elif archetype == "CONTROLLER" and features["instability"] > 0.8:
                semantic_multiplier = 1.5
            # The God Class Rule
            elif archetype == "GOD_CLASS":
                semantic_multiplier = 2.0
                
            final_risk = risk_score * (1.0 + behavioral_factor) * semantic_multiplier
            final_risk = min(1.0, final_risk)
            
            # Recalculate Risk Level if multiplier changed it
            if final_risk >= classifier.thresholds["critical"]:
                risk_level = "CRITICAL"
            elif final_risk >= classifier.thresholds["high"]:
                risk_level = "HIGH"
            elif final_risk >= classifier.thresholds["medium"]:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            results.append({
                "component_name":   metric["component_name"],
                "component_type":   metric["component_type"],
                # Normalized inputs
                "norm_betweenness":  features["norm_betweenness"],
                "norm_blast_radius": features["norm_blast_radius"],
                "norm_in_degree":    features["norm_in_degree"],
                "norm_out_degree":   features["norm_out_degree"],
                # Derived indicators
                "criticality_index": features["criticality_index"],
                "instability":       features["instability"],
                "cycle_flag":        features["cycle_flag"],
                "coupling_pressure": features["coupling_pressure"],
                # Semantic data
                "domain_archetype":  archetype,
                "is_stateful":       metric.get("is_stateful", False),
                "lcom":              metric.get("lcom", 0.0),
                "wmc":               metric.get("wmc", 0),
                "semantic_multiplier": semantic_multiplier,
                # Risk output
                "risk_score":        risk_score,
                "risk_level":        risk_level,
                "behavioral_factor": behavioral_factor,
                "final_risk":        final_risk,
            })

        # 5. Bulk-persist risk scores
        self.repo.save_risk_scores(run_id, results)

        logger.info(f"[Phase 3&4] Risk computed for run_id={run_id}: {len(results)} components.")
        return sorted(results, key=lambda r: r["final_risk"], reverse=True)
