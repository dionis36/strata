"""
Page Registry - Shared st.Page object store.

This module is populated by app.py at startup with the exact st.Page objects
registered in st.navigation(). View files import from here to get those
registered objects for cross-page navigation via st.switch_page() or
st.page_link(), ensuring they reference the same object the router knows about.

Do NOT import from view files in this module (would cause circular imports).
app.py sets these attributes; view files read them.
"""

PAGE_RISK_AUDIT = None
PAGE_BOUNDARY_INTELLIGENCE = None
PAGE_DASHBOARD = None
PAGE_REPORT_VIEWER = None
PAGE_RUN_COMPARISON = None
