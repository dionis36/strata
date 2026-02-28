from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class NodeType(Enum):
    CLASS = "class"
    METHOD = "method"
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
    id: str  # Unique identifier (e.g. fully qualified name or hash)
    name: str
    node_type: NodeType
    file_path: Optional[str] = None
    metrics: NodeMetrics = NodeMetrics()
    
    # Internal representation convenience
    methods: List[str] = []
