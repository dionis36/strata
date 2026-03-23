import logging
from evaluation.runners.experiment_runner import ExperimentRunner

logger = logging.getLogger(__name__)

def run_weight_sensitivity(run_id: int) -> dict:
    """
    Randomly or systematically perturbs the structural weighting factors 
    in the mathematical models to verify that the heuristic limits are 
    architecturally robust and do not cause cascading failures under variation.
    """
    runner = ExperimentRunner()
    results = {}
    
    # Run 1: Baseline Default Config
    results["baseline_0.30"] = runner.execute_full_pipeline(run_id)
    
    perturbations = [0.10, 0.20, 0.40, 0.50]
    
    for variance in perturbations:
        logger.info(f"Perturbing Instability risk bounds to {variance}")
        # Shuffle Risk Weight
        runner.config["weights"]["risk_factors"]["w_instability"] = variance
        
        # We iteratively run the full Phase2-Phase5 pipeline completely internally securely 
        var_cluster = runner.execute_full_pipeline(run_id)
        results[f"variance_{variance}"] = var_cluster
        
    return results
