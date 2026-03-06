"""
Phase 3: Risk Service
Orchestrates the 4-step risk computation pipeline for a given run_id.
Reads Phase 2 ComponentMetric data, produces and persists ComponentRisk rows.
"""
import logging
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ComponentMetric
from infrastructure.persistence.repositories import RiskRepository
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

        if not raw_rows:
            logger.warning(f"No component metrics found for run_id={run_id}. Skipping risk computation.")
            return []

        # Convert ORM rows → plain dicts for the normalizer
        metrics_list = [
            {
                "component_name":  row.component_name,
                "component_type":  row.component_type,
                "betweenness":     row.betweenness,
                "blast_radius":    row.blast_radius,
                "in_degree":       row.in_degree,
                "out_degree":      row.out_degree,
                "scc_size":        row.scc_size,
            }
            for row in raw_rows
        ]

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
                # Risk output
                "risk_score":        risk_score,
                "risk_level":        risk_level,
            })

        # 5. Bulk-persist risk scores
        self.repo.save_risk_scores(run_id, results)

        logger.info(f"[Phase 3] Risk computed for run_id={run_id}: {len(results)} components.")
        return sorted(results, key=lambda r: r["risk_score"], reverse=True)
