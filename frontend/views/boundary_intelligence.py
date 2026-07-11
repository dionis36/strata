import streamlit as st
import os
import requests
import pandas as pd
import streamlit.components.v1 as components
from pyvis.network import Network
from views import page_registry

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")

def fetch_boundary_intelligence(run_id: int):
    try:
        res = requests.get(f"{FASTAPI_URL}/boundary-intelligence/{run_id}", timeout=10)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 404:
            st.error(f"No boundary intelligence data found for run {run_id}.")
        else:
            st.error(f"API Error: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"Connection failed: {e}")
    return None

def show_boundary_intelligence():
    st.title("Boundary Intelligence")
    st.markdown("##### Map the external surface area of the legacy monolith: UI Entanglement, Network Endpoints, and Vendor Dependencies.")

    with st.expander("Boundary Intelligence Blueprint Key", expanded=True):
        colA, colB = st.columns(2)
        with colA:
            st.markdown("""
            **Presentation Layer Analysis**
            - **Global UI Entanglement**: Percentage of logic nodes coupled with HTML.
            - **Fat Views**: Files that query the database AND render HTML.
            """)
        with colB:
            st.markdown("""
            **API & Vendor Surface**
            - **Endpoints Detected**: Incoming network connection points.
            - **Vendor Inventory**: External third-party dependencies mapped.
            """)
    st.markdown("---")

    active_run_id = st.session_state.get("active_run_id")
    if not active_run_id:
        st.warning("No active analysis run detected. Please start a scan from the Executive Dashboard.")
        st.page_link(page_registry.PAGE_DASHBOARD, label="← Go to Executive Dashboard", icon=":material/dashboard:")
        return

    with st.spinner("Analyzing application boundaries..."):
        data = fetch_boundary_intelligence(active_run_id)

    if not data:
        return

    kpis = data.get("kpis", {})
    mvc = data.get("presentation_coupling", [])
    api = data.get("api_surface", [])
    vendor = data.get("vendor_intelligence", [])

    # ── Top-level KPI strip ───────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Global UI Entanglement",
        kpis.get("Global UI Entanglement", "0%"),
        help="Percentage of total AST nodes that are HTML output or echo statements. The higher this value, the more backend logic is coupled to the presentation layer the primary blocker for attaching a React or Vue frontend."
    )
    k2.metric(
        "Fat Views (DB-Coupled)",
        kpis.get("Fat Views (DB-Coupled UI)", 0),
        delta="Refactor Priority",
        delta_color="inverse",
        help="Files that both query the database AND render HTML in the same execution path. Each one is a 'Fat View' the anti-pattern that prevents a clean separation between backend API and frontend UI."
    )
    k3.metric(
        "Endpoints Detected",
        kpis.get("Total Endpoints Detected", 0),
        help="The number of distinct network entry points (routes, direct-access scripts, JSON-emitting files) detected. Represents the full public-facing surface area of the application."
    )
    k4.metric(
        "Vendor Files Scanned",
        kpis.get("Vendor Files Scanned", 0),
        help="Total count of third-party files found in the codebase, including both Composer-managed packages and manually embedded libraries."
    )

    st.markdown("---")

    tabs = st.tabs([
        f"Presentation Layer Coupling ({len(mvc)})",
        f"Endpoint & API Surface ({len(api)})",
        f"Vendor Inventory & Dependency Graph ({len(vendor.get('nodes', [])) if isinstance(vendor, dict) else len(vendor)})"
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 - Presentation Layer
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        st.markdown("#### MVC Deficit Report (UI Entanglement)")
        st.caption("Quantifies how deeply HTML is baked into backend business logic. High entanglement prevents easy migration to React/Vue.")
        
        if mvc:
            df = pd.DataFrame(mvc)
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            st.markdown("""
            <div style="background-color: rgba(28,131,225,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Presentation Layer Intelligence</h4>
                <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">UI Entanglement Ratio proportion of HTML output nodes relative to logic nodes per file.</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**METRIC**: UI Entanglement Ratio - proportion of HTML/echo output nodes relative to logic nodes per file")
            fat_views = kpis.get("Fat Views (DB-Coupled UI)", 0)
            mvc_files = len(mvc)
            st.markdown(
                f"**INTERPRETATION**: **{mvc_files} files** in this codebase produce direct HTML output inside their backend logic. "
                f"Of these, **{fat_views} are classified as 'Fat Views'** - files that simultaneously query the database and render the resulting HTML in the same execution path. "
                "This pattern reveals that the application was built without an MVC framework or templating layer, meaning the *same file* is responsible for fetching data, applying business rules, and deciding how to display the result. "
                "This is the primary structural reason why attaching a React or Vue frontend to this system is not a simple API swap."
            )
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. **{fat_views} 'Fat View' file(s)** detected - these files contain active database operations *and* a UI Entanglement Ratio above 15%, confirming presentation and persistence logic share the same execution context.\n"
                f"2. **{mvc_files - fat_views} file(s)** produce HTML output but without direct DB coupling - these are easier to convert to template files but still require a clear data contract before a frontend framework can consume them."
            )
            st.markdown(
                "**RECOMMENDATION**: The Entanglement Ratio column tells you *how deeply* HTML is mixed into each file. "
                "Study the distribution - are the fat views concentrated in one directory (suggesting a feature module), or scattered across the codebase? "
                "That pattern is the difference between a targeted refactor and a wholesale rewrite of the presentation tier."
            )
            if st.button("Analyze Structural Risk of these Views"):
                st.switch_page(page_registry.PAGE_RISK_AUDIT)
        else:
            st.success("No presentation coupling detected. HTML output is not mixed with backend logic in this scan.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 - API Surface
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        st.markdown("#### Endpoint & API Surface Intelligence")
        st.caption("Automatically infers the 'front door' of the application by detecting routing patterns, JSON signatures, and direct script access.")
        
        if api:
            df = pd.DataFrame(api)
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            st.markdown("""
            <div style="background-color: rgba(33,195,84,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Application Entry Point Intelligence</h4>
                <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Entry Point Classification how external requests reach and enter the application.</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**METRIC**: Entry Point Classification - how external requests reach the application")
            pure_scripts = sum(1 for a in api if a.get("Pure Script") == "Yes")
            api_endpoints = sum(1 for a in api if a.get("Type") == "API Endpoint")
            routers = sum(1 for a in api if a.get("Type") == "Procedural Router")
            total_ep = len(api)
            st.markdown(
                f"**INTERPRETATION**: This codebase exposes **{total_ep} detectable entry points**, classified by how they receive and respond to incoming requests. "
                f"**{pure_scripts} are Pure Scripts** - PHP files with no class or function structure that are accessed directly via URL, meaning each is its own isolated request handler. "
                f"**{api_endpoints} emit structured API responses** (JSON), indicating that parts of the system are already operating as a de-facto API layer, even if undocumented. "
                f"**{routers} handle procedural routing** via `$_SERVER['REQUEST_URI']`, acting as a manual front controller without a formal framework."
            )
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. **{pure_scripts} Pure Scripts** detected - each represents an independent, undocumented entry point that any client (or attacker) can call directly if accessible from the web root.\n"
                f"2. **{api_endpoints} JSON-emitting endpoint(s)** detected - these files are already functioning as an API and are the clearest candidates for formalization into a documented REST layer.\n"
                f"3. **{routers} Procedural Router(s)** detected - these files inspect the request URI and dispatch control manually, suggesting the presence of a routing convention that predates MVC frameworks."
            )
            st.markdown(
                "**RECOMMENDATION**: The entry point table is your first map of the application's public contract. "
                "Before forming any migration strategy, consider: which of these entry points are actively used by real users or clients, and which are dead code? "
                "That distinction changes the scope of work significantly - a system with 50 entry points but 10 active ones has a much smaller viable extraction surface than the raw count suggests."
            )
            if st.button("Audit Architectural Rot"):
                st.switch_page(page_registry.PAGE_RISK_AUDIT)
        else:
            st.warning("No entry points detected. This may indicate the scan covered only a library or internal module, rather than a web-facing application.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 - Vendor Intelligence
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.markdown("#### Vendor Inventory & Dependency Graph")
        st.caption("Detects 'Shadow IT' and third-party libraries. The graph shows entry points from your application into these external dependencies.")
        
        vendor_graph = data.get("vendor_graph", {"nodes": [], "edges": []})
        if vendor_graph["nodes"]:
            st.markdown("##### Shadow IT Dependency Map")
            
            # Use PyVis for graph rendering
            net = Network(height="400px", width="100%", bgcolor="#0e1117", font_color="#e0e0e0")
            for n in vendor_graph["nodes"]:
                net.add_node(n["id"], label=n["label"], color=n["color"], size=n.get("size", 10))
            for e in vendor_graph["edges"]:
                net.add_edge(e["source"], e["target"], color="rgba(150, 150, 150, 0.4)")
                
            net.save_graph(f"/tmp/vendor_graph_{active_run_id}.html")
            with open(f"/tmp/vendor_graph_{active_run_id}.html", "r", encoding="utf-8") as f:
                html = f.read()
            html = html.replace("</head>", "<style>#loadingBar { display: none !important; }</style></head>")
            
            components.html(html, height=450)
            st.markdown("---")

        st.markdown("##### Vendor Registry")
        if vendor:
            df = pd.DataFrame(vendor)
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            st.markdown("""
            <div style="background-color: rgba(255,193,7,0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; font-size: 1.1rem; color: inherit;">Vendor Dependency Intelligence</h4>
                <div class="strata-tooltip-container"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg><span class="strata-tooltip-text">Vendor Classification Composer-managed vs. manually embedded third-party libraries.</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**METRIC**: Vendor Classification - Composer-managed vs. manually embedded third-party libraries")
            orphans = sum(1 for v in vendor if "ORPHANED RISK" in v.get("Status", ""))
            total_vendor = len(vendor)
            composer_managed = sum(1 for v in vendor if v.get("Vendor Type") == "Composer Vendor")
            manual_libs = total_vendor - composer_managed
            st.markdown(
                f"**INTERPRETATION**: **{total_vendor} vendor files** were detected in this codebase. "
                f"**{composer_managed} are managed via Composer**, meaning they can be updated, pinned, and replaced through standard tooling. "
                f"**{manual_libs} are manually embedded** (found in `/lib`, `/plugin`, or `/thirdparty` paths, or identified by known legacy namespaces), meaning they exist outside version control accountability - no audit trail, no automated vulnerability alerts, no standard upgrade path. "
                f"{'Of these, **' + str(orphans) + ' contain active security sinks** (e.g., `mysql_*`) within their own code, meaning the vulnerability cannot be patched by your team - the library must be replaced entirely.' if orphans > 0 else 'None of the detected vendor libraries contain known active security sinks.'}"
            )
            st.markdown(
                f"**EVIDENCE**:\n"
                f"1. **{manual_libs} manually embedded library/plugin file(s)** detected - these exist outside Composer's dependency graph, making it impossible to track their version, provenance, or known CVEs through standard tooling.\n"
                f"2. **{orphans} vendor file(s) flagged as 'Orphaned Risk'** - these contain security sinks within third-party code your team does not own, meaning the vulnerability is structurally embedded and cannot be resolved without replacement.\n"
                f"3. **{composer_managed} Composer-managed file(s)** are present - if the codebase uses a `composer.json`, check whether the manually embedded libraries duplicate any already managed dependency."
            )
            st.markdown(
                "**RECOMMENDATION**: The Vendor Type and Status columns reveal the two-tier dependency problem in this system. "
                "Study the ratio of `Composer Vendor` to `Manual Library/Plugin` - a high proportion of manual libraries tells you that the dependency management strategy was informal, which typically means the codebase has accumulated technical debt from library versions that were never updated. "
                "Understanding which features depend on these libraries is the first step to assessing their replacement cost."
            )
        else:
            st.success("No unmanaged vendor dependencies detected.")
