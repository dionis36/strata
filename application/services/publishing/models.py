from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

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
    architectural_footprint: dict = Field(default_factory=dict)
    root_path: Optional[str] = None

class DatabaseIntelligence(BaseModel):
    table_name: str
    write_intensity: float
    shared_table_pressure: float

class DependencyIntelligence(BaseModel):
    component_name: str
    in_degree: int
    out_degree: int
    scc_size: int
    is_hotspot: bool

class GlobalStateIntelligence(BaseModel):
    variable_name: str
    mutation_count: int
    read_count: int

class LegacyPosture(BaseModel):
    version_score: float
    namespace_score: float
    db_layer_score: float
    security_score: float
    testability_score: float
    coupling_score: float
    total_score: float

class PresentationCoupling(BaseModel):
    file_path: str
    ui_entanglement_ratio: float
    is_fat_view: bool
    db_queries: int

class ApiEndpoint(BaseModel):
    path: str
    type: Literal["Pure Script", "API Endpoint", "Procedural Router", "Unknown", "Server-Rendered Page"]
    methods: List[str] = Field(default_factory=list)

class VendorDependency(BaseModel):
    file_path: str
    vendor_type: str
    status: str

class BoundaryIntelligence(BaseModel):
    presentation_coupling: List[PresentationCoupling] = Field(default_factory=list)
    api_surface: List[ApiEndpoint] = Field(default_factory=list)
    vendor_inventory: List[VendorDependency] = Field(default_factory=list)
    kpis: Dict[str, Any] = Field(default_factory=dict)

class BoundedContext(BaseModel):
    name: str
    file_count: int
    internal_calls: int
    external_calls: int
    coupling_ratio: float
    db_access: bool
    auth_access: bool

class LayeredArchitecture(BaseModel):
    presentation_ratio: float
    bounded_contexts: List[BoundedContext] = Field(default_factory=list)
    directory_tree: Dict[str, Any] = Field(default_factory=dict)
    file_type_distribution: Dict[str, Any] = Field(default_factory=dict)
    system_topology: Dict[str, Any] = Field(default_factory=dict)

class CanonicalModel(BaseModel):
    system_context: SystemContext
    legacy_intelligence: Dict[str, Any] = Field(default_factory=dict)
    database_intelligence: Dict[str, Any] = Field(default_factory=dict)
    dependency_intelligence: List[DependencyIntelligence] = Field(default_factory=list)
    global_state_intelligence: Dict[str, Any] = Field(default_factory=dict)
    boundary_intelligence: Optional[BoundaryIntelligence] = None
    layered_architecture: Optional[LayeredArchitecture] = None
    strategic_advisory: Dict[str, Any] = Field(default_factory=dict)
    modules: List[Module] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    full_risk_register: List[Finding] = Field(default_factory=list)
    ai_executive_summary: Dict[str, Any] = Field(default_factory=dict)
