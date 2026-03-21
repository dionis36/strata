"""
Phase 4.5: Risk Reasoner
Evaluates the rule set against a component's merged metric data.
Produces a deterministic, ordered list of ExplanationItems.
"""
from typing import List

from domain.explanation.rules import RULES
from domain.explanation.explanation_model import ExplanationItem

MAX_EXPLANATIONS = 5


class RiskReasoner:
    """Evaluates all rules against a component data dict and returns ranked explanations.

    Design guarantees:
      - Deterministic: same input always produces the same output.
      - Bounded: at most MAX_EXPLANATIONS items are returned.
      - Ordered: explanations are sorted by weight DESC (highest importance first).
      - Isolated: no DB access, no I/O — pure in-memory evaluation.
    """

    def __init__(self, rules: list = None):
        """Allow rule injection for testing; defaults to the canonical RULES list."""
        self._rules = rules if rules is not None else RULES

    def explain(self, component_data: dict) -> List[ExplanationItem]:
        """Evaluate all rules and return the top N explanations for a component.

        Args:
            component_data: Dict containing merged Phase 3/4 metrics for one component.
                            Required keys include: criticality_index, instability,
                            coupling_pressure, cycle_flag, scc_size, blast_radius,
                            write_intensity, table_dependencies, behavioral_factor, final_risk.

        Returns:
            List of ExplanationItem, sorted by weight DESC, capped at MAX_EXPLANATIONS.
        """
        triggered = []

        for rule in self._rules:
            try:
                if rule["condition"](component_data):
                    message = self._render_message(
                        rule["message_template"], component_data
                    )
                    triggered.append(
                        ExplanationItem(
                            type=rule["name"],
                            category=rule["category"],
                            severity=rule["severity"],
                            weight=rule["weight"],
                            message=message,
                        )
                    )
            except Exception:
                # Silently skip a malformed rule — never crash the pipeline
                continue

        # Sort by weight descending, then cap
        triggered.sort(key=lambda e: e.weight, reverse=True)
        return triggered[:MAX_EXPLANATIONS]

    @staticmethod
    def _render_message(template: str, data: dict) -> str:
        """Render a message template with values from the component data.

        Uses safe .format_map() so missing keys produce a readable fallback
        rather than raising KeyError.
        """
        try:
            return template.format_map(_SafeFormatMap(data))
        except Exception:
            return template  # Return the raw template if rendering fails


class _SafeFormatMap(dict):
    """A dict subclass that returns 'N/A' for missing keys during format_map."""
    def __missing__(self, key):
        return "N/A"
