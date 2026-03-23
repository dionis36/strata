def calculate_top_k_overlap(baseline_rankings: list[dict], experimental_rankings: list[dict], k: int = 5) -> float:
    """
    Calculates the exact overlap coefficient between two sets of clustered outputs.
    Used during Sensitivity loops to prove that minor weight shifts do not 
    catastrophically destroy the top rankings.
    """
    top_baseline = [c.get("unit") for c in baseline_rankings[:k]]
    top_experimental = [c.get("unit") for c in experimental_rankings[:k]]
    
    set_baseline = set(top_baseline)
    set_experimental = set(top_experimental)
    
    if not set_baseline:
        return 0.0
        
    intersection = len(set_baseline.intersection(set_experimental))
    return round(intersection / len(set_baseline), 3)


def calculate_kendall_tau(baseline_rankings: list[dict], experimental_rankings: list[dict]) -> float:
    """
    Counts the number of concordant and discordant pairs to measure exact ranking stability.
    """
    pass # Reserved for future academic extensions
