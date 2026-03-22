from enum import Enum
from typing import List
from pydantic import BaseModel, ConfigDict


class ExtractionUnitType(str, Enum):
    SINGLE = "single"
    CLUSTER = "cluster"


class ExtractionUnit(BaseModel):
    """Internal representation of a cluster or single node to be extracted."""
    label: str
    type: ExtractionUnitType
    nodes: List[str]
    score: float = 0.0  # Quality score of the cluster


class ImpactMetrics(BaseModel):
    """Simulation results representing the architectural consequences of an extraction."""
    dependency_breaks: int
    risk_change: float
    interface_complexity: int
    data_isolation_difficulty: int


class RecommendationCategory(str, Enum):
    SAFE_TO_EXTRACT = "SAFE_TO_EXTRACT"
    EXTRACT_WITH_CAUTION = "EXTRACT_WITH_CAUTION"
    REQUIRES_REFACTOR_FIRST = "REQUIRES_REFACTOR_FIRST"
    DO_NOT_EXTRACT = "DO_NOT_EXTRACT"


class ExtractionCandidate(BaseModel):
    """Final output payload for a single extraction recommendation."""
    model_config = ConfigDict(populate_by_name=True)

    unit: str  # Flattened: corresponds to ExtractionUnit.label
    type: ExtractionUnitType
    nodes: List[str]
    score: float
    impact: ImpactMetrics
    recommendation: RecommendationCategory
    reasoning: List[str] = []  # Detailed text explaining the reasoning
