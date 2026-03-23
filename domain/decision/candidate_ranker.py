from domain.extraction.extraction_model import (
    ExtractionUnit, 
    ImpactMetrics, 
    ExtractionCandidate, 
    RecommendationCategory
)


class CandidateRanker:
    """
    Decides the final feasibility and generates a human-readable "AI Verdict"
    translating mathematically why a component received its Recommendation.
    """
    def rank(self, unit: ExtractionUnit, impact: ImpactMetrics) -> ExtractionCandidate:
        reasoning = []
        
        # 3. Decision Logic & Primary AI Verdict
        recommendation = RecommendationCategory.DO_NOT_EXTRACT
        
        if impact.data_isolation_difficulty >= 4 or impact.risk_change >= 0.15:
            recommendation = RecommendationCategory.DO_NOT_EXTRACT
            reasoning.append("**AI Verdict: Extraction Blocked.** This component is critically entangled with the monolith's data or state. Extracting it would cause massive architectural cascading failures.")
        elif unit.score < 0.35 or impact.interface_complexity >= 15:
            recommendation = RecommendationCategory.REQUIRES_REFACTOR_FIRST
            reasoning.append("**AI Verdict: Refactor First.** While logically related, drawing a network boundary around this cluster would create an unstable interface. You must refactor external dependencies *inside* the monolith before extracting.")
        elif unit.score >= 0.50 and impact.risk_change <= 0 and impact.data_isolation_difficulty <= 1:
            recommendation = RecommendationCategory.SAFE_TO_EXTRACT
            reasoning.append("**AI Verdict: Safe to Extract.** This cleanly bounded context can be safely containerized. It lowers or neutralizes total systemic risk.")
        else:
            recommendation = RecommendationCategory.EXTRACT_WITH_CAUTION
            reasoning.append("**AI Verdict: Proceed with Caution.** A viable candidate, but architectural vigilance is required due to moderate coupling or shared data layers.")

        # Detailed Diagnoses
        if impact.interface_complexity >= 10:
            reasoning.append(f"**Interface Penalty:** The simulated API boundary is crossed by {impact.interface_complexity} tight synchronous logic calls. Microservice latency will immediately degrade performance.")
            
        if impact.data_isolation_difficulty >= 3:
            reasoning.append(f"**Data Penalty:** This module directly modifies {impact.data_isolation_difficulty} tables accessed heavily by other monolithic modules. A split-brain data scenario is highly likely.")

        if impact.risk_change < 0:
            reasoning.append(f"**Risk Shift:** Overall system risk successfully decreases by {abs(impact.risk_change):.3f}.")
        elif impact.risk_change > 0:
            reasoning.append(f"**Risk Warning:** The rigid proxy boundary INCREASES system risk by {impact.risk_change:.3f} due to networking penalties.")
            
        return ExtractionCandidate(
            unit=unit.label,
            type=unit.type,
            nodes=unit.nodes,
            score=unit.score,
            impact=impact,
            recommendation=recommendation,
            reasoning=reasoning
        )
