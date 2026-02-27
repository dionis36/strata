from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class NodeType(Enum):
    CLASS = "class"
    METHOD = "method"
    UNKNOWN = "unknown"

class NodeMetrics(BaseModel):
    # Placeholders for future phases
    pass

class Node(BaseModel):
    id: str  # Unique identifier (e.g. fully qualified name or hash)
    name: str
    node_type: NodeType
    file_path: Optional[str] = None
    metrics: NodeMetrics = NodeMetrics()
    
    # Internal representation convenience
    methods: List[str] = []
