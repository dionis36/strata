import os
import re
from typing import List, Tuple, Optional
from domain.models.node import Node, NodeType
from domain.models.edge import Edge, EdgeType

# Regex patterns
_NS_PATTERN = re.compile(r'^\s*namespace\s+([\w\\]+)\s*;', re.MULTILINE)
_CLASS_PATTERN = re.compile(
    r'\bclass\s+([A-Za-z0-9_]+)'
    r'(?:\s+extends\s+([A-Za-z0-9_\\]+))?'
    r'(?:\s+implements\s+([\w,\s\\]+?))?'
    r'\s*\{'
)
_INTERFACE_PATTERN = re.compile(r'\binterface\s+([A-Za-z0-9_]+)')
_TRAIT_PATTERN = re.compile(r'\btrait\s+([A-Za-z0-9_]+)')
_USE_TRAIT_PATTERN = re.compile(r'^\s*use\s+([\w,\s\\]+?);', re.MULTILINE)
_METHOD_PATTERN = re.compile(r'\bfunction\s+([A-Za-z0-9_]+)')
_INSTANTIATE_PATTERN = re.compile(r'\bnew\s+([\w\\]+)\s*\(')
_STATIC_CALL_PATTERN = re.compile(r'\b([\w\\]+)::[\w]+\s*\(')


def _qualify(name: str, namespace: Optional[str], file_path: str, root_path: str) -> str:
    """Build a fully-qualified, collision-resistant node ID.

    Priority order:
      1. If the raw name already contains a backslash it is already qualified.
      2. If a namespace was declared, use Namespace\\ClassName.
      3. Fallback: relative_dir/ClassName using the file path relative to root.
    """
    name = name.strip()
    if '\\' in name:
        return name  # already fully qualified
    if namespace:
        return f"{namespace}\\{name}"
    # Fallback: use directory relative to root as namespace-like prefix
    rel = os.path.relpath(os.path.dirname(file_path), root_path)
    if rel == '.':
        return name
    return rel.replace(os.sep, '\\') + '\\' + name


class ParserBridge:
    """Parses PHP source files into typed Nodes and Edges.

    Phase A upgrade:
      - Namespace-aware fully-qualified IDs (collision-proof).
      - Typed edges: INHERITS, IMPLEMENTS, USES_TRAIT, INSTANTIATION, METHOD_CALL.
    """

    def parse_files(
        self,
        file_paths: List[str],
        root_path: str = '/data'
    ) -> Tuple[List[Node], List[Edge]]:
        nodes: List[Node] = []
        edges: List[Edge] = []

        for path in file_paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # ── Namespace ──────────────────────────────────────────────
                ns_match = _NS_PATTERN.search(content)
                namespace: Optional[str] = ns_match.group(1) if ns_match else None

                def fq(name: str) -> str:
                    return _qualify(name, namespace, path, root_path)

                methods_found = _METHOD_PATTERN.findall(content)

                # ── Classes ────────────────────────────────────────────────
                for m in _CLASS_PATTERN.finditer(content):
                    cls_name = m.group(1)
                    extends_name = m.group(2)
                    implements_raw = m.group(3)

                    node_id = fq(cls_name)
                    node = Node(
                        id=node_id,
                        name=cls_name,
                        namespace=namespace,
                        node_type=NodeType.CLASS,
                        file_path=path,
                        methods=methods_found
                    )
                    nodes.append(node)

                    # INHERITS edge
                    if extends_name:
                        edges.append(Edge(
                            source_id=node_id,
                            target_id=fq(extends_name),
                            edge_type=EdgeType.INHERITS
                        ))

                    # IMPLEMENTS edges
                    if implements_raw:
                        for iface in re.split(r'[\s,]+', implements_raw.strip()):
                            iface = iface.strip()
                            if iface:
                                edges.append(Edge(
                                    source_id=node_id,
                                    target_id=fq(iface),
                                    edge_type=EdgeType.IMPLEMENTS
                                ))

                    # INSTANTIATION edges — new ClassName()
                    for tgt in _INSTANTIATE_PATTERN.findall(content):
                        tgt_id = fq(tgt)
                        if tgt_id != node_id:
                            edges.append(Edge(
                                source_id=node_id,
                                target_id=tgt_id,
                                edge_type=EdgeType.INSTANTIATION
                            ))

                    # METHOD_CALL edges — ClassName::method()
                    for tgt in _STATIC_CALL_PATTERN.findall(content):
                        tgt_id = fq(tgt)
                        if tgt_id != node_id:
                            edges.append(Edge(
                                source_id=node_id,
                                target_id=tgt_id,
                                edge_type=EdgeType.METHOD_CALL
                            ))

                # ── Trait usage — USES_TRAIT edges ─────────────────────────
                # trait usage inside a class body emits USES_TRAIT edges
                # We attach them to the last class parsed in the file (simplification)
                if nodes:
                    last_node_id = nodes[-1].id
                    for use_line in _USE_TRAIT_PATTERN.findall(content):
                        for trait_name in re.split(r'[\s,]+', use_line.strip()):
                            trait_name = trait_name.strip()
                            if trait_name:
                                edges.append(Edge(
                                    source_id=last_node_id,
                                    target_id=fq(trait_name),
                                    edge_type=EdgeType.USES_TRAIT
                                ))

            except Exception:
                # Individual file errors do not abort the run
                pass

        return nodes, edges


class FileScanner:
    @staticmethod
    def scan(root_path: str, max_files: Optional[int] = None) -> List[str]:
        """Walk `root_path` and collect PHP files.

        Args:
            root_path: Directory to scan.
            max_files: Optional cap on number of files returned.
                       None means no limit (Phase A+).
        """
        php_files = []
        for root, _, files in os.walk(root_path):
            for file in sorted(files):   # sorted = deterministic ordering
                if file.endswith('.php'):
                    php_files.append(os.path.join(root, file))

        if max_files is not None:
            return php_files[:max_files]
        return php_files

