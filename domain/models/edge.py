from enum import Enum
from pydantic import BaseModel


class EdgeType(Enum):
    DECLARES = "declares"  # e.g. File -> Class
    CALLS = "calls"        # e.g. Method -> Method
    INSTANTIATES = "instantiates" # e.g. Class uses `new` keyword
    STATIC_CALL = "static_call" # e.g. Class::method()
    INJECTS = "injects" # e.g. Dependency passed via constructor
    WRITES_TO = "writes_to"
    READS_FROM = "reads_from"
    INHERITS = "inherits"  # Covers extends and implements
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    UNKNOWN = "unknown"

from typing import Optional

class Edge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    target_fqn: Optional[str] = None
