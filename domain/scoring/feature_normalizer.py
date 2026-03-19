"""
Phase 3: Feature Normalizer
Applies per-run min-max normalization to raw Phase 2 metrics.
System-relative: each run is normalized within its own min/max.
"""
from typing import List, Dict


class FeatureNormalizer:
    """Fits on a list of raw metric dicts and normalizes each component."""

    FIELDS = ["betweenness", "blast_radius", "in_degree", "out_degree", "write_intensity", "table_dependencies"]

    def __init__(self):
        self._min: Dict[str, float] = {}
        self._max: Dict[str, float] = {}
        self._fitted = False

    def fit(self, metrics_list: List[dict]) -> "FeatureNormalizer":
        """Compute min and max for each field across the run.

        Args:
            metrics_list: List of raw metric dicts from ComponentMetric rows.
        """
        for field in self.FIELDS:
            values = [float(m.get(field, 0.0)) for m in metrics_list]
            self._min[field] = min(values) if values else 0.0
            self._max[field] = max(values) if values else 0.0
        self._fitted = True
        return self

    def normalize(self, metric: dict) -> dict:
        """Normalize a single metric dict.

        Returns a new dict with norm_{field} keys in [0.0, 1.0].
        """
        if not self._fitted:
            raise RuntimeError("FeatureNormalizer.fit() must be called before normalize().")

        normalized = {}
        for field in self.FIELDS:
            raw = float(metric.get(field, 0.0))
            lo = self._min[field]
            hi = self._max[field]
            if hi == lo:
                # All components have identical values → assign 0.0 (no signal)
                normalized[f"norm_{field}"] = 0.0
            else:
                normalized[f"norm_{field}"] = (raw - lo) / (hi - lo)
        return normalized
