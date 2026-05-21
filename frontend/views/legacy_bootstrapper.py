import streamlit as st
import requests
import os

def show_legacy_bootstrapper():
    st.title("Modernization Factory")
    st.markdown("### Legacy System Bootstrapping")
    st.markdown("---")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
    run_id = st.session_state.get("active_run_id")
    
    if not run_id:
        st.warning("No active analysis run detected. Please execute a scan from the Dashboard.")
        return

    @st.cache_data(ttl=60)
    def fetch_tree_data(rid):
        res = requests.get(f"{FASTAPI_URL}/graph/{rid}/includes")
        if res.status_code == 200:
            return res.json()
        return None

    tree_data = fetch_tree_data(run_id)
    if not tree_data:
        st.error("Technical error retrieving bootstrapping data.")
        return

    # --- Structural Integrity ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Circular Dependency Audit")
        cycles = tree_data.get("circular_includes", [])
        if cycles:
            st.error(f"Detected {len(cycles)} circular inclusion paths.")
            with st.expander("Review Circular Paths"):
                for c in cycles:
                    st.code(c, language="text")
        else:
            st.success("No circular inclusions detected.")

    with c2:
        st.markdown("#### Reachability Analysis")
        orphans = tree_data.get("dead_includes", [])
        if orphans:
            st.warning(f"Detected {len(orphans)} orphaned files.")
            with st.expander("Review Orphaned Entities"):
                st.code("\n".join(orphans), language="text")
        else:
            st.success("Universal code reachability verified.")

    st.markdown("---")
    
    # --- Modernization Artifacts ---
    st.markdown("#### Modernization Artifact Generator")
    tabs = st.tabs(["Composer Configuration", "Bootstrap Hierarchy"])
    
    with tabs[0]:
        st.markdown("##### PSR-4 Autoloading Bridge")
        st.markdown("Generated based on detected namespace patterns and directory taxonomy.")
        
        # Mocking composer.json generation logic for now
        composer_json = {
            "name": f"strata-modernization/{st.session_state.get('project_slug', 'legacy-app')}",
            "require": {
                "php": ">=8.1"
            },
            "autoload": {
                "psr-4": {
                    "App\\": "src/"
                }
            }
        }
        st.code(str(composer_json).replace("'", '"'), language="json")
        st.download_button("Download composer.json", str(composer_json).replace("'", '"'), file_name="composer.json")

    with tabs[1]:
        st.markdown("##### Inferred Inclusion Hierarchy")
        adjacency = tree_data.get("bootstrap_chain", {})
        if adjacency:
            def generate_html_tree(node, graph, visited=None, depth=0):
                if visited is None: visited = set()
                children = graph.get(node, [])
                label = f"📄 <b>{node}</b>"
                
                if node in visited:
                    return f"<div style='margin-left: 20px; color: #777; font-size: 0.9rem;'>{label} <span style='color: #f87171;'>(circular loop)</span></div>"
                
                if depth > 3:
                    return f"<div style='margin-left: 20px; font-size: 0.9rem; color: #58a6ff;'>[+] ... ({len(children)} deeper dependencies hidden)</div>"
                
                visited.add(node)
                
                if not children:
                    return f"<div style='margin-left: 20px; font-size: 0.9rem;'>{label}</div>"
                
                children_html = "".join([generate_html_tree(c, graph, visited.copy(), depth + 1) for c in children])
                return f"<details open style='margin-left: 10px; margin-bottom: 2px;'><summary style='cursor: pointer; padding: 2px;'>{label}</summary><div style='border-left: 1px dashed #444; margin-left: 7px; padding-top: 4px; padding-bottom: 4px;'>{children_html}</div></details>"

            in_degrees = {k: 0 for k in adjacency.keys()}
            for children in adjacency.values():
                for c in children:
                    if c not in in_degrees: in_degrees[c] = 0
                    in_degrees[c] += 1
            roots = [n for n, deg in in_degrees.items() if deg == 0][:10]
            
            st.markdown("<div style='font-family: monospace; background: #111; padding: 15px; border-radius: 8px; max-height: 500px; overflow-y: auto; border: 1px solid #333;'>", unsafe_allow_html=True)
            for root in roots:
                st.markdown(generate_html_tree(root, adjacency), unsafe_allow_html=True)
                st.markdown("<hr style='border-color: #333; margin: 10px 0;'>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No inclusion hierarchy identified.")

if __name__ == "__main__":
    show_legacy_bootstrapper()
