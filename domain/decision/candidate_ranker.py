from domain.extraction.extraction_model import (
    ExtractionUnit, 
    ImpactMetrics, 
    ExtractionCandidate, 
    RecommendationCategory
)


class CandidateRanker:
    """
    Decides the final feasibility and recommendation category for an extraction
    candidate based on its inherent cluster score and its simulated structural impact.
    """
    def rank(self, unit: ExtractionUnit, impact: ImpactMetrics) -> ExtractionCandidate:
        reasoning = []
        
        # 1. Cluster Quality Reasoning
        if unit.score >= 0.6:
            reasoning.append(f"High-quality architectural boundary (Score: {unit.score:.2f}).")
        elif unit.score >= 0.4:
            reasoning.append(f"Moderate cohesion and isolation (Score: {unit.score:.2f}).")
        else:
            reasoning.append(f"Weak cohesion or severe external coupling (Score: {unit.score:.2f}).")
            
        # 2. Impact Reasoning
        if impact.risk_change < 0:
            reasoning.append(f"System risk decreases by {abs(impact.risk_change):.3f}.")
        elif impact.risk_change > 0:
            reasoning.append(f"System risk INCREASES by {impact.risk_change:.3f}.")
            
        if impact.interface_complexity >= 10:
            reasoning.append(f"High API surface: {impact.interface_complexity} cross-boundary calls.")
            
        if impact.data_isolation_difficulty >= 3:
            reasoning.append(f"High data entanglement: shares {impact.data_isolation_difficulty} tables with other modules.")

        # 3. Decision Logic
        recommendation = RecommendationCategory.DO_NOT_EXTRACT
        
        if impact.data_isolation_difficulty >= 4 or impact.risk_change >= 0.15:
            recommendation = RecommendationCategory.DO_NOT_EXTRACT
            reasoning.append("Verdict: Extraction blocked due to extreme data entanglement or massive risk surge.")
        elif unit.score < 0.35 or impact.interface_complexity >= 15:
            recommendation = RecommendationCategory.REQUIRES_REFACTOR_FIRST
            reasoning.append("Verdict: Refactor internally to reduce external dependencies before extraction.")
        elif unit.score >= 0.50 and impact.risk_change <= 0 and impact.data_isolation_difficulty <= 1:
            recommendation = RecommendationCategory.SAFE_TO_EXTRACT
            reasoning.append("Verdict: Clean boundary with net-positive or neutral systemic risk impact.")
        else:
            recommendation = RecommendationCategory.EXTRACT_WITH_CAUTION
            reasoning.append("Verdict: Viable extraction, but monitor interface complexity and data sharing.")
            
        return ExtractionCandidate(
            unit=unit.label,
            type=unit.type,
            nodes=unit.nodes,
            score=unit.score,
            impact=impact,
            recommendation=recommendation,
            reasoning=reasoning
        )
