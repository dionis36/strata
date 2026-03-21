"""
Phase 4.5: Evidence Builder
Extracts concrete, traceable evidence for each explanation.

Evidence sources:
  1. Metrics  — flat values from the component_data dict (already computed)
  2. Graph    — dependent components and SCC membership, read from graph_<run_id>.json
  3. Code     — source file path, sourced from graph node attributes

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
        """Load the graph JSON artifact from disk for a given run.

        Returns None if the file doesn't exist (analysis may not have serialised it).
        """
        path = os.path.join(GRAPH_DIR, f"graph_{run_id}.json")
        if not os.path.exists(path):
            logger.warning(f"[EvidenceBuilder] Graph file not found: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[EvidenceBuilder] Failed to load graph: {e}")
            return None

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
        """Extract dependent components and SCC membership from graph JSON."""
        if not graph:
            return {"dependent_components": [], "scc_members": []}

        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        links = graph.get("links", [])

        # Components that have an edge pointing TO this component (in-bound dependents)
        dependents = [
            link["source"]
            for link in links
            if link.get("target") == component_name
            and link.get("source") != component_name
        ]

        # Components sharing the same scc_id (cycle members), excluding self
        target_node = nodes.get(component_name, {})
        scc_id = target_node.get("scc_id")
        scc_members = []
        if scc_id and scc_id != 0:
            scc_members = [
                nid for nid, ndata in nodes.items()
                if ndata.get("scc_id") == scc_id and nid != component_name
            ]

        return {
            "dependent_components": dependents[:10],  # Cap to avoid payload bloat
            "scc_members": scc_members,
        }

    @staticmethod
    def _extract_code_context(component_name: str, graph: Optional[dict]) -> dict:
        """Extract the source file path for a component from graph node attributes."""
        if not graph:
            return {"file_path": None}

        for node in graph.get("nodes", []):
            if node.get("id") == component_name:
                raw_path = node.get("file_path") or node.get("filepath")
                if raw_path:
                    # Normalise to forward-slash relative path for readability
                    rel = raw_path.replace("\\", "/")
                    return {"file_path": rel}
                break

        return {"file_path": None}
