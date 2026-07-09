"""
Phase 4.5: Evidence Builder
Extracts concrete, traceable evidence for each explanation.

Evidence sources:
  1. Metrics  - flat values from the component_data dict (already computed)
  2. Graph    - dependent components and SCC membership, read from graph_<run_id>.json
  3. Code     - source file path, sourced from graph node attributes

Design: stateless, no DB access. Reads from the pre-serialised graph JSON on disk.
"""
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GRAPH_DIR = "/data"


class EvidenceBuilder:
    """Builds the evidence payload for a component's explanation.

    Call build() once per component per request. The graph JSON is loaded
    once and passed in by the ExplanationService to avoid redundant I/O.
    """

    # Metric fields to surface in evidence (keeps payload focused)
    EVIDENCE_METRICS = [
        "criticality_index",
        "instability",
        "coupling_pressure",
        "cycle_flag",
        "scc_size",
        "blast_radius",
        "write_intensity",
        "table_dependencies",
        "behavioral_factor",
        "final_risk",
    ]

    @staticmethod
    def load_graph(run_id: int) -> Optional[dict]:
        """Load and pre-index the graph JSON artifact from disk.

        Returns a pre-processed dict with:
          - 'nodes':   {node_id: node_data}
          - 'inbound': {node_id: [source_ids]}  - who points AT this node
        Returns None if the file doesn't exist.
        """
        path = os.path.join(GRAPH_DIR, f"graph_{run_id}.json")
        if not os.path.exists(path):
            logger.warning(f"[EvidenceBuilder] Graph file not found: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            logger.error(f"[EvidenceBuilder] Failed to load graph: {e}")
            return None

        # Pre-index nodes by ID - O(n) once, then O(1) per lookup
        nodes_index = {n["id"]: n for n in raw.get("nodes", [])}

        # Pre-build inbound adjacency map - O(e) once, then O(1) per lookup
        inbound_map: dict = {}
        for link in raw.get("links", []):
            target = link.get("target")
            source = link.get("source")
            if target and source and source != target:
                inbound_map.setdefault(target, []).append(source)

        return {"nodes": nodes_index, "inbound": inbound_map}

    @classmethod
    def build(
        cls,
        component_name: str,
        component_data: dict,
        graph: Optional[dict],
    ) -> dict:
        """Assemble the full evidence payload for a single component.

        Args:
            component_name: Fully-qualified component ID (e.g. 'system\\core\\CI_Loader').
            component_data: Merged metrics dict from ExplanationService.
            graph: Loaded graph JSON dict (node-link format), or None.

        Returns:
            Evidence dict with keys: 'metrics', 'graph', 'code'.
        """
        return {
            "metrics": cls._extract_metrics(component_data),
            "graph":   cls._extract_graph_context(component_name, graph),
            "code":    cls._extract_code_context(component_name, graph),
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    @classmethod
    def _extract_metrics(cls, component_data: dict) -> dict:
        """Return the focused subset of metric values for the evidence panel."""
        return {
            k: round(v, 4) if isinstance(v, float) else v
            for k, v in component_data.items()
            if k in cls.EVIDENCE_METRICS
        }

    @staticmethod
    def _extract_graph_context(component_name: str, graph: Optional[dict]) -> dict:
        """O(1) lookup using pre-indexed nodes and inbound adjacency map."""
        if not graph:
            return {"dependent_components": [], "scc_members": []}

        nodes   = graph.get("nodes", {})    # dict: id -> node_data or list
        inbound = graph.get("inbound", {})  # dict: id -> [source_ids]

        if isinstance(nodes, list):
            # Raw list format, index on the fly
            nodes_list = nodes
            nodes = {n["id"]: n for n in nodes_list}
            inbound = {}
            for link in graph.get("links", []):
                target = link.get("target") or link.get("callee")
                source = link.get("source") or link.get("caller")
                if target and source and source != target:
                    inbound.setdefault(target, []).append(source)

        # Direct inbound dependents (capped to avoid payload bloat)
        dependents = inbound.get(component_name, [])[:10]

        # SCC members - same scc_id, same scc_size > 1
        target_node = nodes.get(component_name, {})
        scc_id   = target_node.get("scc_id")
        scc_size = target_node.get("scc_size", 1)
        scc_members = []
        if scc_id and scc_size > 1:
            scc_members = [
                nid for nid, ndata in nodes.items()
                if ndata.get("scc_id") == scc_id and nid != component_name
            ]

        return {
            "dependent_components": dependents,
            "scc_members":          scc_members,
        }

    @staticmethod
    def _extract_code_context(component_name: str, graph: Optional[dict]) -> dict:
        """O(1) file path lookup from pre-indexed node dict."""
        if not graph:
            return {"file_path": None}

        nodes = graph.get("nodes", {})
        if isinstance(nodes, list):
            nodes = {n["id"]: n for n in nodes}

        node = nodes.get(component_name)
        if node:
            raw_path = node.get("file_path") or node.get("filepath")
            if raw_path:
                return {"file_path": raw_path.replace("\\", "/")}

        return {"file_path": None}
