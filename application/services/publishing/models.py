from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Evidence(BaseModel):
    type: Literal["file", "edge", "metric"]
    target: str
    metric_value: Optional[float] = None

class Finding(BaseModel):
    id: str
    category: Literal["Architecture", "Security", "Complexity", "Coupling", "Legacy"]
    observation: str
    evidence: List[Evidence]
    impact: str
    reasoning: str
    recommended_action: str
    priority: Literal["Critical", "High", "Medium", "Low"]
    confidence: Literal["Confirmed", "Probable", "Insufficient Evidence"]
    prerequisites: List[str] = Field(default_factory=list)

class Module(BaseModel):
    id: str
    name: str
    boundary_confidence: Literal["Confirmed", "Probable", "Weak"]
    files: List[str]
    dependencies: List[str]
    entry_points: List[str]

class SystemContext(BaseModel):
    project_name: str
    total_files: int
    total_classes: int
    php_era: str
    framework: str
    overall_readiness: float

class CanonicalModel(BaseModel):
    system_context: SystemContext
    modules: List[Module]
    findings: List[Finding]
