from enum import Enum
from pydantic import BaseModel


class EdgeType(Enum):
    DECLARES = "declares"  # e.g. File -> Class
    CALLS = "calls"        # e.g. Method -> Method
    WRITES_TO = "writes_to"
    READS_FROM = "reads_from"
    INHERITS = "inherits"  # Covers extends and implements
    DEPENDS_ON = "depends_on"
    UNKNOWN = "unknown"

class Edge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    # In future phases, weight and other metadata will go here.
