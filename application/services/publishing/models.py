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
    mermaid_diagram: Optional[str] = None
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
    lines_of_code: int = 0
    avg_complexity: float = 0.0
    connectivity: int = 0
    test_coverage: str = "N/A"
    php_era: str
    framework: str
    overall_readiness: float

class DatabaseIntelligence(BaseModel):
    table_name: str
    write_intensity: float
    shared_table_pressure: float

class LegacyPosture(BaseModel):
    version_score: float
    namespace_score: float
    db_layer_score: float
    security_score: float
    testability_score: float
    coupling_score: float
    total_score: float

class CanonicalModel(BaseModel):
    system_context: SystemContext
    legacy_posture: Optional[LegacyPosture] = None
    database_intelligence: List[DatabaseIntelligence] = Field(default_factory=list)
    modules: List[Module]
    findings: List[Finding]
