"""
Severity Constants — Single source of truth for the 4-tier risk/complexity scale.
Ensures consistency across all UI components and views.
"""

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

SEVERITY_COLORS = {
    SEVERITY_CRITICAL: "#ff4b4b",  # Red
    SEVERITY_HIGH: "#ffa726",      # Orange
    SEVERITY_MEDIUM: "#fdd835",    # Yellow
    SEVERITY_LOW: "#00cc96"        # Green
}
