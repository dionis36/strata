import logging
from evaluation.runners.experiment_runner import ExperimentRunner

logger = logging.getLogger(__name__)

def run_ablation_study(run_id: int) -> dict:
    """
    Executes multiple passes of the architecture generator, intentionally 
    disabling core heuristic layers to prove their mathematical contribution.
    """
    runner = ExperimentRunner()
    results = {}
    
    # Run 1: Full Baseline
    logger.info("Starting Ablation: Baseline Full Engine")
    results["baseline"] = runner.execute_full_pipeline(run_id)
    
    # Run 2: Remove DB Behavior (Disable Phase 4)
    logger.info("Starting Ablation: No Database Behavior")
    runner.config["weights"]["risk_factors"]["w_behavior"] = 0.0
    runner.config["weights"]["cluster_factors"]["behavior"] = 0.0
    results["no_behavior"] = runner.execute_full_pipeline(run_id)
    
    # Run 3: Remove Structural Network Density 
    logger.info("Starting Ablation: No Density Logic")
    # Restore behavior
    runner.config["weights"]["risk_factors"]["w_behavior"] = 0.20
    runner.config["weights"]["cluster_factors"]["behavior"] = 0.15
    # Kill density
    runner.config["weights"]["cluster_factors"]["cohesion"] = 0.0
    runner.config["weights"]["cluster_factors"]["isolation"] = 0.0
    results["no_density"] = runner.execute_full_pipeline(run_id)
    
    return results
