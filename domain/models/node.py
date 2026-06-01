from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class NodeType(Enum):
    FILE = "file"
    ENTRY_POINT = "entry_point"
    BOOTSTRAP = "bootstrap"
    CONTROLLER = "controller"
    VIEW = "view"
    CONFIG = "config"
    ASSET = "asset"
    JOB = "job"
    VENDOR = "vendor"
    NAMESPACE = "namespace"
    CLASS = "class"
    INTERFACE = "interface"
    TRAIT = "trait"
    METHOD = "method"
    FUNCTION = "function"
    FIELD = "field"
    TABLE = "table"
    API_ROUTE = "api_route"
    GLOBAL_VAR = "global_var"
    MODEL = "model"
    SCHEMA = "schema"
    SITE_VARIANT = "site_variant"
    UNKNOWN = "unknown"

class NodeMetrics(BaseModel):
    # Core Structural Metrics (Phase 2)
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    weighted_in: int = 0
    weighted_out: int = 0
    betweenness: float = 0.0
    closeness: float = 0.0
    scc_id: int = 0
    scc_size: int = 0
    blast_radius: int = 0

    # Coupling Indicators
    fan_in_ratio: float = 0.0
    fan_out_ratio: float = 0.0
    scc_density: float = 0.0
    reachability_ratio: float = 0.0

class Node(BaseModel):

    id: str  # Deterministic Hash: SHA256(FQN + type)
    name: str  # Short name without namespace
    fqn: str  # Full Fully Qualified Name
    node_type: NodeType
    namespace: Optional[str] = None  # PHP namespace if declared
    file_path: Optional[str] = None
    metrics: NodeMetrics = NodeMetrics()

    # Internal representation convenience
    methods: List[str] = []
    metadata: dict = {}  # Raw AST metadata (requirements, globals, includes etc.)
