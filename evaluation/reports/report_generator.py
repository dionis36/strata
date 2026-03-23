import os
import json
import logging
import matplotlib
# Use Agg backend so matplotlib doesn't hang in headless setups
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evaluation.experiments.ablation import run_ablation_study
from evaluation.experiments.weight_sensitivity import run_weight_sensitivity
from evaluation.metrics.classification import calculate_classification_metrics
from evaluation.metrics.ranking import calculate_top_k_overlap

logger = logging.getLogger(__name__)

def generate_full_evaluation_report(run_id: int):
    # 1. Load pseudo-truth rules mapping
    gt_path = f"evaluation/ground_truth/graph_{run_id}_truth.json"
    if not os.path.exists(gt_path):
        gt_path = "evaluation/ground_truth/graph_1_truth.json"
    
    with open(gt_path, "r") as f:
        ground_truth = json.load(f)
        
    # 2. Run Ablation
    ablation_results = run_ablation_study(run_id)
    
    # 3. Calculate F1 Accuracies
    metrics_report = {}
    f1_scores = {}
    for variation, candidates in ablation_results.items():
        metrics = calculate_classification_metrics(candidates, ground_truth)
        metrics_report[variation] = metrics
        f1_scores[variation] = metrics["f1"]
        
    os.makedirs("evaluation/results/charts", exist_ok=True)
    
    # 4. Generate Ablation Chart
    plt.figure(figsize=(8, 5))
    plt.bar(list(f1_scores.keys()), list(f1_scores.values()), color=['blue', 'orange', 'red'])
    plt.title("Ablation Study: Architecture Extraction Accuracy Dropoff")
    plt.ylabel("F1 Score vs Ground Truth")
    plt.ylim(0, 1.0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig("evaluation/results/charts/ablation_f1.png")
    plt.close()
    
    # 5. Run Perturbation Loop (Sensitivity Checks)
    sensitivity_results = run_weight_sensitivity(run_id)
    baseline_top = sensitivity_results["baseline_0.30"]
    
    overlaps = {}
    for var, cands in sensitivity_results.items():
        if var != "baseline_0.30":
            overlaps[var] = calculate_top_k_overlap(baseline_top, cands)
            
    # 6. Generate Ranking Chart
    if overlaps:
        plt.figure(figsize=(8, 5))
        plt.plot(list(overlaps.keys()), list(overlaps.values()), marker="o", linestyle="-", color="green", linewidth=2)
        plt.title("Risk Model Mathematical Sensitivity")
        plt.ylabel("Top 5 Rank Overlap Rate")
        plt.ylim(0, 1.0)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.savefig("evaluation/results/charts/sensitivity_overlap.png")
        plt.close()
        
    # 7. Package Data Payload
    report_data = {
        "run_id": run_id,
        "ablation_metrics": metrics_report,
        "sensitivity_overlaps": overlaps
    }
    with open("evaluation/results/report.json", "w") as f:
        json.dump(report_data, f, indent=4)
        
    logger.info("Academic Evaluation report generated successfully.")
    return report_data
