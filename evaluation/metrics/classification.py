def calculate_classification_metrics(predictions: list[dict], ground_truth: dict) -> dict:
    """
    Computes rigorous Precision, Recall, and F1 limits based on node intersections.
    Because our engine outputs Clusters (lists of nodes), we calculate hit rates 
    by checking if the nodes within Recommended Clusters perfectly cover the Ground Truth nodes.
    """
    safe_truth = set(ground_truth.get("SAFE_TO_EXTRACT", []))
    blocked_truth = set(ground_truth.get("DO_NOT_EXTRACT", []))

    if not safe_truth:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    # Gather nodes that the engine effectively "Predicted to Extract"
    # i.e., Candidates marked as SAFE_TO_EXTRACT or EXTRACT_WITH_CAUTION
    predicted_safe_nodes = set()
    for cand in predictions:
        if cand.get("recommendation") in ("SAFE_TO_EXTRACT", "EXTRACT_WITH_CAUTION"):
            for n in cand.get("nodes", []):
                predicted_safe_nodes.add(n)

    # True Positive: Node is predicted Safe, and is actually Safe
    tp = len(predicted_safe_nodes.intersection(safe_truth))
    # False Positive: Node is predicted Safe, but is either explicitly Blocked or Neutral
    fp = len(predicted_safe_nodes.intersection(blocked_truth))
    # False Negative: Node is actually Safe, but engine predicted Refactor First or Blocked (or ignored it)
    fn = len(safe_truth.difference(predicted_safe_nodes))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn
    }
