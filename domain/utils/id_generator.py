import hashlib


def generate_deterministic_id(name: str, node_type: str) -> str:
    """
    Phase 3: Generates a stable, unique hash for a node.
    PHP names (classes, etc.) are case-insensitive, so we normalize to lower.
    """
    normalized_name = name.lower()
    raw = f"{normalized_name}:{node_type}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
