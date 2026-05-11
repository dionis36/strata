import hashlib

def generate_deterministic_id(name: str, node_type: str) -> str:
    """
    Phase 3: Generates a stable, unique hash for a node.
    Format: SHA256(name + type)
    """
    raw = f"{name}:{node_type}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
