from tests.benchmark_validation import run_benchmark

def test_advisory_accuracy_benchmark():
    """
    Ensure the strategic modernization advisory algorithm achieves the required F1-Score accuracy on WebGoat.
    """
    results = run_benchmark()
    
    project_path = "/data/OWASPWebGoatPHP-master/app/model"
    assert project_path in results, "WebGoat model folder must be benchmarked"
    
    metrics = results[project_path]
    
    # Assertions
    assert metrics["f1_score"] >= 0.80, f"F1-Score should be >= 0.80, got {metrics['f1_score']:.3f}"
    assert metrics["precision"] >= 0.75, f"Precision should be >= 0.75, got {metrics['precision']:.3f}"
    assert metrics["tp"] >= 1, "Should correctly identify at least 1 safe unit"
