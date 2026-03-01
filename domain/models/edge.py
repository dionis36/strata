from enum import Enum
from pydantic import BaseModel

class EdgeType(Enum):
    METHOD_CALL = "method_call"
    INSTANTIATION = "instantiation"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    USES_TRAIT = "uses_trait"
    DEPENDS_ON = "depends_on"
    UNKNOWN = "unknown"

class Edge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    # In future phases, weight and other metadata will go here.
