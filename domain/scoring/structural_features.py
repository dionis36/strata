"""
Phase 3: Structural Feature Engineering
Derives 4 architectural signal indicators from normalized Phase 2 metrics.
All functions are pure - zero side effects - fully testable in isolation.
"""


def compute_criticality_index(norm_betweenness: float, norm_blast_radius: float) -> float:
    """Chokepoint indicator: many paths pass through AND many downstream components.

    Range: [0, 1]
    """
    return norm_betweenness * norm_blast_radius


def compute_instability(in_degree: float, out_degree: float) -> float:
    """Robert C. Martin instability metric.

    instability = efferent_coupling / (afferent + efferent)
    High value → component depends on many others → change-sensitive.

    Range: [0, 1]. Returns 0.0 if both degrees are zero (isolated node).
    """
    total = in_degree + out_degree
    if total == 0:
        return 0.0
    return out_degree / total


def compute_cycle_flag(scc_size: int) -> int:
    """Binary cycle participation indicator.

    1 → component is in a circular dependency cluster.
    0 → component is acyclic.
    """
    return 1 if scc_size > 1 else 0


def compute_coupling_pressure(norm_in_degree: float, norm_out_degree: float) -> float:
    """Integration density: component is heavily wired into the system.

    Raw sum of normalized in+out, clamped to [0, 1].
    (Dividing by 2 keeps it symmetric with other indicators.)

    Range: [0, 1]
    """
    return min(1.0, (norm_in_degree + norm_out_degree) / 2.0)


def engineer_features(normalized: dict, raw_metric: dict) -> dict:
    """Derive all 4 structural indicators for a single component.

    Args:
        normalized: Output from FeatureNormalizer.normalize() - norm_{field} keys.
        raw_metric: Original metric dict - used for raw in_degree/out_degree/scc_size.

    Returns:
        Dict with: criticality_index, instability, cycle_flag, coupling_pressure
    """
    return {
        "criticality_index": compute_criticality_index(
            normalized.get("norm_betweenness", 0.0),
            normalized.get("norm_blast_radius", 0.0),
        ),
        "instability": compute_instability(
            float(raw_metric.get("in_degree", 0)),
            float(raw_metric.get("out_degree", 0)),
        ),
        "cycle_flag": compute_cycle_flag(
            int(raw_metric.get("scc_size", 1))
        ),
        "coupling_pressure": compute_coupling_pressure(
            normalized.get("norm_in_degree", 0.0),
            normalized.get("norm_out_degree", 0.0),
        ),
        # Carry through normalized values for persistence
        "norm_betweenness":  normalized.get("norm_betweenness", 0.0),
        "norm_blast_radius": normalized.get("norm_blast_radius", 0.0),
        "norm_in_degree":    normalized.get("norm_in_degree", 0.0),
        "norm_out_degree":   normalized.get("norm_out_degree", 0.0),
    }
